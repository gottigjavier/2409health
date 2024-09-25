FROM python:3.12-slim as python

ENV PYTHONDONTWRITEBYTECODE 1

ENV PYTHONUNBUFFERED 1

WORKDIR /health

COPY /health /health

RUN python -m pip install -r requirements.txt

RUN ["chmod", "+x", "/health/entrypoint.sh"]

CMD ./entrypoint.sh