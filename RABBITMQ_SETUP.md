# RabbitMQ Architecture and Setup

This document explains the RabbitMQ architecture in the Django Challenge project and how to set it up.

## Overview

The project uses a true microservices architecture with four separate services:

1. **API Service**: Handles API requests from users, authenticates them, and manages the database
2. **Stock Service**: Fetches stock data from the external stooq.com API
3. **RabbitMQ Service**: Handles message queue communication between services
4. **RabbitMQ Broker**: The actual RabbitMQ message broker

## Architecture

The communication flow works as follows:

1. API Service receives a stock query request from a user
2. API Service sends a message to the RabbitMQ Service with the stock code
3. RabbitMQ Service receives the message and forwards it to the Stock Service
4. Stock Service fetches the data from stooq.com API
5. Stock Service sends the response back to the RabbitMQ Service
6. RabbitMQ Service forwards the response back to the API Service
7. API Service saves the data and returns it to the user

This approach provides several benefits:
- Better separation of concerns
- Services can be scaled independently
- Improved fault tolerance and resilience
- Each service has a single responsibility

## Running the Services

The easiest way to run all services is with Docker Compose:

```bash
docker-compose up -d
```

This will start all four services:
- RabbitMQ Broker on ports 5672 (AMQP) and 15672 (Management UI)
- RabbitMQ Service on port 8080
- Stock Service on port 8001
- API Service on port 8000

## RabbitMQ Service

The RabbitMQ Service is a standalone microservice written in Python using Flask:

- It connects to the RabbitMQ Broker and listens for messages
- It forwards requests to the Stock Service via HTTP
- It sends responses back to the API Service via RabbitMQ
- It uses the Remote Procedure Call (RPC) pattern with correlation IDs
- It provides fault tolerance and error handling

## Configuration

The RabbitMQ architecture is configured through environment variables in the `.env` file:

```
# RabbitMQ settings
RABBITMQ_DEFAULT_USER=guest
RABBITMQ_DEFAULT_PASS=guest
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_STOCK_QUEUE=stock_queue
RABBITMQ_TIMEOUT=10

# Services URLs
STOCK_SERVICE_URL=http://stock-service:8001
RABBITMQ_SERVICE_URL=http://rabbitmq-service:8080
```

## RabbitMQ Management UI

You can access the RabbitMQ Management UI at http://localhost:15672:

- Username: guest (or as configured in .env)
- Password: guest (or as configured in .env)

This UI allows you to monitor queues, connections, and messages in real-time.

## Health Checks

All services provide health check endpoints:

- API Service: http://localhost:8000/health/
- Stock Service: http://localhost:8001/health/
- RabbitMQ Service: http://localhost:8080/health

These endpoints are used by Docker for health checks but can also be used for monitoring.

## Testing the Integration

To test the RabbitMQ integration manually, you can:

1. Start all services with `docker-compose up -d`
2. Use the API Service to query a stock:
   ```bash
   curl -X GET -H "Authorization: Token <your_token>" http://localhost:8000/stock/?symbol=aapl.us
   ```

Docker Compose is configured to ensure services start in the correct order, with proper health checks and dependencies.