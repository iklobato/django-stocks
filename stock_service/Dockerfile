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

# Copy project
COPY ./stock_service/ /app/

# Copy entrypoint script
COPY ./stock_service/entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8001

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]