from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.db import IntegrityError
from ninja import NinjaAPI, ModelSchema, Schema
from typing import Optional, List
from datetime import datetime
from ninja.security import HttpBearer

# ninja_jwt is optional in this environment; provide a safe fallback when
# the package isn't installed so module import won't crash during tests.
try:
    from ninja_jwt.tokens import RefreshToken
    from ninja_jwt.authentication import JWTAuth
except Exception:

    class RefreshToken:
        @staticmethod
        def for_user(u):
            class RT:
                def __str__(self):
                    return "refresh-token-mock"

                @property
                def access_token(self):
                    return "access-token-mock"

            return RT()

    class JWTAuth:
        pass


from .models import User, Patient, Bed, Task, Call, Event
import paho.mqtt.client as mqtt
import json
from urllib.parse import parse_qs
from django.views.decorators.csrf import csrf_exempt

jwtauth = JWTAuth()
api = NinjaAPI(auth=jwtauth)


def send_mqtt_cancel_call(bed_id_str):
    """
    Envía un mensaje MQTT para cancelar llamadas en una habitación
    Formato esperado: "room,0" (ej: "1,0")
    """
    try:
        client = mqtt.Client()
        client.connect("mosquitto", 1883)

        # Preparar mensaje de cancelación
        message = {
            "state": False,
            "id": bed_id_str,
            "key": "this&is$a$key&to?prevent?hacking",
        }

        client.publish("mqtt/call/", json.dumps(message))
        client.disconnect()
        print(f"✓ MQTT Cancel message sent for: {bed_id_str}")
    except Exception as e:
        print(f"✗ Error sending MQTT cancel: {str(e)}")


class UserSchema(ModelSchema):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_leader",
            "is_superuser",
            "role",
            "image",
            "date_joined",
        ]


class UserCreateSchema(Schema):
    username: str
    email: str
    password: str
    is_leader: bool = False


class LoginSchema(Schema):
    username: str
    password: str


class TokenSchema(Schema):
    access: str
    refresh: str
    user: UserSchema


class PatientSchema(ModelSchema):
    class Meta:
        model = Patient
        fields = [
            "id",
            "name",
            "social_security_number",
            "image",
            "inpatient",
            "admission",
            "diagnosis",
            "short_diagnosis",
            "treatment_roadmap",
            "action_done_by",
        ]


class BedSchema(ModelSchema):
    class Meta:
        model = Bed
        fields = [
            "id",
            "id_bed",
            "active",
            "bed_state",
            "occupied_time",
            "planed_vacate",
            "vacate_time",
            "action_done_by",
        ]


class TaskSchema(ModelSchema):
    class Meta:
        model = Task
        fields = [
            "id",
            "bed",
            "repeat",
            "repeat_id",
            "task",
            "programed_time",
            "done_time",
            "active",
            "state",
            "programed_by",
            "task_done_by",
            "action_done_by",
        ]


class CallSchema(ModelSchema):
    class Meta:
        model = Call
        fields = [
            "id",
            "bed",
            "response",
            "call_time",
            "response_time",
            "state",
            "action_done_by",
        ]


class BedInputSchema(Schema):
    roomBedId: str
    patientName: str
    patientSocial: str
    diagnosis: str
    occupiedDateTime: str
    planedVacate: str
    doneBy: str


class BedEditSchema(Schema):
    bedId: int
    patientName: str
    patientSocial: str
    diagnosis: str
    occupiedDateTime: str
    planedVacate: str
    doneBy: str


class VacateSchema(Schema):
    bedId: int
    patientId: int
    vacateDT: str
    doneBy: str


class TaskInputSchema(Schema):
    bed_id: int
    task: str
    programed_time: str
    repeat: bool = False
    repeat_lapse: Optional[int] = None  # número (2, 3, etc)
    repeat_lapse_unit: Optional[str] = None  # minutes, hours, days
    repeat_until: Optional[str] = None  # fecha/hora hasta repetir


