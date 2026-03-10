FROM python:3.12-slim as python

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install Node.js 20.x and Bun
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && curl -fsSL https://bun.sh/install | bash - \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# FIX: Add Bun to PATH after installation
ENV PATH="/root/.bun/bin:$PATH"

WORKDIR /health

COPY health /health

# FIX: Upgrade pip before installing dependencies
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Build React frontend using Bun
WORKDIR /health/nursing_react

# FIX: bun ci is not valid; use --frozen-lockfile to replicate CI behavior
RUN bun install

# Build React app
RUN bun run build

WORKDIR /health

# Collect static files
# RUN python manage.py collectstatic --clear --no-input

RUN ["chmod", "+x", "/health/entrypoint.sh"]

CMD ["./entrypoint.sh"]