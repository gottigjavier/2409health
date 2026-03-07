# Health App Codebase Analysis Report

## Executive Summary
The health monitoring app has a Django REST API backend (using Django Ninja) with React frontend, WebSocket real-time updates via Channels, and MQTT integration. The codebase has several architectural inconsistencies and missing implementations that could cause issues with task repeat functionality, API endpoints, and state management.

---

## 1. BACKEND API ENDPOINTS ANALYSIS

### 1.1 Tasks API Endpoints

**File**: `/health/nursing/api.py`

#### Created/Implemented Endpoints:
- `POST /api/tasks` - Create task (line 339-352)
  - Schema: `TaskInputSchema` - accepts `bed_id`, `task`, `programed_time`, `repeat` (bool)
  - Returns: `TaskSchema`
  - **Issue**: Does NOT support repeat_lapse, repeat_lapse_unit, repeat_until
  
- `PUT /api/tasks/{int:task_id}` - Update task (line 355-363)
  - Schema: `TaskEditSchema` - accepts `task_id`, `task`, `programed_time`
  - Returns: `TaskSchema`
  - **Issue**: Does NOT support state/active updates
  
- `POST /api/tasks/{int:task_id}/complete` - Mark task complete (line 366-373)
  - No input schema required
  - Sets: `active=False`, `done_time=datetime.now()`, `task_done_by=username`
  - Returns: `TaskSchema`
  
- `DELETE /api/tasks/{int:task_id}` - Delete task (line 376-379)
  - Returns: simple message
  
- `GET /api/tasks` - List all tasks (line 333-336)

#### Missing Modular View Integration:
The API endpoints do NOT use the modular views that exist:
- `/health/nursing/modular_views/tasks/task_new.py` - Has repeat logic
- `/health/nursing/modular_views/tasks/task_edit.py` - Has bed state logic
- `/health/nursing/modular_views/tasks/task_delete.py` - Has repeat deletion logic

**This is a critical architectural problem**: The API endpoints bypass the business logic in modular_views.

### 1.2 Calls API Endpoints

**File**: `/health/nursing/api.py`

#### Implemented Endpoints:
- `POST /api/calls/{int:call_id}/answer` - Answer call (line 388-395)
  - Sets: `state='answered'`, `response_time=datetime.now()`, `action_done_by=username`
  
- `POST /api/calls/{int:call_id}/close` - Close call (line 398-405)
  - Schema: `CallResponseSchema` - accepts `bed_id`, `response`
  - Sets: `state='closed'`, `response`, `action_done_by=username`
  
- `GET /api/calls` - List all calls (line 382-385)

#### Missing Modular View Integration:
- `/health/nursing/modular_views/calls/call_new.py` - Creates calls with bed state management
- `/health/nursing/modular_views/calls/call_answered.py` - Has bed state logic
- `/health/nursing/modular_views/calls/call_close.py` - Has recording logic

### 1.3 Beds API Endpoints

#### Implemented Endpoints:
- `POST /api/beds` - Create bed (line 255-275)
- `GET /api/beds` - List beds (line 243-246)
- `GET /api/beds/{id}` - Get bed (line 249-252)
- `PUT /api/beds/{id}` - Update bed (line 278-294)
- `POST /api/beds/vacate` - Vacate bed (line 297-325)

---

## 2. TASK MODEL & SERIALIZATION

**File**: `/health/nursing/models.py` (lines 137-166)

```python
class Task(models.Model):
    bed = ForeignKey(Bed)
    repeat = BooleanField(default=False)          # ✓ Repeat enabled flag
    repeat_id = CharField(max_length=50)          # ✓ Groups repeated tasks
    task = TextField(default="Tarea de Rutina")
    programed_time = DateTimeField(null=True)
    done_time = DateTimeField(null=True)
    active = BooleanField(default=False)
    state = CharField(default="soon")             # later, soon, passed
    programed_by = CharField()
    task_done_by = CharField(default="Pendiente")
    action_done_by = CharField()
```

**Missing Fields**: 
- No `repeat_lapse` field
- No `repeat_lapse_unit` field  
- No `repeat_until` field

These fields exist in the frontend and modular views but NOT in the model!

### Task States:
- `"later"` - Task scheduled >10 minutes away
- `"soon"` - Task scheduled <10 minutes away
- `"passed"` - Task scheduled time has passed

---

## 3. REPEAT/RECURRENCE FUNCTIONALITY

### 3.1 Frontend Implementation (NewTaskModal.js)

