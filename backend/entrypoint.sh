#!/bin/bash
set -e

echo "========================================"
echo "  WaterWeb Backend Startup Script"
echo "========================================"

python manage.py check --deploy 2>/dev/null || true

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput 2>/dev/null || true

if [ "$DJANGO_ENV" = "production" ]; then
    echo "Running in production mode..."
    exec "$@"
else
    echo "Starting development server..."
    exec python manage.py runserver 0.0.0.0:8000
fi
