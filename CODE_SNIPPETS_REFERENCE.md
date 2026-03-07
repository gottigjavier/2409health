# Health App - Code Snippets Reference

## 1. BROKEN TASK REPEAT FLOW

### Frontend NewTaskModal.js (BROKEN)
Location: `/health/nursing_react/src/components/tasks-list/task-modal/NewTaskModal.js:24-77`

```javascript
// Lines 24-28: Frontend collects ALL repeat data
const [repeatIsChecked, setRepeatIsChecked] = useState(false)
const [repeatUntilDate, setRepeatUntilDate] = useState()
const [repeatUntilTime, setRepeatUntilTime] = useState()
const [repeatLapse, setRepeatLapse] = useState(2)
const [repeatLapseUnit, setRepeatLapseUnit] = useState('hours')

// Lines 73-77: But ONLY sends repeat boolean!
const payload = {
    bed_id: bedId,
    task: textAction,
    programed_time: programedDT,
    repeat: repeatIsChecked    // ← MISSING: repeatLapse, repeatLapseUnit, repeatUntil!
};

// Line 80: Sends to API
authFetch('/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)  // ← INCOMPLETE payload!
})
```

**What's missing from payload:**
- repeatLapse (2)
- repeatLapseUnit ('hours')
- repeatUntilDate + repeatUntilTime

---

### Backend api.py (BROKEN)
Location: `/health/nursing/nursing/api.py:164-168`

```python
# TaskInputSchema - only accepts 4 fields
class TaskInputSchema(Schema):
    bed_id: int
    task: str
    programed_time: str
    repeat: bool = False
    # ← MISSING: repeat_lapse, repeat_lapse_unit, repeat_until

# POST endpoint - can't create multiple tasks
@api.post("/tasks", response=TaskSchema, auth=jwtauth)
def create_task(request, data: TaskInputSchema):
    bed = Bed.objects.get(id=data.bed_id)
    task = Task.objects.create(
        bed=bed,
        task=data.task,
        programed_time=datetime.strptime(
            data.programed_time.replace("T", " "), "%Y-%m-%d %H:%M"
        ),
        repeat=data.repeat,  # ← Just a boolean! Doesn't create multiple tasks
        active=True,
        programed_by=request.user.username,
    )
    return task  # ← Returns single task only
```

---

### Legacy Implementation (WORKS but UNUSED)
Location: `/health/nursing/modular_views/tasks/task_new.py:7-65`

```python
# This function accepts ALL the repeat parameters but is NEVER called by API!
def modular_new_task(request):
    data = json.loads(request.body)
    bed_id = data['bedId']
    programed_time = data['programedDT']
    done_time = data['doneDT']
    programed_by = data['programer']
    task_text = data['textAction']
    task_state = data['state']
    task_repeat_checked = data['repeatIsChecked']
    task_repeat_lapse = data['repeatLapse']              # ← Has repeat_lapse
    task_repeat_lapse_unit = data['repeatLapseUnit']    # ← Has repeat_lapse_unit
    task_repeat_until = data['repeatUntil']             # ← Has repeat_until
    
    # ... create initial task ...
    
    if task_repeat_checked:
        save_repeated_tasks(                  # ← Creates multiple tasks!
            task_repeat_checked,
            task_repeat_lapse,
            task_repeat_lapse_unit,
            programed_time,
            task_repeat_until,
            bed_id,
            task_repeat_id,
            # ... more params ...
        )

# Lines 68-132: save_repeated_tasks() function
def save_repeated_tasks(task_repeat_checked,
                        task_repeat_lapse, 
                        task_repeat_lapse_unit, 
                        programed_time, 
                        task_repeat_until,
                        bed_id,
                        task_repeat_id,
                        # ... 7 more parameters ...
                        ):
    # Convert repeat_lapse_unit to seconds
    time_factor = int(task_repeat_lapse) * 60
    if task_repeat_lapse_unit == 'hours':
        time_factor = int(task_repeat_lapse) * 3600
    if task_repeat_lapse_unit == 'days':
        time_factor = int(task_repeat_lapse) * 86400
    
    # Calculate how many tasks to create
    task_repeat_until_float = datetime.strptime(task_repeat_until, ...).timestamp()
    programed_time_float = datetime.strptime(programed_time, ...).timestamp()
    task_count = int((task_repeat_until_float - programed_time_float) / time_factor)
    
    # Create a task for each interval
    for i in range(1, task_count + 1):
        programed_time_float = programed_time_float + time_factor
        # Set state based on time until execution
        if programed_time_float - time_now_float < 600:
            task_state = 'soon'
        else:
            task_state = 'later'
        
        programed_time = datetime.fromtimestamp(programed_time_float)
        
        task = Task()
        task.bed = bed
        task.repeat = task_repeat_checked
        task.repeat_id = task_repeat_id  # ← Groups all repeat tasks together
        task.task = task_text
        task.programed_time = programed_time
        # ... more fields ...
        task.state = task_state
        task.active = True
        task.save()  # ← Creates one task per interval!
```

