Tipos y roles de usuario.
Hay cuatro typos, todos BooleanField: is_superuser, is_leader, is_staff, is_active.
Hay tres roles, todos CharField: office, doctor, nurse.

is_superuser, staff y active son manejados internamente por django y no por models.py
is_leader y role es manejado por models.py

Si el backend responde "True" a las consultas es lo que el usuario puede hacer:

is_superuser con cualquier role: acceso a todo. En este momento no puede registrar nuevos usuarios en /register. Cambiar para que pueda hacerlo.
role doctor y is_leader: acceso a la app, puede registrar nuevos usuarios
