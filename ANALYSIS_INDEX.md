# Health App Codebase Analysis - Complete Index

## Overview

This directory contains a comprehensive analysis of the 2409health application codebase. The analysis was performed to understand the backend API endpoints, task/call logic, frontend state management, and identify architectural issues.

## Generated Analysis Documents

### 1. **CODEBASE_ANALYSIS.md** (684 lines)
**Location**: `/CODEBASE_ANALYSIS.md`

Complete technical analysis covering:
- Backend API endpoints (Tasks, Calls, Beds)
- Task model and serialization
- Task repetition/recurrence functionality
- Task editing endpoints and logic
- Task completion flow
- Call endpoints and MQTT integration
- WebSocket & real-time updates
- Frontend state management
- 10 Critical issues found
- What works vs what's broken
- Data flow diagrams
- Recommendations for fixes
- Key file locations summary

**Best for**: Getting the full technical picture and understanding all issues

---

### 2. **ANALYSIS_SUMMARY.txt** (210 lines)
**Location**: `/ANALYSIS_SUMMARY.txt`

Visual summary with ASCII diagrams covering:
- Backend API endpoints (quick reference)
- 5 Critical architectural problems
- State management overview
- What works (8 items)
- What's broken (10 items)
- Quick fix checklist (16 items)
- File locations summary

**Best for**: Quick overview and prioritizing fixes

---

### 3. **CODE_SNIPPETS_REFERENCE.md** (629 lines)
**Location**: `/CODE_SNIPPETS_REFERENCE.md`

Detailed code snippets showing:
1. Broken task repeat flow (3 implementations compared)
2. Missing task model fields
3. Bed state management issues
4. Inconsistent frontend endpoints
5. WebSocket update triggers
6. Task state scheduler
7. Frontend state structure
8. Call creation (MQTT only)
9. Duplicate WebSocket files
10. Security issue (hardcoded MQTT key)
11. Key takeaways

**Best for**: Understanding specific code problems and learning how to fix them

---

## Key Findings Summary

### Critical Issues (Must Fix)

1. **Task Repeat Completely Broken**
   - Frontend collects repeat_lapse, repeat_lapse_unit, repeat_until but doesn't send them
   - Backend API doesn't accept these parameters
   - Task model missing these fields
   - Multiple tasks never created for repeated tasks
   - **Impact**: Repeat functionality doesn't work at all

2. **Dual Code Paths**
   - Modern API endpoints in `api.py`
   - Legacy implementation in `modular_views/`
   - Frontend uses BOTH inconsistently
   - **Impact**: Some features work only with legacy code, others with API

3. **Bed State Not Managed by API**
   - Legacy code updates bed state when tasks created/edited/deleted
   - API endpoints ignore bed state completely
   - **Impact**: Bed colors/states don't update correctly

4. **WebSocket Updates Incomplete**
   - Only legacy endpoints trigger WebSocket broadcasts
   - API endpoints don't broadcast updates
   - **Impact**: Some operations don't update frontend in real-time

5. **Missing Call Creation API**
   - Only MQTT can create calls
   - No `/api/calls` POST endpoint
   - **Impact**: Can't create calls via API

---

## File Organization

