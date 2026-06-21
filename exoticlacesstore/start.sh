#!/bin/bash

# start.sh
set -e

echo "=========================================="
echo "Starting Exotic Laces Store..."
echo "=========================================="

# Start MySQL
echo "Starting MySQL..."
service mysql start

# Wait for MySQL
echo "Waiting for MySQL to be ready..."
for i in {1..30}; do
    if mysqladmin ping -h localhost --silent 2>/dev/null; then
        echo "MySQL is ready!"
        break
    fi
    echo "Waiting for MySQL... ($i/30)"
    sleep 2
done

echo "Setting up database..."

# Create database and user using root with no password (MySQL default in container)
mysql -u root <<EOF
CREATE DATABASE IF NOT EXISTS exoticlaces_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'exoticlaces_user'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON exoticlaces_db.* TO 'exoticlaces_user'@'localhost';
FLUSH PRIVILEGES;
EOF

# Verify database setup
if mysql -u root -e "USE exoticlaces_db;" 2>/dev/null; then
    echo "✓ Database setup successful!"
else
    echo "⚠️ Database setup failed, but continuing..."
fi

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Load data if datadump.json exists
if [ -f "/app/datadump.json" ]; then
    echo "Loading data from datadump.json..."
    python manage.py loaddata datadump.json
else
    echo "No datadump.json found. Skipping data load."
fi

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