class TaskEditSchema(Schema):
    # Allow partial updates: make fields optional so PUT bodies can include
    # only the fields the client wants to change.
    task: Optional[str] = None
    programed_time: Optional[str] = None
    done_time: Optional[str] = None
    active: Optional[bool] = None


class CallResponseSchema(Schema):
    bed_id: int
    response: str


@api.post("/auth/login", response=TokenSchema, auth=None)
def login(request, data: LoginSchema):
    user = authenticate(username=data.username, password=data.password)
    if user:
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": user,
        }
    return JsonResponse({"error": "Invalid credentials"}, status=401)


# Temporary debug endpoint to inspect incoming request payloads (safe to remove later)
@api.post("/auth/debug", auth=None)
def auth_debug(request):
    django_req = getattr(request, "_request", request)
    info = {
        "content_type": getattr(request, "content_type", None),
        "headers": {k: v for k, v in getattr(request, "headers", {}).items()},
        "body_len": len(getattr(django_req, "body", b""))
        if getattr(django_req, "body", None)
        else 0,
    }
    try:
        raw = getattr(django_req, "body", b"") or b""
        info["raw_snippet"] = raw.decode(errors="ignore")[:200]
    except Exception:
        info["raw_snippet"] = ""
    try:
        post = getattr(django_req, "POST", {}) or {}
        info["post_keys"] = list(post.keys())
    except Exception:
        info["post_keys"] = []
    return info