**File**: `/health/nursing_react/src/components/tasks-list/task-modal/NewTaskModal.js`

Lines 24-28 show repeat interface:
```javascript
const [repeatIsChecked, setRepeatIsChecked] = useState(false)
const [repeatUntilDate, setRepeatUntilDate] = useState()
const [repeatUntilTime, setRepeatUntilTime] = useState()
const [repeatLapse, setRepeatLapse] = useState(2)
const [repeatLapseUnit, setRepeatLapseUnit] = useState('hours')
```

**Frontend Payload** (line 73-77):
```javascript
const payload = {
    bed_id: bedId,
    task: textAction,
    programed_time: programedDT,
    repeat: repeatIsChecked    // ← ONLY sends repeat flag
};
```

**Critical Issue**: Frontend collects repeat_lapse, repeat_lapse_unit, repeat_until but ONLY sends `repeat` boolean to the API!

### 3.2 Backend Modular View Implementation

**File**: `/health/nursing/modular_views/tasks/task_new.py`

Lines 68-132 show `save_repeated_tasks()` function that:
1. Calculates time_factor from repeat_lapse and repeat_lapse_unit
2. Converts to seconds (60s for minutes, 3600s for hours, 86400s for days)
3. Loops from programed_time to repeat_until, creating tasks at intervals
4. Sets task.state based on time until execution (within 600s = "soon")
5. Groups tasks by repeat_id (generated from: `str(programed_time_float * random.random())`)

**Function Signature** (lines 68-81):
```python
def save_repeated_tasks(
    task_repeat_checked,
    task_repeat_lapse,           # 2
    task_repeat_lapse_unit,      # 'hours', 'minutes', 'days'
    programed_time,              # ISO string
    task_repeat_until,           # ISO string
    bed_id,
    task_repeat_id,              # UUID for grouping
    done_time,
    programed_by,
    action_done_by,
    task_done_by,
    task_text,
    task_state,
    username
)
```

**THIS FUNCTION IS NEVER CALLED BY API** - it's only called by the old modular_views/tasks/task_new.py endpoint

### 3.3 Task Deletion with Repeat Support

**File**: `/health/nursing/modular_views/tasks/task_delete.py`

Lines 37-52: `delete_task_repeated()` function deletes all tasks with matching repeat_id.

**API endpoint** (`DELETE /api/tasks/{id}`) just deletes the single task - it doesn't check for repeat_id!

---

## 4. TASK EDITING ENDPOINTS

### 4.1 API Update Endpoint

**File**: `/health/nursing/api.py` (lines 355-363)

```python
@api.put("/tasks/{int:task_id}", response=TaskSchema, auth=jwtauth)
def update_task(request, task_id: int, data: TaskEditSchema):
    task = Task.objects.get(id=task_id)
    task.task = data.task
    task.programed_time = datetime.strptime(
        data.programed_time.replace("T", " "), "%Y-%m-%d %H:%M"
    )
    task.save()
    return task
```

**Issues**:
- Does NOT update `state` or `active` flags
- Schema only accepts: `task_id`, `task`, `programed_time`
- Does NOT handle bed state changes

### 4.2 Modular View Edit Logic

**File**: `/health/nursing/modular_views/tasks/task_edit.py`

Lines 6-26: `modular_edit_task()` function properly handles:
- State transitions (later/soon/passed)
- Bed state updates based on task state
- Recording changes in audit log
- Active flag management

**This more complete logic is NOT used by the API!**

---

## 5. TASK COMPLETION FLOW

### 5.1 API Complete Endpoint

**File**: `/health/nursing/api.py` (lines 366-373)

```python
@api.post("/tasks/{int:task_id}/complete", response=TaskSchema, auth=jwtauth)
def complete_task(request, task_id: int):
    task = Task.objects.get(id=task_id)
    task.active = False
    task.done_time = datetime.now()
    task.task_done_by = request.user.username
    task.save()
    return task
```

**Issues**:
- Does NOT trigger WebSocket updates
- Does NOT update bed state
- Does NOT handle repeated task logic
- No audit logging

### 5.2 Frontend Task Completion (EditTaskModal.js)

**File**: `/health/nursing_react/src/components/tasks-list/task-modal/EditTaskModal.js`

Lines 93-99: `doneTask()` function:
```javascript
const doneTask = () => {
    setDoneDate(formattingDate('y-m-d', new Date()))
    setDoneTime(formattingTime('h:m:s', new Date()))
    setTaskState(false)
    setDoneBy(doneBy)
    setTaskEditor(taskEditor)
    setTextResponse(textResponse => `${textResponse}(Done)`)
}
```

