# Dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DJANGO_SETTINGS_MODULE=exoticlacesstore.settings

WORKDIR /app

# Copy requirements from the correct location
COPY exoticlacesstore/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY exoticlacesstore/ .

# Copy start.sh
COPY exoticlacesstore/start.sh .
RUN chmod +x start.sh

RUN mkdir -p /app/staticfiles /app/media
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["/app/start.sh"]