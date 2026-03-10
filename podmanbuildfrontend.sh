#!/bin/bash

# Con cambios en nursimg_react
cd health/nursing_react/

# "bun run build" es preferible a "npm run build" si se tiene instalado
bun run build
cd ..
cd ..
podman build -t health-app:latest .