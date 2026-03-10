#!/bin/bash

echo "Waiting for postgres..."
until python -c "
import socket, sys
try:
    s = socket.socket()
    s.settimeout(1)
    s.connect(('localhost', 5432))
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" ; do
  echo "Postgres not ready, retrying..."
  sleep 2
done
echo "Postgres ready"

echo "Waiting for redis..."
until python -c "
import socket, sys
try:
    s = socket.socket()
    s.settimeout(1)
    s.connect(('localhost', 6379))
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" ; do
  echo "Redis not ready, retrying..."
  sleep 2
done
echo "Redis ready"

# Correr collectstatic en runtime, después de que el volumen esté montado
python manage.py collectstatic --clear --no-input

python manage.py wait_for_db
python manage.py migrate auth
python manage.py migrate --run-syncdb
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').delete(); User.objects.create_superuser('admin', 'admin@project.com', 'password')" | python manage.py shell
daphne -b 0.0.0.0 -p 8000 healthproject.asgi:application
