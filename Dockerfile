# syntax=docker/dockerfile:1
FROM python:3.12-slim

# OCI Labels (ADR-022 konform)
ARG APP_NAME=writing-hub
LABEL org.opencontainers.image.source="https://github.com/achimdehnert/${APP_NAME}"
LABEL org.opencontainers.image.description="Writing Hub — Autorenplattform (ADR-083)"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    git \
    make \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

RUN chmod +x /app/docker/entrypoint.web.sh \
    && groupadd -g 1000 app && useradd -u 1000 -g app -m app \
    && chown -R app:app /app

USER app:1000
EXPOSE 8000

# HEALTHCHECK removed — ADR-022: Healthchecks belong in docker-compose.prod.yml per service,
# not in Dockerfile (would apply to all containers including worker/beat which have no web server)

CMD ["/app/docker/entrypoint.web.sh"]
