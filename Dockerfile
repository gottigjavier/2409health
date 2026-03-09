FROM python:3.12-slim as python

ENV PYTHONDONTWRITEBYTECODE 1

ENV PYTHONUNBUFFERED 1

# Install Node.js 20.x
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /health

COPY health /health

# Install Python dependencies
RUN python -m pip install -r requirements.txt

# Build React frontend using npm (cached from previous runs)
WORKDIR /health/nursing_react
RUN npm ci --prefer-offline || npm install

# Build React app
RUN npm run build

WORKDIR /health

# Collect static files
RUN python manage.py collectstatic --clear --no-input

RUN ["chmod", "+x", "/health/entrypoint.sh"]

CMD ./entrypoint.sh
