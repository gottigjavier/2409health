#!/bin/bash

systemctl start postgresql
redis-server &
cd health/nursing_react/
react-scripts build
cd ..
python manage.py collectstatic --clear --no-input
python manage.py runserver
pkill redis-server
systemctl stop postgresql
