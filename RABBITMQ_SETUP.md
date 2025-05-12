# RabbitMQ Architecture and Setup

This document explains the RabbitMQ architecture in the Django Challenge project and how to set it up.

## Overview

The project uses a clean producer-consumer pattern with RabbitMQ as the message broker:

1. **API Service (Producer)**: Produces messages with stock query requests
2. **Stock Service (Consumer)**: Consumes messages and processes stock queries
3. **RabbitMQ Broker**: Facilitates message passing between services

## Architecture

The communication flow works as follows:

1. API Service (Producer) receives a stock query request from a user
2. API Service creates a message with the stock code and publishes it to RabbitMQ
3. Stock Service (Consumer) consumes the message from RabbitMQ
4. Stock Service fetches the data from stooq.com API
5. Stock Service sends the response back to API Service through RabbitMQ
6. API Service receives the response, saves it to the database, and returns it to the user

This approach provides several benefits:
- Decoupled services that can evolve independently
- Asynchronous communication for better scalability
- Built-in message queuing and retry mechanisms
- Improved fault tolerance and resilience

## Running the Services

The easiest way to run all services is with Docker Compose:

```bash
docker-compose up -d
```

This will start all three services:
- RabbitMQ Broker on ports 5672 (AMQP) and 15672 (Management UI)
- Stock Service (Consumer) on port 8001
- API Service (Producer) on port 8000

## RabbitMQ Implementation

### API Service (Producer)

The API Service acts as a RabbitMQ producer:

- Uses the RPC (Remote Procedure Call) pattern for request-response communication
- Creates a unique correlation ID for each request
- Publishes messages to a durable queue
- Listens for responses on a temporary callback queue
- Includes a fallback HTTP mechanism if RabbitMQ communication fails

### Stock Service (Consumer)

The Stock Service acts as a RabbitMQ consumer:

- Listens for messages on the stock queue
- Processes stock requests by fetching data from the external API
- Sends responses back to the API service using the reply_to queue
- Uses the correlation ID to match responses with requests
- Automatically reconnects if the connection to RabbitMQ is lost

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