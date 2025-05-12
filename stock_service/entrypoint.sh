#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Set maximum number of retries
MAX_RETRIES=30
RETRY_COUNT=0

# Wait for RabbitMQ to be ready
echo "Waiting for RabbitMQ..."
until nc -z ${RABBITMQ_HOST} ${RABBITMQ_PORT} || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
  echo "RabbitMQ is unavailable - sleeping (attempt $((RETRY_COUNT+1))/$MAX_RETRIES)"
  RETRY_COUNT=$((RETRY_COUNT+1))
  sleep 2
done

# Check if max retries reached
if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
  echo "Max retries reached. RabbitMQ is still unavailable. Exiting."
  exit 1
fi

echo "RabbitMQ is up - continuing..."

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Start the Django application
echo "Starting Stock Service..."
exec gunicorn stock_service.wsgi:application --bind 0.0.0.0:8001 --workers 2 --timeout 120