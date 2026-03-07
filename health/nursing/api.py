from django.contrib.auth import authenticate
from ninja import NinjaAPI, ModelSchema, Schema
from typing import Optional, List
from datetime import datetime
from ninja.security import HttpBearer
from ninja_jwt.tokens import RefreshToken
from ninja_jwt.authentication import JWTAuth
from .models import User, Patient, Bed, Task, Call, Record
import paho.mqtt.client as mqtt
import json

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


class TaskEditSchema(Schema):
    task_id: int
    task: str
    programed_time: str


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
    return {"error": "Invalid credentials"}, 401


@api.post("/auth/register", response=UserSchema, auth=None)
def register(request, data: UserCreateSchema):
    user = User.objects.create_user(
        username=data.username,
        email=data.email,
        password=data.password,
        is_leader=data.is_leader,
    )
    return user


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
def create_bed(request, data: BedInputSchema):
    patient = Patient.objects.create(
        name=data.patientName if data.patientName else "No Name",
        social_security_number=data.patientSocial if data.patientSocial else "0000",
        short_diagnosis=data.diagnosis if data.diagnosis else "No Diagnosis",
    )
    bed = Bed.objects.create(
        id_bed=data.roomBedId,
        bed_patient=patient,
        active=True,
        bed_state="occupied",
        occupied_time=datetime.strptime(
            data.occupiedDateTime.replace("T", " "), "%Y-%m-%d %H:%M"
        ),
        planed_vacate=datetime.strptime(
            data.planedVacate.replace("T", " "), "%Y-%m-%d %H:%M"
        ),
        action_done_by=data.doneBy if data.doneBy else "Anónimo",
    )
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
    task = Task.objects.create(
        bed=bed,
        task=data.task,
        programed_time=datetime.strptime(
            data.programed_time.replace("T", " "), "%Y-%m-%d %H:%M"
        ),
        repeat=data.repeat,
        active=True,
        programed_by=request.user.username,
    )
    return task


@api.put("/tasks/{int:task_id}", response=TaskSchema, auth=jwtauth)
def update_task(request, task_id: int, data: TaskEditSchema):
    task = Task.objects.get(id=task_id)
    task.task = data.task
    task.programed_time = datetime.strptime(
        data.programed_time.replace("T", " "), "%Y-%m-%d %H:%M"
    )
    task.save()
    return task


@api.post("/tasks/{int:task_id}/complete", response=TaskSchema, auth=jwtauth)
def complete_task(request, task_id: int):
    task = Task.objects.get(id=task_id)
    task.active = False
    task.done_time = datetime.now()
    task.task_done_by = request.user.username
    task.save()
    return task


@api.delete("/tasks/{int:task_id}", auth=jwtauth)
def delete_task(request, task_id: int):
    Task.objects.get(id=task_id).delete()
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
    return call


@api.post("/calls/{int:call_id}/close", response=CallSchema, auth=jwtauth)
def close_call(request, call_id: int, data: CallResponseSchema):
    call = Call.objects.get(id=call_id)
    call.state = "closed"
    call.response = data.response
    call.action_done_by = request.user.username
    call.save()
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


@api.get("/records", response=List[dict], auth=jwtauth)
def list_records(request):
    records = Record.objects.all().order_by("-time")[:100]
    return [r.serialize() for r in records]
