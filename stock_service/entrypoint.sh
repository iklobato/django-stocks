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

# Start the Django application
echo "Starting Stock Service..."
exec gunicorn stock_service.wsgi:application --bind 0.0.0.0:8001 --workers 2 --timeout 120