---

## 2. MISSING TASK MODEL FIELDS

Location: `/health/nursing/models.py:137-166`

```python
class Task(models.Model):
    bed = models.ForeignKey(Bed, related_name="task_bed", on_delete=models.CASCADE)
    repeat = models.BooleanField(default=False)
    repeat_id = models.CharField(max_length=50, null=True, blank=True)
    task = models.TextField(default="Tarea de Rutina")
    programed_time = models.DateTimeField(null=True, blank=True)
    done_time = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=False)
    state = models.CharField(default="soon", max_length=15)
    programed_by = models.CharField(default="Anónimo", max_length=50)
    task_done_by = models.CharField(default="Pendiente", max_length=50)
    action_done_by = models.CharField(default="Anónimo", max_length=50)
    
    # ↓ MISSING FIELDS NEEDED FOR REPEAT LOGIC:
    # repeat_lapse = models.IntegerField(default=1, null=True, blank=True)
    # repeat_lapse_unit = models.CharField(max_length=10, default="hours", null=True, blank=True)
    # repeat_until = models.DateTimeField(null=True, blank=True)
```

**To fix, add database migration:**

```python
# models.py - add to Task class
repeat_lapse = models.IntegerField(default=1, null=True, blank=True)
repeat_lapse_unit = models.CharField(
    max_length=10, 
    choices=[('minutes', 'Minutes'), ('hours', 'Hours'), ('days', 'Days')],
    default='hours',
    null=True,
    blank=True
)
repeat_until = models.DateTimeField(null=True, blank=True)
```

---

## 3. BED STATE MANAGEMENT (MISSING IN API)

### What SHOULD happen:
Location: `/health/nursing/modular_views/tasks/task_new.py:27-31`

```python
def modular_new_task(request):
    # ... create task ...
    task_state = data['state']
    
    bed = Bed.objects.get(id=bed_id)
    if task_state == 'passed':
        if bed.bed_state == 'call' or bed.bed_state == 'call-task':
            bed.bed_state = 'call-task'    # ← Combine call + task
        else:
            bed.bed_state = 'task'         # ← New task indicator
    bed.save()
```

### What ACTUALLY happens in API:
Location: `/health/nursing/api.py:339-352`

```python
@api.post("/tasks", response=TaskSchema, auth=jwtauth)
def create_task(request, data: TaskInputSchema):
    bed = Bed.objects.get(id=data.bed_id)
    task = Task.objects.create(
        bed=bed,
        task=data.task,
        programed_time=datetime.strptime(...),
        repeat=data.repeat,
        active=True,
        programed_by=request.user.username,
    )
    return task  # ← NO BED STATE UPDATE!
```

### State Transitions (task_edit.py handles this properly):
Location: `/health/nursing/modular_views/tasks/task_edit.py:28-52`

```python
def edit_task_bed_color(task, bed_task_list, task_state, task_active):
    if len(bed_task_list) == 1:
        bed = Bed.objects.get(id=task.bed.pk)
        if bed_task_list[0].id == task.pk:
            if not task_active:
                # Task is now inactive
                if bed.bed_state == 'call-task':
                    bed.bed_state = 'call'      # ← Remove task indicator
                else:
                    bed.bed_state = 'occupied'  # ← Back to normal
            else:
                # Task is active
                if task_state != 'passed':
                    if bed.bed_state == 'call-task' or bed.bed_state == 'call':
                        bed.bed_state = 'call'   # ← Keep call indicator
                    else:
                        bed.bed_state = 'occupied'
        bed.save()
    
    if len(bed_task_list) == 0:
        # No passed tasks, but this task is being activated
        bed = Bed.objects.get(id=task.bed.pk)
        if task_active and task_state == 'passed':
            if bed.bed_state == 'call':
                bed.bed_state = 'call-task'    # ← Add task indicator
            else:
                bed.bed_state = 'task'
        bed.save()
```

**API Endpoints DON'T do any of this!**

---

## 4. INCONSISTENT FRONTEND ENDPOINTS

### NewTaskModal (uses API):
Location: `/health/nursing_react/src/components/tasks-list/task-modal/NewTaskModal.js:80-88`

```javascript
authFetch('/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
})
.then(response => response.json())  
.then(() => fetchLoad())
.then(data => setAppState(data))
```

### EditTaskModal (uses OLD endpoint):
Location: `/health/nursing_react/src/components/tasks-list/task-modal/EditTaskModal.js:61-78`

