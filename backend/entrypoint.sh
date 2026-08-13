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

if [ -n "$ADMIN_USERNAME" ] && [ -n "$ADMIN_PASSWORD" ]; then
    echo "Ensuring admin user exists..."
    python manage.py shell <<PYEOF
import os
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ.get('ADMIN_USERNAME', 'admin')
password = os.environ.get('ADMIN_PASSWORD', 'admin123456')
email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, password=password, email=email)
    print(f"  -> Created superuser: {username}")
else:
    print(f"  -> Superuser {username} already exists")
PYEOF
fi

if [ "$DJANGO_ENV" = "production" ]; then
    echo "Running in production mode..."
    exec "$@"
else
    echo "Starting development server..."
    exec python manage.py runserver 0.0.0.0:8000
fi
