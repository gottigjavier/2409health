**Instalar DRF Spectacular en Arch Linux e integrarlo a un proyecto Django API es igual que en cualquier otro sistema Linux**, ya que se trata de un paquete Python. Arch Linux no afecta el proceso de instalación. 

### **1. Instalación**
Ejecuta en tu entorno virtual (recomendado):
```bash
pip install drf-spectacular
```

> ⚠️ **Nota**: Asegúrate de tener `python`, `pip` y `django` ya instalados (puedes instalarlos con `pacman` si es necesario: `sudo pacman -S python python-pip python-django`). 

### **2. Configuración en Django**
Agrega `drf_spectacular` a `INSTALLED_APPS` en `settings.py`:
```python
INSTALLED_APPS = [
    # ...
    'drf_spectacular',
]
```

Configura DRF para usar `drf-spectacular` como clase de esquema:
```python
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
```

(Opcional) Añade metadatos a la API:
```python
SPECTACULAR_SETTINGS = {
    'TITLE': 'Tu API',
    'DESCRIPTION': 'Documentación automática de tu API Django',
    'VERSION': '1.0.0',
}
```

### **3. Configurar URLs**
En tu archivo `urls.py` principal:
```python
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # ... tus otras rutas
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
```

### **4. Acceder a la documentación**
Inicia el servidor:
```bash
python manage.py runserver
```

Abre en tu navegador:
- **Swagger UI**: `http://127.0.0.1:8000/api/docs/`



