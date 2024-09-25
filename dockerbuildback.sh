#!/bin/bash

# Sin cambios en nursing_react

cd health/
python manage.py collectstatic --clear --no-input
cd ..
docker-compose up --build