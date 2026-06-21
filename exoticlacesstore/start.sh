#!/bin/bash

# start.sh
set -e

echo "=========================================="
echo "Starting Exotic Laces Store..."
echo "=========================================="

# Initialize MariaDB data directory if empty
if [ ! -d "/var/lib/mysql/mysql" ]; then
    echo "Initializing MariaDB data directory..."
    mysql_install_db --user=mysql --datadir=/var/lib/mysql
fi

# Start MariaDB
echo "Starting MariaDB..."
service mariadb start

# Wait for MariaDB to be ready
echo "Waiting for MariaDB to be ready..."
for i in {1..30}; do
    if mysqladmin ping -h localhost --silent 2>/dev/null; then
        echo "MariaDB is ready!"
        break
    fi
    echo "Waiting for MariaDB... ($i/30)"
    sleep 2
done

# Check if root password is already set
echo "Setting up database..."

# Try to set root password and create database
mysql -u root <<EOF 2>/dev/null
ALTER USER 'root'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
FLUSH PRIVILEGES;
CREATE DATABASE IF NOT EXISTS exoticlaces_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'exoticlaces_user'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON exoticlaces_db.* TO 'exoticlaces_user'@'localhost';
FLUSH PRIVILEGES;
EOF

# If the above failed, try with password
if [ $? -ne 0 ]; then
    echo "Trying with root password..."
    mysql -u root -p"${DB_PASSWORD}" <<EOF 2>/dev/null
CREATE DATABASE IF NOT EXISTS exoticlaces_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'exoticlaces_user'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON exoticlaces_db.* TO 'exoticlaces_user'@'localhost';
FLUSH PRIVILEGES;
EOF
fi

# Verify database setup
echo "Verifying database setup..."
if mysql -u root -p"${DB_PASSWORD}" -e "USE exoticlaces_db;" 2>/dev/null; then
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