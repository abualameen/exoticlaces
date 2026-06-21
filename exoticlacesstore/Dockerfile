# Dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DJANGO_SETTINGS_MODULE=exoticlacesstore.settings

WORKDIR /app

# Install system dependencies including MariaDB
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    mariadb-server \
    mariadb-client \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set up MariaDB data directory
RUN mkdir -p /var/run/mysqld && chown mysql:mysql /var/run/mysqld



COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY start.sh .
RUN chmod +x start.sh

RUN mkdir -p /app/staticfiles /app/media
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["/app/start.sh"]