```
health-app/
├── Backend (Django)
│   ├── nursing/
│   │   ├── models.py                    ← Task model (missing fields)
│   │   ├── api.py                       ← Django Ninja endpoints (incomplete)
│   │   ├── consumer.py                  ← WebSocket consumers
│   │   └── modular_views/
│   │       ├── tasks/
│   │       │   ├── task_new.py         ← Repeat logic (unused!)
│   │       │   ├── task_edit.py        ← State logic (unused!)
│   │       │   ├── task_delete.py      ← Repeat deletion (unused!)
│   │       │   └── task_ws.py          ← Scheduler (works!)
│   │       ├── calls/
│   │       │   ├── call_new.py         ← MQTT only
│   │       │   ├── call_mqtt.py        ← MQTT handler
│   │       │   ├── call_answered.py    ← Legacy endpoint
│   │       │   └── call_close.py       ← Legacy endpoint
│   │       └── app/
│   │           ├── app_load.py         ← Initial load
│   │           └── app_ws_update.py    ← WebSocket broadcast
│   │
│   └── healthproject/
│       ├── settings.py
│       └── asgi.py                     ← Channels config
│
├── Frontend (React)
│   ├── nursing_react/src/
│   │   ├── context/
│   │   │   └── appContext.js           ← Global state
│   │   ├── services/
│   │   │   ├── api.js                  ← Good structure
│   │   │   ├── websocket.js            ← Used
│   │   │   ├── app-socket.js           ← Unused (hardcoded)
│   │   │   ├── calls-socket.js         ← Unused (hardcoded)
│   │   │   └── tasks-socket.js         ← Unused (hardcoded)
│   │   ├── components/
│   │   │   ├── tasks-list/
│   │   │   │   ├── TasksList.js        ← Works
│   │   │   │   └── task-modal/
│   │   │   │       ├── NewTaskModal.js ← Broken (incomplete payload)
│   │   │   │       └── EditTaskModal.js← Broken (uses legacy endpoint)
│   │   │   └── calls-list/
│   │   │       ├── CallsList.js        ← Uses legacy endpoints
│   │   │       └── call-modal/
│   │   │           └── CallModal.js
│   │   └── App.js
│   │       └── HealthApp.js            ← Main component
│
└── Analysis Files (This Analysis)
    ├── CODEBASE_ANALYSIS.md            ← Full technical analysis
    ├── ANALYSIS_SUMMARY.txt            ← Visual summary
    ├── CODE_SNIPPETS_REFERENCE.md      ← Code examples
    └── ANALYSIS_INDEX.md               ← This file
```

---

## How to Use This Analysis

### If you want to understand ONE specific issue:
1. Start with **ANALYSIS_SUMMARY.txt** - find the issue
2. Go to **CODE_SNIPPETS_REFERENCE.md** - see the code
3. Reference **CODEBASE_ANALYSIS.md** - detailed explanation

### If you want to understand the whole picture:
1. Start with **ANALYSIS_SUMMARY.txt** - get orientation
2. Read **CODEBASE_ANALYSIS.md** - full context
3. Use **CODE_SNIPPETS_REFERENCE.md** - for implementation details

### If you want to fix something:
1. Find the issue in **ANALYSIS_SUMMARY.txt** - see what's broken
2. Look at the code section in **CODE_SNIPPETS_REFERENCE.md** - understand it
3. Reference line numbers in **CODEBASE_ANALYSIS.md** - full explanation
4. Check the file paths for exact locations

---

## Priority Fixes (From ANALYSIS_SUMMARY.txt)

### Priority 1: CRITICAL
- [ ] Add repeat_lapse, repeat_lapse_unit, repeat_until to Task model
- [ ] Update TaskInputSchema to accept repeat parameters
- [ ] Move repeat logic from modular_views to api.py
- [ ] Update frontend NewTaskModal to send repeat parameters

### Priority 2: HIGH
- [ ] Add bed state management to all API task endpoints
- [ ] Update PUT /api/tasks/{id} to handle state transitions
- [ ] Update DELETE /api/tasks/{id} to check repeat_id
- [ ] Create /api/calls POST endpoint

### Priority 3: MEDIUM
- [ ] Migrate EditTaskModal to use API endpoint
- [ ] Migrate CallsList to use API endpoints
- [ ] Add WebSocket broadcast after all operations
- [ ] Add audit logging to API endpoints

### Priority 4: NICE-TO-HAVE
- [ ] Add input validation on backend
- [ ] Fix hardcoded MQTT key
- [ ] Add error handling on frontend
- [ ] Use env variables for all configs

---

## Technical Stack

