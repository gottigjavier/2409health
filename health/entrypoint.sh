#!/bin/bash

python3 manage.py wait_for_db
python3 manage.py migrate auth
python3 manage.py migrate --run-syncdb
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').delete(); User.objects.create_superuser('admin', 'admin@project.com', 'password')" | python manage.py shell
python3 subscribe.py
python3 manage.py collectstatic --clear --no-input
daphne -b 0.0.0.0 -p 8000 healthproject.asgi:application