Then saves via PUT to `/nursing/edit_task` endpoint (old modular views, not API)

---

## 6. CALL ENDPOINTS & FLOW

### 6.1 Call Creation (MQTT-Driven)

**File**: `/health/nursing/modular_views/calls/call_new.py`

```python
def new_call(bed):
    active_bed = Bed.objects.get(id_bed=bed, active=True)
    call = Call.objects.get(state='active', bed__id_bed=bed)  # Check existing
    if not active_bed == {} and call == {}:
        if active_bed.bed_state == 'task':
            active_bed.bed_state = 'call-task'
        else:
            active_bed.bed_state = 'call'
        new_call = Call()
        new_call.bed = active_bed
        new_call.call_time = datetime.now()
        new_call.response_time = datetime.now()  # ← Wrong: set on creation
        new_call.state = 'active'
        new_call.save()
        return ws_load()
```

**API Note**: There's NO API endpoint to create calls. Calls are created by MQTT messages.

### 6.2 Call Answer & Close

**API Endpoints**:
- `POST /api/calls/{id}/answer` - Sets state='answered', response_time=now
- `POST /api/calls/{id}/close` - Sets state='closed', adds response text

**Frontend**: Uses old endpoints at `http://localhost:8000/nursing/answered_call` and `http://localhost:8000/nursing/close_call`

These old endpoints are in `urls.py` but NOT mapped to API!

---

## 7. WEBSOCKET & REAL-TIME UPDATES

### 7.1 WebSocket Channels

**File**: `/health/nursing/consumer.py`

Three consumer classes:

1. **appConsumer** (lines 7-38)
   - GroupName: `'appboard'`
   - Broadcasts full app state (beds, patients, tasks, calls)

2. **callConsumer** (lines 41-111)
   - GroupName: `'callsboard'`
   - Handles call MQTT messages
   - Validates security key: `'this&is$a$key&to?prevent?hacking'`

3. **taskConsumer** (lines 118-149)
   - GroupName: `'tasksboard'`
   - Broadcasts tasks_and_beds updates

### 7.2 WebSocket Broadcasting

**File**: `/health/nursing/modular_views/app/app_ws_update.py`

```python
def app_ws_update():
    all_data = json.loads(ws_load_encoded())  # Serialize to JSON
    layer = get_channel_layer()
    async_to_sync(layer.group_send)('appboard', {
        'type': 'deprocessing',
        'all_data': all_data,
    })
```

This is called after:
- Initial load
- Task creation
- Task edit
- Task deletion
- Task state changes

### 7.3 Task Scheduler (Background Job)

**File**: `/health/nursing/modular_views/tasks/task_ws.py`

Uses APScheduler to:
1. Update task states (later → soon → passed)
2. Update bed states when tasks become "passed"
3. Broadcast via WebSocket

**Key Logic** (lines 14-46):
```python
def tasks_ws_update():
    tasks = Task.objects.filter(active=True).order_by('programed_time')
    for task in tasks:
        task_time = task.programed_time.timestamp()
        if task_time - time_now_float > 0:
            if task_time - time_now_float < 600:
                task.state = 'soon'  # Within 10 minutes
        else:
            task.state = 'passed'    # Time has passed
            if bed.bed_state == 'call':
                bed.bed_state = 'call-task'
            elif bed.bed_state == 'occupied':
                bed.bed_state = 'task'
        bed.save()
        task.save()
```

---

## 8. FRONTEND STATE MANAGEMENT

### 8.1 AppContext

**File**: `/health/nursing_react/src/context/appContext.js`

```javascript
const AppContext = createContext([{}, () => {}])
export default AppContext;
```

Very minimal - just a tuple of [state, setState].

### 8.2 AppState Structure

**File**: `/health/nursing_react/src/HealthApp.js` (lines 14-26)

```javascript
const [appState, setAppState] = useContext(AppContext);
const [localAppState, setLocalAppState] = useState(null);

const handleApp = (msg) => {
    if (msg) {
        setAppState(msg);
        setLocalAppState(msg);
    }
};
```

**appState Shape** (from app_load.py):
```javascript
{
    beds: [
        {
            id, id_bed, active, bed_state, occupied_time,
            planed_vacate, action_done_by, patient: {...}
        }
    ],
    patients: [{...}],
    tasks: [{
        id, bed_id, repeat, repeat_id, bed, patient,
        task, programed_time, done_time, active, state,
        programed_by, task_done_by, action_done_by
    }],
    calls: [{
        id, bed_id, bed, patient, call_time, response_time,
        response, state, action_done_by
    }]
}
```