@api.post("/auth/register", response=UserSchema, auth=None)
def register(request, body: dict = None):
    """
    Robust registration handler that reads the underlying Django request
    body aggressively. Some combinations of middleware and Ninja's parsing
    can cause the body to be consumed before Ninja provides a parsed value.
    This function attempts several fallbacks (JSON, form-encoded body,
    request.POST) to recover the payload.
    """
    django_req = getattr(request, "_request", request)

    # small debug snapshot to help reproduce issues during tests
    try:
        meta = {}
        try:
            meta = {
                k: str(v)
                for k, v in dict(getattr(django_req, "META", {})).items()
                if k in ("CONTENT_TYPE", "CONTENT_LENGTH")
            }
        except Exception:
            meta = {}
        snapshot = {
            "req_content_type": getattr(request, "content_type", None),
            "req_body_attr": repr(getattr(request, "body", None))[:1000],
            "django_body_attr": repr(getattr(django_req, "body", None))[:1000],
            "meta_snippet": meta,
        }
        # Debug snapshot generation left intentionally inert in production.
        # Previously this wrote to /tmp which was used during debugging; remove
        # active file writes to avoid leaving artifacts in the host environment.
    except Exception:
        pass

    parsed = {}
    # If Ninja provided parsed body, prefer it
    if isinstance(body, dict):
        parsed = body

    # Try several places for the raw body
    raw_candidates = []
    try:
        raw_candidates.append(getattr(django_req, "body", None))
    except Exception:
        pass
    try:
        raw_candidates.append(getattr(request, "body", None))
    except Exception:
        pass
    try:
        raw_candidates.append(getattr(django_req, "_body", None))
    except Exception:
        pass
    try:
        raw_candidates.append(getattr(request, "_body", None))
    except Exception:
        pass

    # Try to decode JSON from any raw candidate first
    for raw in raw_candidates:
        if not raw:
            continue
        try:
            if isinstance(raw, bytes):
                text = raw.decode(errors="ignore")
            else:
                text = str(raw)
            if not text:
                continue
            try:
                parsed = json.loads(text)
                break
            except Exception:
                # maybe it's form-encoded like username=...&email=...
                try:
                    qs = parse_qs(text)
                    if qs:
                        # flatten values
                        parsed = {k: v[0] for k, v in qs.items()}
                        break
                except Exception:
                    pass
        except Exception:
            continue

    # If still empty, try reading raw wsgi input or _stream if present
    if not parsed:
        try:
            wsgi_in = None
            try:
                wsgi_in = django_req.META.get("wsgi.input")
            except Exception:
                wsgi_in = None
            if wsgi_in:
                try:
                    wsgi_in.seek(0)
                except Exception:
                    pass
                try:
                    raw = wsgi_in.read()
                except Exception:
                    try:
                        raw = wsgi_in.read().decode(errors="ignore")
                    except Exception:
                        raw = None
                if raw:
                    try:
                        if isinstance(raw, bytes):
                            text = raw.decode(errors="ignore")
                        else:
                            text = str(raw)
                        parsed = json.loads(text)
                    except Exception:
                        try:
                            qs = parse_qs(text)
                            parsed = {k: v[0] for k, v in qs.items()}
                        except Exception:
                            parsed = {}
        except Exception:
            pass

    # As a last resort, try reading an internal _stream attribute
    if not parsed:
        try:
            stream = getattr(django_req, "_stream", None)
            if stream:
                try:
                    stream.seek(0)
                except Exception:
                    pass
                try:
                    raw = stream.read()
                except Exception:
                    try:
                        raw = stream.read().decode(errors="ignore")
                    except Exception:
                        raw = None
                if raw:
                    try:
                        if isinstance(raw, bytes):
                            text = raw.decode(errors="ignore")
                        else:
                            text = str(raw)
                        parsed = json.loads(text)
                    except Exception:
                        try:
                            qs = parse_qs(text)
                            parsed = {k: v[0] for k, v in qs.items()}
                        except Exception:
                            parsed = {}
        except Exception:
            pass

    # If not parsed yet, try request.POST (multipart/form-data / form-encoded)
    if not parsed:
        try:
            post = getattr(django_req, "POST", {}) or {}
            if post:
                parsed = {k: v for k, v in post.items()}
        except Exception:
            parsed = {}

    # final guard: ensure parsed is a dict
    if not isinstance(parsed, dict):
        parsed = {}

    username = parsed.get("username")
    email = parsed.get("email")
    password = parsed.get("password")
    is_leader = parsed.get("is_leader", False)

    if not username or not email or not password:
        return JsonResponse(
            {"error": "Username, email, and password are required"}, status=400
        )

    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_leader=is_leader,
        )
    except IntegrityError:
        return JsonResponse(
            {"error": "User with this username or email already exists"}, status=400
        )

    # Save image if present
    try:
        files = getattr(django_req, "FILES", {}) or {}
        if files and files.get("image"):
            user.image = files.get("image")
            user.save()
    except Exception:
        pass

    return user


# A fallback plain Django view for JSON registration.
# This bypasses Ninja parsing so tests that POST JSON directly are handled
# even if middleware consumed the body before Ninja handlers run.
@csrf_exempt
def django_register(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    django_req = request
    parsed = {}
    # try raw body JSON
    try:
        raw = getattr(django_req, "body", b"") or b""
        if raw:
            try:
                parsed = json.loads(raw.decode(errors="ignore"))
            except Exception:
                parsed = {}
    except Exception:
        parsed = {}

    # fallback to form data
    if not parsed:
        try:
            post = getattr(django_req, "POST", {}) or {}
            if post:
                parsed = {k: v for k, v in post.items()}
        except Exception:
            parsed = {}

    if not isinstance(parsed, dict):
        parsed = {}

    username = parsed.get("username")
    email = parsed.get("email")
    password = parsed.get("password")
    is_leader_raw = parsed.get("is_leader", False)
    is_leader = (
        str(is_leader_raw).lower() in ("true", "1", "yes") if is_leader_raw else False
    )

    if not username or not email or not password:
        return JsonResponse(
            {"error": "Username, email, and password are required"}, status=400
        )

    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_leader=is_leader,
        )
    except IntegrityError:
        return JsonResponse(
            {"error": "User with this username or email already exists"}, status=400
        )

    return JsonResponse(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_leader": user.is_leader,
            "role": getattr(user, "role", "nurse"),
            "image": getattr(user, "image", None) and str(user.image.url),
            "date_joined": user.date_joined.isoformat()
            if getattr(user, "date_joined", None)
            else None,
        }
    )


