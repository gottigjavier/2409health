# AGENTS.md - 2409health Project

## Project Overview
- **Project**: 2409health - Health monitoring application
- **Tech Stack**: Django, Django Ninja (API), React, Channels (WebSockets), MQTT, Docker

## Architecture

### Backend (Django + Django Ninja API)
- **API REST** con Django Ninja en `/api/`
- **Autenticación** JWT con django-ninja-jwt
- **WebSockets** con Channels para tiempo real
- **MQTT** para comunicación con dispositivos IoT

### Frontend (React)
- Consume la **API REST** en `/api/`
- Usa **WebSockets** para actualizaciones en tiempo real
- Autenticación con **JWT tokens** (access + refresh)

## API Endpoints

### Autenticación
- `POST /api/auth/login` - Iniciar sesión (retorna access + refresh tokens)
- `POST /api/auth/register` - Registrar usuario
- `POST /api/auth/logout` - Cerrar sesión
- `POST /api/auth/refresh` - Refrescar token

### Recursos
- `GET /api/beds` - Listar camas
- `GET /api/beds/{id}` - Ver cama específica
- `POST /api/beds` - Crear cama
- `PUT /api/beds/{id}` - Actualizar cama
- `POST /api/beds/vacate` - Vacar cama
- `GET /api/tasks` - Listar tareas
- `POST /api/tasks` - Crear tarea
- `PUT /api/tasks/{id}` - Actualizar tarea
- `POST /api/tasks/{id}/complete` - Completar tarea
- `DELETE /api/tasks/{id}` - Eliminar tarea
- `GET /api/calls` - Listar llamadas
- `POST /api/calls/{id}/answer` - Atender llamada
- `POST /api/calls/{id}/close` - Cerrar llamada
- `GET /api/rooms` - Obtener habitaciones
- `GET /api/app/load` - Carga inicial de la app

## Directory Structure
```
health/
├── healthproject/      # Django project settings
├── nursing/            # Django app - core functionality
│   ├── api.py         # Django Ninja API endpoints
│   ├── consumer.py    # WebSocket consumers
│   └── modular_views/ # Vistas modulares
├── nursing_react/     # React frontend
│   └── src/
│       ├── services/
│       │   ├── api.js      # API client con JWT
│       │   └── websocket.js # WebSocket client
│       ├── components/
│       │   └── Login.js    # Componente de login
│       └── App.js          # Routing principal
├── mosquitto/         # MQTT configuration
├── manage.py          # Django management script
└── requirements.txt   # Python dependencies
```

## Key Commands
- `python manage.py runserver` - Run Django dev server
- `docker-compose up` - Start all services
- `npm run dev` - Run React dev server (in nursing_react/)

## Environment Variables (.env)
```
DB=db
DB_NAME=healthdb
DB_USER=postgres
DB_PASSWORD=postgres
SECRET_KEY=mydevsecretkey123
ALLOWED_HOSTS=localhost,127.0.0.1
```

## Version Control
- Using Jujutsu (jj) for version control
- Colocated with Git (`.jj/` + `.git/`)
