#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Wait for RabbitMQ to be ready
echo "Waiting for RabbitMQ..."
until nc -z ${RABBITMQ_HOST} ${RABBITMQ_PORT}; do
  echo "RabbitMQ is unavailable - sleeping"
  sleep 2
done
echo "RabbitMQ is up - continuing..."

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Create superuser if not exists
echo "Creating superuser if not exists..."
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(username='${ADMIN_USERNAME}').exists() or User.objects.create_superuser('${ADMIN_USERNAME}', '${ADMIN_EMAIL}', '${ADMIN_PASSWORD}')"

# Start the Django application
echo "Starting API Service..."
exec gunicorn api_service.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120