```javascript
fetch('http://localhost:8000/nursing/edit_task', {  // ← HARDCODED OLD ENDPOINT!
    method: 'PUT',
    headers: {
        'Access-Control-Allow-Origin': '*',
        'crossorigin': 'anonymous',
        'Cache-Control': 'no-cache'
    },
    body: JSON.stringify({
        taskId,
        currentBed,
        programedDT,
        doneDT,
        programer,
        editor,
        maker,
        textAction,
        state,
        active
    })
})
```

### CallsList (uses OLD endpoint):
Location: `/health/nursing_react/src/components/calls-list/CallsList.js:81-91`

```javascript
const saveAnsweredCall = async (saveCallsList) => {
    if (saveCallsList.length > 0) {            
        await fetch('http://localhost:8000/nursing/answered_call', {  // ← OLD!
            method: 'POST',
            headers: {
                'Access-Control-Allow-Origin': '*',
                'crossorigin': 'anonymous',
                'Cache-Control': 'no-cache'
            },
            body: JSON.stringify({ saveCallsList })
        })
```

---

## 5. WEBSOCKET UPDATES

### What triggers WebSocket broadcast:
Location: `/health/nursing/modular_views/app/app_ws_update.py:44-50`

```python
def app_ws_update():
    all_data = json.loads(ws_load_encoded())
    layer = get_channel_layer()
    async_to_sync(layer.group_send)('appboard', {
        'type': 'deprocessing',
        'all_data': all_data,
    })  # ← Broadcasts to all connected WebSocket clients
```

### Called from:
- `app_load.py:32-33` - Initial load
- `task_new.py:49` - When new task created (LEGACY, not API)
- `task_edit.py:26` - When task edited (LEGACY, not API)
- `task_delete.py:32` - When task deleted (LEGACY, not API)
- `call_close.py:24` - When call closed (LEGACY, not API)

### API endpoints that DON'T trigger it:
- `POST /api/tasks` - No broadcast
- `PUT /api/tasks/{id}` - No broadcast
- `POST /api/tasks/{id}/complete` - No broadcast
- `DELETE /api/tasks/{id}` - No broadcast
- `POST /api/calls/{id}/answer` - No broadcast
- `POST /api/calls/{id}/close` - No broadcast

**RESULT**: Frontend might not see updates from API operations!

---

## 6. TASK STATE SCHEDULER (WORKS)

Location: `/health/nursing/modular_views/tasks/task_ws.py:14-71`

```python
def tasks_ws_update():
    """
    Runs on a schedule to:
    1. Update task states based on current time
    2. Update bed states when tasks pass their scheduled time
    3. Broadcast updates via WebSocket
    """
    tasks = Task.objects.filter(active=True).order_by('programed_time').all()
    if tasks:
        time_now = datetime.now()
        time_now_float = time_now.timestamp()
        
        for task in tasks:
            task_time = task.programed_time.timestamp()
            bed = Bed.objects.get(pk=task.bed.pk)
            
            if task_time - time_now_float > 0:
                # Task is in the future
                if task_time - time_now_float < 600:
                    task.state = 'soon'  # Within 10 minutes
            else:
                # Task time has passed
                task.state = 'passed'
                if bed.bed_state == 'call':
                    bed.bed_state = 'call-task'
                if bed.bed_state == 'occupied':
                    bed.bed_state = 'task'
            
            bed.save()
            task.save()
        
        # Broadcast updates
        tasks = Task.objects.filter(active=True).order_by('programed_time').all()
        beds = Bed.objects.filter(active=True).all()
        beds_list = serial_beds(beds)
        tasks_list = [task.serialize() for task in tasks]
        tasks_and_beds = {
            'beds_list': beds_list,
            'tasks_list': tasks_list
        }
        
        layer = get_channel_layer()
        async_to_sync(layer.group_send)('tasksboard', {
            'type': 'deprocessing',
            'tasks_and_beds': tasks_and_beds,
        })
        
        # Schedule next update
        tasks_scheduler()
```

**This works but only broadcasts to 'tasksboard' group, not 'appboard'!**

---

## 7. FRONTEND STATE STRUCTURE

Location: `/health/nursing_react/src/HealthApp.js:14-26`