### 8.3 State Updates

**Where appState is updated**:
1. Initial load in HealthApp (fetchLoad)
2. WebSocket messages from appManager (line 47: `appManager({ handleApp })`)
3. After task operations in TasksList (line 27-30)
4. After call operations in CallsList (line 42-50)

---

## 9. CRITICAL ISSUES FOUND

### Issue #1: API/Modular Views Mismatch

The backend has two parallel implementations:
- **Modern API** (`/api/tasks`, `/api/calls`) - in `api.py`
- **Old Modular Views** (`/nursing/edit_task`, `/nursing/new_task`) - in `modular_views/`

The frontend uses BOTH:
- API calls in `NewTaskModal.js` line 80: `authFetch('/tasks', { method: 'POST' })`
- Old endpoints in `EditTaskModal.js` line 61: `fetch('http://localhost:8000/nursing/edit_task')`
- Old endpoints in `CallsList.js` line 81: `fetch('http://localhost:8000/nursing/answered_call')`

**Result**: Task repeat logic never executes via API!

### Issue #2: Task Repeat Not Sent to Backend

**Frontend** (NewTaskModal.js lines 73-77):
```javascript
const payload = {
    bed_id: bedId,
    task: textAction,
    programed_time: programedDT,
    repeat: repeatIsChecked  // ← Only boolean, missing params!
};
authFetch('/tasks', { method: 'POST', body: JSON.stringify(payload) })
```

Collects repeat_lapse, repeat_lapse_unit, repeat_until but never sends them!

**Backend** (api.py lines 340-352):
```python
def create_task(request, data: TaskInputSchema):
    # TaskInputSchema only has: bed_id, task, programed_time, repeat
    task = Task.objects.create(
        bed=bed,
        task=data.task,
        programed_time=datetime.strptime(...),
        repeat=data.repeat,  # ← Just boolean, can't create multiple tasks
        active=True,
    )
    return task
```

**Impact**: Repeated tasks are never created!

### Issue #3: Missing Task Model Fields

Model has `repeat` and `repeat_id` but missing:
- `repeat_lapse` (int) - "2"
- `repeat_lapse_unit` (str) - "hours"
- `repeat_until` (datetime) - when to stop repeating

### Issue #4: WebSocket URL Hardcoded

**Old files** (`calls-socket.js`, `tasks-socket.js`):
```javascript
export const callsManager = ({handleCall}) => {
    const call = new WebSocket('ws://127.0.0.1:8000/ws/callData/');
    // ... hardcoded localhost!
}
```

**New file** (`websocket.js`):
```javascript
const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
// ... uses environment variable
```

Only the new websocket.js is actually used in HealthApp!

### Issue #5: Old Endpoints Not in API

TasksList and CallsList use old endpoints that aren't mapped to Django Ninja API:
- `POST /nursing/edit_task` ← modular_views
- `POST /nursing/answered_call` ← modular_views
- `POST /nursing/close_call` ← modular_views

But NewTaskModal uses NEW API endpoints:
- `POST /api/tasks` ← api.py
- `PUT /api/tasks/{id}` ← api.py

**Impact**: Inconsistent behavior, some operations don't trigger WebSocket updates!

### Issue #6: Bed State Management Inconsistency

Old modular views properly update bed state:
- task_new.py (line 27-31): Sets bed_state = "task" or "call-task"
- task_edit.py (line 29-52): Complex state transitions
- task_delete.py (line 22-29): Removes task state

API endpoints DON'T update bed state at all!

### Issue #7: Call Response Time Set Twice

**call_new.py** (line 25):
```python
new_call.response_time = datetime.now()  # ← Set on creation!
```

Should be set when call is ANSWERED, not created!

**call_close.py** (line 18):
```python
call.response_time = call_time  # ← Set again on close
```

This is overwritten by what's sent in the request.

### Issue #8: No Validation for Past Times

NewTaskModal has validation (lines 59-68) but it's only on frontend:
```javascript
if(Date.parse(programedDT) < Date.parse(timeNow)){
    setAlertMessage('Está intentando programar una tarea para un momento que ya pasó')
    return openAlertShow()
}
```

Backend has no such validation!

### Issue #9: Task State Transitions Broken

API endpoint doesn't handle state transitions:
- "later" ↔ "soon" ↔ "passed"
- Never checks bed state
- Never updates bed state

Modular view (task_edit.py) handles this correctly but isn't used by API!

### Issue #10: Security Issues