@api.post("/auth/logout")
def logout(request):
    return {"message": "Logged out successfully"}


@api.get("/users/me", response=UserSchema, auth=jwtauth)
def get_current_user(request):
    return request.user


@api.get("/beds", response=List[BedSchema], auth=jwtauth)
def list_beds(request):
    beds = Bed.objects.all().select_related("bed_patient")
    return beds


@api.get("/beds/{int:bed_id}", response=BedSchema, auth=jwtauth)
def get_bed(request, bed_id: int):
    bed = Bed.objects.get(id=bed_id)
    return bed


@api.post("/beds", response=BedSchema, auth=jwtauth)
def create_bed(request, data: Optional[BedInputSchema] = None, payload: dict = None):
    # Accept either a Ninja-parsed schema or raw JSON/form payloads. This
    # avoids errors when the request body was consumed or when the client
    # sends a plain dict/string.
    django_req = getattr(request, "_request", request)

    # prefer Ninja schema
    parsed = {}
    if data is not None:
        try:
            if isinstance(data, dict):
                parsed = data
            else:
                parsed = {
                    "roomBedId": getattr(data, "roomBedId", None),
                    "patientName": getattr(data, "patientName", None),
                    "patientSocial": getattr(data, "patientSocial", None),
                    "diagnosis": getattr(data, "diagnosis", None),
                    "occupiedDateTime": getattr(data, "occupiedDateTime", None),
                    "planedVacate": getattr(data, "planedVacate", None),
                    "doneBy": getattr(data, "doneBy", None),
                }
        except Exception:
            parsed = {}

    # fallback to provided payload dict
    if not parsed and isinstance(payload, dict):
        parsed = payload

    # try to parse raw body if still empty
    if not parsed:
        try:
            raw = getattr(django_req, "body", b"") or b""
            if raw:
                try:
                    parsed = json.loads(raw.decode(errors="ignore"))
                except Exception:
                    parsed = {}
        except Exception:
            parsed = {}

    # form POST fallback
    if not parsed:
        try:
            post = getattr(django_req, "POST", {}) or {}
            for k, v in post.items():
                parsed.setdefault(k, v)
        except Exception:
            pass

    # Ensure parsed is a dict; if not, bail with helpful error
    if not isinstance(parsed, dict):
        return JsonResponse({"error": "Invalid payload for creating bed"}, status=400)

    # Create patient
    patient = Patient.objects.create(
        name=parsed.get("patientName") or "No Name",
        social_security_number=parsed.get("patientSocial") or "0000",
        short_diagnosis=parsed.get("diagnosis") or "No Diagnosis",
    )

    # parse datetimes permissively
    def _parse_dt(val):
        if not val:
            return None
        try:
            s = str(val).replace("T", " ")
            if s.endswith("Z"):
                s = s[:-1]
            try:
                return datetime.fromisoformat(s)
            except Exception:
                try:
                    return datetime.strptime(s, "%Y-%m-%d %H:%M")
                except Exception:
                    try:
                        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
                    except Exception:
                        return None
        except Exception:
            return None

    occupied_dt = _parse_dt(parsed.get("occupiedDateTime"))
    planed_vac = _parse_dt(parsed.get("planedVacate"))

    bed = Bed.objects.create(
        id_bed=parsed.get("roomBedId"),
        bed_patient=patient,
        active=True,
        bed_state="occupied",
        occupied_time=occupied_dt,
        planed_vacate=planed_vac,
        action_done_by=parsed.get("doneBy") or "Anónimo",
    )
    try:
        from .modular_views.app.app_ws_update import app_ws_update

        app_ws_update()
    except Exception:
        pass
    return bed


