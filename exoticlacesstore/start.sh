#!/bin/bash

# start.sh
set -e

echo "=========================================="
echo "Starting Exotic Laces Store..."
echo "=========================================="

# Start MariaDB
echo "Starting MariaDB..."
service mariadb start

# Wait for MariaDB
echo "Waiting for MariaDB to be ready..."
sleep 10

# Create the database and user using a different method
echo "Setting up database..."

# Use a temporary file to run SQL commands
cat > /tmp/setup.sql <<EOF
CREATE DATABASE IF NOT EXISTS exoticlaces_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'exoticlaces_user'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON exoticlaces_db.* TO 'exoticlaces_user'@'localhost';
FLUSH PRIVILEGES;
EOF

# Run the SQL file with mysql -u root
mysql -u root < /tmp/setup.sql 2>/dev/null || echo "Database setup warning..."

# Check if we can connect
if mysql -u root -e "SELECT 1" > /dev/null 2>&1; then
    echo "Database setup successful!"
else
    echo "WARNING: Database setup failed, but continuing..."
fi

# Continue with migrations
echo "Running database migrations..."
python manage.py migrate --noinput

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