### Backend
- **Framework**: Django
- **API**: Django Ninja (REST API)
- **Real-time**: Django Channels (WebSockets)
- **Database**: PostgreSQL
- **IoT**: MQTT (Mosquitto)
- **Background Jobs**: APScheduler

### Frontend
- **Framework**: React
- **State**: React Context API
- **HTTP**: fetch API
- **WebSocket**: Native WebSocket API
- **Build**: npm/webpack

### DevOps
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **VCS**: Git + Jujutsu (jj)

---

## Database Models

### Task
```
- id (PK)
- bed_id (FK)
- repeat (bool)
- repeat_id (str) - groups repeated tasks
- task (text)
- programed_time (datetime)
- done_time (datetime)
- active (bool)
- state (str) - later, soon, passed
- programed_by (str)
- task_done_by (str)
- action_done_by (str)
- MISSING: repeat_lapse, repeat_lapse_unit, repeat_until
```

### Call
```
- id (PK)
- bed_id (FK)
- response (text)
- call_time (datetime)
- response_time (datetime)
- state (str) - active, answered, closed
- action_done_by (str)
```

### Bed
```
- id (PK)
- bed_patient_id (FK)
- id_bed (str) - "room,bed" format
- active (bool)
- bed_state (str) - free, occupied, call, task, call-task
- occupied_time (datetime)
- planed_vacate (datetime)
- vacate_time (datetime)
- action_done_by (str)
```

---

## API Endpoints Status

### Tasks
- ✓ GET /api/tasks - List
- ✓ POST /api/tasks - Create (incomplete)
- ✓ PUT /api/tasks/{id} - Update (incomplete)
- ✓ POST /api/tasks/{id}/complete - Mark done
- ✓ DELETE /api/tasks/{id} - Delete

### Calls
- ✓ GET /api/calls - List
- ✗ POST /api/calls - Create (MISSING)
- ✓ POST /api/calls/{id}/answer - Answer
- ✓ POST /api/calls/{id}/close - Close

### Beds
- ✓ GET /api/beds - List
- ✓ POST /api/beds - Create
- ✓ PUT /api/beds/{id} - Update
- ✓ POST /api/beds/vacate - Vacate
- ✓ GET /api/beds/{id} - Get one

### App
- ✓ GET /api/app/load - Initial load
- ✓ WS /ws/appData/ - Real-time updates (via consumer.py)

---

## Frontend State Flow

```
Initial Load
    ↓
fetchLoad() → /api/app/load
    ↓
setAppState({beds, tasks, calls, patients})
    ↓
HealthApp renders with appState
    ↓
Components subscribe via appManager() → WebSocket
    ↓
Backend sends updates → appboard group
    ↓
Consumer handles deprocessing event
    ↓
Frontend setState(msg) updates appState
    ↓
Components re-render with new data
```

---

## References in Source

All code line numbers reference the files as they exist in:
- `/health/nursing/` - Backend Django app
- `/health/nursing_react/src/` - Frontend React app

Example: `/health/nursing/api.py:339-352` means:
- File: `/health/nursing/api.py`
- Lines: 339 to 352

---

## Document Maintenance

- **Created**: March 7, 2025
- **Scope**: Health monitoring application (2409health)
- **Analyzed Files**: 24 Python files + 10 JavaScript files
- **Total Analysis**: 1,523 lines across 3 documents
- **Issues Found**: 10 critical, multiple breaking changes needed

---

## Quick Navigation

| Need | Document | Section |
|------|----------|---------|
| Quick overview | ANALYSIS_SUMMARY.txt | Top section |
| Full details | CODEBASE_ANALYSIS.md | Any section |
| Code examples | CODE_SNIPPETS_REFERENCE.md | Relevant number |
| Priorities | ANALYSIS_SUMMARY.txt | Fix checklist |
| File list | CODEBASE_ANALYSIS.md | Section 13 |
| State structure | CODE_SNIPPETS_REFERENCE.md | Section 7 |

---

**End of Analysis Index**

For detailed information, refer to the three analysis documents in this directory.
