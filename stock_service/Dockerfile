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
COPY ./stock_service/entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Copy project
COPY ./stock_service/ /app/

# Expose port
EXPOSE 8001

# Add Docker health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8001/health/ || exit 1

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]