```javascript
const [appState, setAppState] = useContext(AppContext);

// appState is updated with:
const handleApp = (msg) => {
    if (msg) {
        setAppState(msg);
        setLocalAppState(msg);
    }
};

// appState structure (from backend app_load.py):
{
    beds: [
        {
            id: 1,
            id_bed: "1,1",           // "room,bed" format
            active: true,
            bed_state: "occupied",   // free, occupied, call, task, call-task
            occupied_time: "2024-01-01T10:00:00",
            planed_vacate: "2024-01-05T10:00:00",
            action_done_by: "nurse_name",
            patient: {
                id: 1,
                name: "Patient Name",
                social_security_number: "123456789",
                short_diagnosis: "Diagnosis",
                diagnosis: "Full diagnosis text"
            }
        }
    ],
    
    patients: [
        {
            id, name, social_security_number, image, inpatient,
            admission, diagnosis, short_diagnosis, treatment_roadmap,
            action_done_by
        }
    ],
    
    tasks: [
        {
            id: 1,
            bed_id: 1,               // Foreign key to bed
            repeat: false,
            repeat_id: "123.456",    // Groups repeated tasks
            bed: "1,1",              // "room,bed" format
            patient: "Patient Name",
            task: "Change bandages",
            programed_time: "2024-01-01T14:00:00",
            done_time: null,
            active: true,
            state: "soon",           // later, soon, passed
            programed_by: "nurse_name",
            task_done_by: "Pendiente",
            action_done_by: "nurse_name"
        }
    ],
    
    calls: [
        {
            id: 1,
            bed_id: 1,
            bed: "1,1",
            patient: "Patient Name",
            call_time: "2024-01-01T10:30:00",
            response_time: "2024-01-01T10:35:00",
            response: "Response text",
            state: "active",         // active, answered, closed
            action_done_by: "nurse_name"
        }
    ]
}
```

---

## 8. CALL CREATION (MQTT ONLY)

Location: `/health/nursing/modular_views/calls/call_new.py:7-30`

```python
def new_call(bed):
    """Called from MQTT, NOT from API"""
    try:
        active_bed = Bed.objects.get(id_bed=bed, active=True)
    except:
        active_bed = {}
    try:
        call = Call.objects.get(state='active', bed__id_bed=bed)
    except:
        call = {}
    
    if not active_bed == {} and call == {}:
        # Update bed state
        if active_bed.bed_state == 'task':
            active_bed.bed_state = 'call-task'
        else:
            active_bed.bed_state = 'call'
        active_bed.save()
        
        # Create new call
        new_call = Call()
        new_call.bed = active_bed
        new_call.call_time = datetime.now()
        new_call.response_time = datetime.now()  # ← BUG: Set on creation!
        new_call.state = 'active'
        new_call.save()
        return ws_load()  # ← Returns updated app state
    else:
        pass  # Duplicate call or no active bed
```

**API has NO equivalent endpoint!**

---

## 9. DUPLICATE WEBSOCKET FILES

### Working (used in HealthApp.js):
Location: `/health/nursing_react/src/services/websocket.js`

```javascript
const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

const getToken = () => localStorage.getItem('access_token');

export const getWsUrl = (path) => {
    const token = getToken();
    if (token) {
        return `${WS_URL}${path}?token=${token}`;  // ← Passes token!
    }
    return `${WS_URL}${path}`;
};

export const appManager = ({ handleApp }) => {
    const wsUrl = getWsUrl('/ws/appData/');  // ← Uses env variable
    const call = new WebSocket(wsUrl);
    // ... handlers ...
    return call;
};
```

### Not Used (hardcoded):
Location: `/health/nursing_react/src/services/app-socket.js`

```javascript
export const appManager = ({handleApp}) => {
    const call = new WebSocket('ws://127.0.0.1:8000/ws/appData/');  // ← HARDCODED!
    // ... handlers ...
}
```

**Same for calls-socket.js and tasks-socket.js - all UNUSED!**

---

## 10. SECURITY ISSUE: HARDCODED MQTT KEY

Location: `/health/nursing/api.py:17-37`

```python
def send_mqtt_cancel_call(bed_id_str):
    client = mqtt.Client()
    client.connect("mosquitto", 1883)
    
    message = {
        "state": False,
        "id": bed_id_str,
        "key": "this&is$a$key&to?prevent?hacking",  # ← HARDCODED IN SOURCE!
    }
    client.publish("mqtt/call/", json.dumps(message))
```

Also in `/health/nursing/consumer.py:62`:

```python
if data['key'] == 'this&is$a$key&to?prevent?hacking':  # ← Visible in code!
    # Process the message
```

And in `/health/nursing/modular_views/calls/call_mqtt.py:27`:

```python
if data["key"] == "this&is$a$key&to?prevent?hacking":  # ← THREE PLACES!
    # Process the message
```

**Should use environment variable instead:**

```python
MQTT_KEY = os.getenv('MQTT_SECURITY_KEY', 'this&is$a$key&to?prevent?hacking')
```

---

## KEY TAKEAWAYS

1. **Repeat feature is completely broken** - Params not sent, logic not called
2. **Dual code paths** - API and modular_views do different things
3. **State management incomplete** - Bed states not updated by API
4. **WebSocket not triggered** - Many operations don't broadcast updates
5. **Old endpoints still used** - EditTaskModal and CallsList use legacy code
6. **Missing fields** - Task model lacks repeat_lapse, repeat_until, etc.
7. **Security exposed** - Hardcoded MQTT key visible in source

