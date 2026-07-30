#!/bin/bash

# start.sh
set -e

echo "=========================================="
echo "Starting Exotic Laces Store..."
echo "=========================================="

# ⚠️ SKIP MIGRATIONS - Database is already set up
echo "Skipping migrations (database already configured)..."

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser
echo "Creating superuser if needed..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@exoticlaces.com', '${DJANGO_SUPERUSER_PASSWORD:-admin123}')
    print("Superuser created.")
else:
    print("Superuser already exists.")
EOF

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 \
    --workers 2 \
    --threads 2 \
    --worker-tmp-dir /dev/shm \
    --timeout 120 \
    --log-level info \
    exoticlacesstore.wsgi:application