**Call MQTT** (api.py line 30):
```python
"key": "this&is$a$key&to?prevent?hacking",
```

This hardcoded key is visible in source code - not secure!

---

## 10. WHAT WORKS vs WHAT'S BROKEN

### ✓ Working:
1. Basic task CRUD via API
2. Basic call CRUD via API
3. Bed management via API
4. Authentication/JWT tokens
5. WebSocket real-time updates (for appboard)
6. Initial app load
7. Task state scheduler (runs independently)

### ✗ Broken:
1. **Task repetition/recurrence** - Never created, parameters not sent
2. **Task repeat deletion** - API doesn't check repeat_id
3. **Task state transitions** - API doesn't update state
4. **Bed state on task operations** - Never updated by API
5. **Call creation via API** - Only MQTT works
6. **Consistent behavior** - Mix of API and modular_views
7. **Audit logging** - Only in modular_views, not in API
8. **EditTaskModal save** - Uses old endpoint, not API
9. **CallsList operations** - Use old endpoints, not API

---

## 11. DATA FLOW DIAGRAMS

### Current (Broken) Task Creation Flow:
```
Frontend NewTaskModal
  ↓
authFetch('/api/tasks', POST, { bed_id, task, programed_time, repeat })
  ↓
api.py: create_task()
  ↓
Creates ONE task with repeat=True (no repeat_lapse/unit/until)
  ↓
No repeated tasks created! ✗
  ↓
fetchLoad() called to refresh state
  ↓
WebSocket: appboard updated
```

### How It Should Work (Old Modular View):
```
Frontend NewTaskModal
  ↓
authFetch('/tasks', POST, { 
    bed_id, task, programedDT, doneDT, 
    repeatIsChecked, repeatLapse, repeatLapseUnit, repeatUntil,
    programer, state
})
  ↓
modular_views/tasks/task_new.py: modular_new_task()
  ↓
Creates initial task
  ↓
IF repeat=True:
  Loop save_repeated_tasks():
    For each interval until repeat_until:
      Create task with repeat_id, state (soon/later)
  ↓
Returns ws_load()
  ↓
All tasks created ✓
```

---

## 12. RECOMMENDATIONS FOR FIXES

### Priority 1: Complete the API Implementation
1. Add missing fields to Task model
2. Update TaskInputSchema to include repeat parameters
3. Integrate repeat logic into api.py create_task()
4. Update PUT endpoint to handle state transitions
5. Add bed state management to task operations

### Priority 2: Consolidate Endpoints
1. Remove old modular view endpoints
2. Migrate all frontend calls to use /api/* paths
3. Ensure all operations trigger WebSocket updates
4. Add audit logging to API endpoints

### Priority 3: Fix State Management
1. Ensure consistent appState updates
2. Add loading states
3. Add error handling
4. Validate inputs on backend

### Priority 4: Security Fixes
1. Generate random keys instead of hardcoded
2. Use environment variables for secrets
3. Add rate limiting
4. Add CSRF protection

---

## 13. KEY FILE LOCATIONS SUMMARY

| Component | File Path | Status |
|-----------|-----------|--------|
| Task Model | `/health/nursing/models.py:137-166` | Missing fields |
| Task API | `/health/nursing/api.py:339-379` | Incomplete repeat logic |
| Task Modular Create | `/health/nursing/modular_views/tasks/task_new.py` | Has repeat logic (unused) |
| Task Modular Edit | `/health/nursing/modular_views/tasks/task_edit.py` | Has state logic (unused) |
| Call API | `/health/nursing/api.py:382-405` | No create endpoint |
| Call MQTT | `/health/nursing/modular_views/calls/call_mqtt.py` | Only creation method |
| WebSocket Setup | `/health/nursing/consumer.py` | ✓ Working |
| Task Scheduler | `/health/nursing/modular_views/tasks/task_ws.py` | ✓ Working |
| Frontend Context | `/health/nursing_react/src/context/appContext.js` | Basic |
| Frontend API | `/health/nursing_react/src/services/api.js` | ✓ Good structure |
| NewTaskModal | `/health/nursing_react/src/components/tasks-list/task-modal/NewTaskModal.js` | Incomplete payload |
| EditTaskModal | `/health/nursing_react/src/components/tasks-list/task-modal/EditTaskModal.js` | Uses old endpoint |
| TasksList | `/health/nursing_react/src/components/tasks-list/TasksList.js` | ✓ Working |
| CallsList | `/health/nursing_react/src/components/calls-list/CallsList.js` | Uses old endpoints |

