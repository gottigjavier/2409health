#!/bin/bash

# Con cambios en nursimg_react
cd health/nursing_react/

# "bun run build" es preferible a "npm run build" si se tiene instalado
npm run build
cd ..
python3 manage.py collectstatic --clear --no-input
cd ..
docker-compose up --build
