#!/bin/bash

set -e

echo "=========================================="
echo "Starting Exotic Laces Store..."
echo "=========================================="

# Initialize MariaDB if this is the first run
if [ ! -d "/var/lib/mysql/mysql" ]; then
    echo "📦 Initializing MariaDB data directory..."
    mysql_install_db --user=mysql --datadir=/var/lib/mysql
fi

# Start MariaDB
echo "🔧 Starting MariaDB..."
service mariadb start

# Wait for MariaDB to be ready
echo "⏳ Waiting for MariaDB to be ready..."
for i in {1..30}; do
    if mysqladmin ping -h localhost --silent 2>/dev/null; then
        echo "✅ MariaDB is ready!"
        break
    fi
    echo "⏳ Waiting for MariaDB... ($i/30)"
    sleep 2
done

# Create database and user
echo "📝 Setting up database..."
mysql -u root <<EOF
CREATE DATABASE IF NOT EXISTS exoticlaces_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'exoticlaces_user'@'localhost' IDENTIFIED BY '${DB_PASSWORD:-April_1985@}';
GRANT ALL PRIVILEGES ON exoticlaces_db.* TO 'exoticlaces_user'@'localhost';
FLUSH PRIVILEGES;
EOF

echo "✅ Database setup complete!"

# Run migrations
echo "🔄 Running database migrations..."
python manage.py migrate --noinput

# Load data if available
if [ -f "/app/datadump.json" ]; then
    echo "📂 Loading data from datadump.json..."
    python manage.py loaddata datadump.json
fi

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser
echo "👤 Creating superuser if needed..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@exoticlaces.com', '${DJANGO_SUPERUSER_PASSWORD:-admin123}')
    print("✅ Superuser created.")
else:
    print("✅ Superuser already exists.")
EOF

# Start Gunicorn
echo "🚀 Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 \
    --workers 2 \
    --threads 2 \
    --worker-tmp-dir /dev/shm \
    --timeout 120 \
    --log-level info \
    exoticlacesstore.wsgi:application