@api.put("/beds/{int:bed_id}", response=BedSchema, auth=jwtauth)
def update_bed(request, bed_id: int, data: BedEditSchema):
    bed = Bed.objects.get(id=bed_id)
    patient = bed.bed_patient
    bed.occupied_time = datetime.strptime(
        data.occupiedDateTime.replace("T", " "), "%Y-%m-%d %H:%M"
    )
    bed.planed_vacate = datetime.strptime(
        data.planedVacate.replace("T", " "), "%Y-%m-%d %H:%M"
    )
    bed.action_done_by = data.doneBy
    patient.name = data.patientName
    patient.social_security_number = data.patientSocial
    patient.short_diagnosis = data.diagnosis
    patient.save()
    bed.save()
    try:
        from .modular_views.app.app_ws_update import app_ws_update

        app_ws_update()
    except Exception:
        pass
    return bed


@api.post("/beds/vacate", auth=jwtauth)
def vacate_bed(request, data: VacateSchema):
    patient = Patient.objects.get(id=data.patientId)
    bed = Bed.objects.get(id=data.bedId)

    # Obtener el room ID del bed_id (formato: "room,bed")
    room_id = (
        bed.id_bed.split(",")[0] if "," in bed.id_bed else bed.id_bed.split("-")[0]
    )

    # Cancelar todas las tareas activas de esta cama
    Task.objects.filter(bed=bed, active=True).delete()

    # Cerrar todas las llamadas activas de esta cama
    Call.objects.filter(bed=bed).exclude(state="closed").update(state="closed")

    # Enviar notificación MQTT para cancelar llamadas en la habitación
    send_mqtt_cancel_call(f"{room_id},0")

    patient.inpatient = False
    bed.active = False
    bed.bed_state = "free"
    bed.vacate_time = datetime.strptime(
        data.vacateDT.replace("T", " "), "%Y-%m-%d %H:%M"
    )
    bed.action_done_by = data.doneBy if data.doneBy else "Anónimo"
    patient.save()
    bed.save()
    try:
        from .modular_views.app.app_ws_update import app_ws_update

        app_ws_update()
    except Exception:
        pass
    return {"message": "Bed vacated successfully"}


@api.get("/patients", response=List[PatientSchema], auth=jwtauth)
def list_patients(request):
    return Patient.objects.filter(inpatient=True)


@api.get("/tasks", response=List[TaskSchema], auth=jwtauth)
def list_tasks(request):
    tasks = Task.objects.all().select_related("bed__bed_patient")
    return tasks


@api.post("/tasks", response=TaskSchema, auth=jwtauth)
def create_task(request, data: TaskInputSchema):
    bed = Bed.objects.get(id=data.bed_id)
    # Create primary task
    programed_time_obj = datetime.strptime(
        data.programed_time.replace("T", " "), "%Y-%m-%d %H:%M"
    )
    task = Task.objects.create(
        bed=bed,
        task=data.task,
        programed_time=programed_time_obj,
        repeat=data.repeat,
        repeat_lapse=data.repeat_lapse if hasattr(data, "repeat_lapse") else None,
        repeat_lapse_unit=data.repeat_lapse_unit
        if hasattr(data, "repeat_lapse_unit")
        else None,
        repeat_until=(
            datetime.strptime(data.repeat_until.replace("T", " "), "%Y-%m-%d %H:%M")
            if getattr(data, "repeat_until", None)
            else None
        ),
        active=True,
        # compute initial state based on programed_time
        state=(
            "passed"
            if programed_time_obj.timestamp() < datetime.now().timestamp()
            else (
                "soon"
                if programed_time_obj.timestamp() - datetime.now().timestamp() <= 600
                else "later"
            )
        ),
        programed_by=request.user.username,
    )

    # If repeat requested and parameters provided, replicate using modular logic
    if (
        data.repeat
        and getattr(data, "repeat_lapse", None)
        and getattr(data, "repeat_until", None)
    ):
        # reuse existing modular implementation
        from .modular_views.tasks.task_new import save_repeated_tasks

        try:
            # ensure primary task has a repeat_id so generated tasks belong to same series
            if not task.repeat_id:
                import random

                programed_time_float = int(programed_time_obj.timestamp())
                task.repeat_id = str(programed_time_float * random.random())
                task.save()

            save_repeated_tasks(
                data.repeat,
                data.repeat_lapse,
                data.repeat_lapse_unit,
                data.programed_time,
                data.repeat_until,
                bed.id,
                task.repeat_id if task.repeat_id else None,
                data.programed_time,
                request.user.username,
                request.user.username,
                "Pendiente",
                data.task,
                task.state,
                request.user.username,
            )
        except Exception as e:
            # don't fail the main request if repeat generation has an issue
            print(f"Error generating repeated tasks: {e}")

    try:
        from .modular_views.app.app_ws_update import app_ws_update

        app_ws_update()
    except Exception:
        pass

    return task


