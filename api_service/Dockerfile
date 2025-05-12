FROM python:3.8-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install dependencies including netcat and curl for health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint script first and set permissions
COPY ./api_service/entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Copy project
COPY ./api_service/ /app/

# Expose port
EXPOSE 8000

# Use gunicorn directly instead of entrypoint script for simplicity
CMD ["gunicorn", "api_service.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]