#!/bin/bash
set -e

echo "[writing-hub] Running migrations..."
python manage.py migrate --noinput

echo "[writing-hub] Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "[writing-hub] Seeding Stammdaten + aifw-Konfiguration..."
python manage.py seed_all || echo "[writing-hub] seed_all Warnung (nicht kritisch, weiter)"

echo "[writing-hub] Starting gunicorn on :8000"
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120 \
    --log-level info