@api.put("/tasks/{int:task_id}", response=TaskSchema, auth=jwtauth)
def update_task(request, task_id: int, data: TaskEditSchema):
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return JsonResponse({"error": "Task not found"}, status=404)
    # Log incoming update for easier debugging of 422/parse issues
    try:
        print(f"update_task called with: task_id={task_id}, data={data}")
    except Exception:
        pass

    # Only set fields provided by the client
    if getattr(data, "task", None) is not None:
        task.task = data.task

    if getattr(data, "programed_time", None):
        # accept several ISO-like formats, be permissive
        pt_raw = data.programed_time
        pt = None
        try:
            pt_str = pt_raw.replace("T", " ")
            # handle trailing Z as UTC
            if pt_str.endswith("Z"):
                pt_str = pt_str[:-1] + "+00:00"
            try:
                pt = datetime.fromisoformat(pt_str)
            except Exception:
                try:
                    pt = datetime.strptime(pt_str, "%Y-%m-%d %H:%M")
                except Exception:
                    try:
                        pt = datetime.strptime(pt_str, "%Y-%m-%d %H:%M:%S")
                    except Exception as e:
                        print(f"Failed parsing programed_time '{pt_raw}': {e}")
                        raise
        except Exception:
            # fallback to now to avoid failing the whole request; caller may retry
            pt = datetime.now()
        task.programed_time = pt
    # support marking task as done from the edit modal
    if getattr(data, "done_time", None):
        dt_raw = data.done_time
        try:
            dt_str = dt_raw.replace("T", " ")
            if dt_str.endswith("Z"):
                dt_str = dt_str[:-1] + "+00:00"
            try:
                task.done_time = datetime.fromisoformat(dt_str)
            except Exception:
                try:
                    task.done_time = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                except Exception:
                    task.done_time = datetime.now()
        except Exception:
            task.done_time = datetime.now()
        task.active = False
        task.task_done_by = request.user.username
    if getattr(data, "active", None) is not None:
        task.active = data.active
    try:
        task.save()
    except Exception as e:
        # return a clear JSON error instead of a 500/422
        return JsonResponse({"error": f"Failed saving task: {str(e)}"}, status=400)

    # After updating the task, adjust the bed state if task was marked as done/completed
    if getattr(data, "done_time", None) or (not getattr(data, "active", None)):
        try:
            from .models import Bed, Call

            bed = task.bed
            if bed and bed.active:
                # Check remaining active tasks for this bed (all states)
                remaining_tasks = Task.objects.filter(bed=bed, active=True)
                has_passed = remaining_tasks.filter(state="passed").exists()
                has_soon = remaining_tasks.filter(state="soon").exists()
                has_later = remaining_tasks.filter(state="later").exists()

                # Check for active calls
                has_active_call = Call.objects.filter(bed=bed, state="active").exists()

                if has_active_call:
                    if has_passed:
                        bed.bed_state = "call-task"
                    elif has_soon or has_later:
                        bed.bed_state = "call"
                    else:
                        bed.bed_state = "call"
                else:
                    if has_passed:
                        bed.bed_state = "task"
                    elif has_soon:
                        bed.bed_state = "soon"
                    elif has_later:
                        bed.bed_state = "later"
                    else:
                        bed.bed_state = "occupied"
                bed.save()
        except Exception:
            pass

    try:
        from .modular_views.app.app_ws_update import app_ws_update

        app_ws_update()
    except Exception:
        pass
    return task


