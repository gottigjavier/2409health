#!/bin/bash

# Con cambios en nursimg_react
cd health/

python3 manage.py collectstatic --clear --no-input
cd ..
podman build -t health-app:latest .