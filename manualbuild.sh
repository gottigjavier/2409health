#!/bin/bash

systemctl start postgresql
redis-server &
cd health/nursing_react/
react-scripts build
cd ..
python3 manage.py collectstatic --clear --no-input
python3 manage.py runserver
pkill redis-server
systemctl stop postgresql