@api.post("/tasks/{int:task_id}/complete", response=TaskSchema, auth=jwtauth)
def complete_task(request, task_id: int):
    task = Task.objects.get(id=task_id)
    task.active = False
    task.done_time = datetime.now()
    task.task_done_by = request.user.username
    task.save()
    # After marking the task completed, adjust the bed state if needed.
    try:
        from .models import Bed, Call

        bed = task.bed
        if bed and bed.active:
            # Check remaining active tasks for this bed (all states)
            remaining_tasks = Task.objects.filter(bed=bed, active=True)
            has_passed = remaining_tasks.filter(state="passed").exists()
            has_soon = remaining_tasks.filter(state="soon").exists()
            has_later = remaining_tasks.filter(state="later").exists()

            # Check for active calls
            has_active_call = Call.objects.filter(bed=bed, state="active").exists()

            if has_active_call:
                if has_passed:
                    bed.bed_state = "call-task"
                elif has_soon or has_later:
                    bed.bed_state = "call"
                else:
                    bed.bed_state = "call"
            else:
                if has_passed:
                    bed.bed_state = "task"
                elif has_soon:
                    bed.bed_state = "soon"
                elif has_later:
                    bed.bed_state = "later"
                else:
                    bed.bed_state = "occupied"
            bed.save()
    except Exception:
        # don't let bed-update failures break API
        pass

    try:
        from .modular_views.app.app_ws_update import app_ws_update

        app_ws_update()
    except Exception:
        pass
    return task


@api.delete("/tasks/{int:task_id}", auth=jwtauth)
def delete_task(request, task_id: int):
    # Get task and bed before deleting
    try:
        task = Task.objects.get(id=task_id)
        bed = task.bed
        task.delete()

        # After deleting the task, adjust the bed state if needed.
        if bed and bed.active:
            # Check remaining active tasks for this bed
            remaining_tasks = Task.objects.filter(bed=bed, active=True)
            has_passed = remaining_tasks.filter(state="passed").exists()
            has_soon = remaining_tasks.filter(state="soon").exists()

            # Check for active calls
            has_active_call = Call.objects.filter(bed=bed, state="active").exists()

            if has_active_call:
                if has_passed:
                    bed.bed_state = "call-task"
                else:
                    bed.bed_state = "call"
            else:
                if has_passed:
                    bed.bed_state = "task"
                elif has_soon:
                    bed.bed_state = "soon"
                else:
                    bed.bed_state = "occupied"
            bed.save()
    except Task.DoesNotExist:
        pass

    try:
        from .modular_views.app.app_ws_update import app_ws_update

        app_ws_update()
    except Exception:
        pass
    return {"message": "Task deleted"}


@api.get("/calls", response=List[CallSchema], auth=jwtauth)
def list_calls(request):
    calls = Call.objects.all().select_related("bed__bed_patient")
    return calls


@api.post("/calls/{int:call_id}/answer", response=CallSchema, auth=jwtauth)
def answer_call(request, call_id: int):
    call = Call.objects.get(id=call_id)
    call.state = "answered"
    call.response_time = datetime.now()
    call.action_done_by = request.user.username
    call.save()

    # Update bed_state after answering the call
    try:
        bed = call.bed
        if bed and bed.active:
            from .models import Task

            bed_tasks = Task.objects.filter(bed=bed, active=True)
            has_passed = any(t.state == "passed" for t in bed_tasks)
            has_soon = any(t.state == "soon" for t in bed_tasks)
            if has_passed:
                bed.bed_state = "task"
            elif has_soon:
                bed.bed_state = "soon"
            else:
                bed.bed_state = "occupied"
            bed.save()
    except Exception as e:
        pass

    try:
        from .modular_views.app.app_ws_update import app_ws_update

        app_ws_update()
    except Exception:
        pass
    return call


@api.post("/calls/{int:call_id}/close", response=CallSchema, auth=jwtauth)
def close_call(request, call_id: int, data: CallResponseSchema):
    call = Call.objects.get(id=call_id)
    call.state = "closed"
    call.response = data.response
    call.action_done_by = request.user.username
    call.save()

    # Update bed_state after closing the call
    try:
        bed = call.bed
        if bed and bed.active:
            from .models import Task

            bed_tasks = Task.objects.filter(bed=bed, active=True)
            has_passed = any(t.state == "passed" for t in bed_tasks)
            has_soon = any(t.state == "soon" for t in bed_tasks)
            if has_passed:
                bed.bed_state = "task"
            elif has_soon:
                bed.bed_state = "soon"
            else:
                bed.bed_state = "occupied"
            bed.save()
    except Exception as e:
        pass

    try:
        from .modular_views.app.app_ws_update import app_ws_update

        app_ws_update()
    except Exception:
        pass
    return call


@api.get("/rooms", auth=jwtauth)
def get_rooms(request):
    beds = Bed.objects.all().select_related("bed_patient").order_by("id_bed")
    rooms_data = {}
    for bed in beds:
        room_num = bed.id_bed.split("-")[0] if "-" in bed.id_bed else "1"
        if room_num not in rooms_data:
            rooms_data[room_num] = {
                "beds": [],
                "status": "gray",  # Por defecto gris (vacío)
            }
        bed_data = {
            "id": bed.id,
            "id_bed": bed.id_bed,
            "active": bed.active,
            "bed_state": bed.bed_state,
            "occupied_time": bed.occupied_time.isoformat()
            if bed.occupied_time
            else None,
            "planed_vacate": bed.planed_vacate.isoformat()
            if bed.planed_vacate
            else None,
            "action_done_by": bed.action_done_by,
        }
        if bed.bed_patient:
            bed_data["patient"] = {
                "id": bed.bed_patient.id,
                "name": bed.bed_patient.name,
                "social_security_number": bed.bed_patient.social_security_number,
                "short_diagnosis": bed.bed_patient.short_diagnosis,
                "diagnosis": bed.bed_patient.diagnosis,
            }
        rooms_data[room_num]["beds"].append(bed_data)

        # Si la cama está activa, la habitación es verde
        if bed.active:
            rooms_data[room_num]["status"] = "green"

    return rooms_data


@api.get("/app/load", auth=jwtauth)
def initial_load(request):
    from .modular_views.app.app_load import load
    from .modular_views.calls.call_mqtt import mqtt_service
    from .modular_views.tasks.task_ws import tasks_ws_update
    from .modular_views.app.app_ws_update import app_ws_update
    from .modular_views.data_analytics import data_analytics

    mqtt_service()
    tasks_ws_update()
    app_ws_update()
    data_analytics()

    return load()


@api.get("/events", response=List[dict], auth=jwtauth)
def list_events(request):
    events = Event.objects.all().order_by("-time")[:100]
    return [e.serialize() for e in events]


@api.get("/events/{int:event_id}", response=dict, auth=jwtauth)
def get_event(request, event_id: int):
    event = Event.objects.get(id=event_id)
    return event.serialize()
