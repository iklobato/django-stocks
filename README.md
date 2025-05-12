<div align="center">
    <img src="https://media.licdn.com/dms/image/D4E0BAQETyObSEmZH-A/company-logo_200_200/0/1693956448491/jobsity_llc_logo?e=1723075200&v=beta&t=rGq4fY1cprFyIaSabim0_bgb-QLCbJUk6Es9dXuua1w"/>
</div>

# Python/Django Challenge

## Description
This project is designed to test your knowledge of back-end web technologies, specifically in Python/Django, Rest APIs, and decoupled services (microservices).

## Assignment
The goal of this exercise is to create a simple API using Django and the Django Rest Framework to allow users to query [stock quotes](https://www.investopedia.com/terms/s/stockquote.asp).

The project consists of two separate services:
* A user-facing API that will receive requests from registered users asking for quote information.
* An internal stock service that queries external APIs to retrieve the requested quote information.

For simplicity, both services will share the same dependencies (requirements.txt) and can be run from the same virtualenv, but remember that they are still separate processes.

## Minimum requirements

 - You will need to **record a video explaining the code** you created, the decisions you made, its functionality, and demonstrating the complete operation of the challenge. _Remember to show the execution from scratch, it should not be running beforehand._


### API service
* Use Django's built-in features to create a user and a super user.
* Endpoints in the API service should require authentication (no anonymous requests should be allowed). Each request should be authenticated via Basic Authentication.
* When a user makes a request to get a stock quote (calls the stock endpoint in the api service), if a stock is found, it should be saved in the database associated to the user making the request.
* The response returned by the API service should be like this:

  `GET /stock?q=aapl.us`
  ```
    {
    "name": "APPLE",
    "symbol": "AAPL.US",
    "open": 123.66,
    "high": 123.66,
    "low": 122.49,
    "close": 123
    }
  ```
* A user can get his history of queries made to the api service by hitting the history endpoint. The endpoint should return the list of entries saved in the database, showing the latest entries first:
  
  `GET /history`
  ```
  [
      {"date": "2021-04-01T19:20:30Z", "name": "APPLE", "symbol": "AAPL.US", "open": "123.66", "high": 123.66, "low": 122.49, "close": "123"},
      {"date": "2021-03-25T11:10:55Z", "name": "APPLE", "symbol": "AAPL.US", "open": "121.10", "high": 123.66, "low": 122, "close": "122"},
      ...
  ]
  ```
* A super user (and only super users) can hit the stats endpoint, which will return the top 5 most requested stocks:

  `GET /stats`
  ```
  [
      {"stock": "aapl.us", "times_requested": 5},
      {"stock": "msft.us", "times_requested": 2},
      ...
  ]
  ```
* All endpoint responses should be in JSON format.

### Stock service
* Assume this is an internal service, so requests to endpoints in this service don't need to be authenticated.
* When a stock request is received, this service should query an external API to get the stock information. For this challege, use this API: `​https://stooq.com/q/l/?s={stock_code}&f=sd2t2ohlcvn&h&e=csv​`.
* Note that `{stock_code}` above is a parameter that should be replaced with the requested stock code.
* You can see a list of available stock codes here: https://stooq.com/t/?i=518

## Architecture
![Architecture Diagram](diagram.svg)
1. A user makes a request asking for Apple's current Stock quote: `GET /stock?q=aapl.us`
2. The API service communicates with the stock service through RabbitMQ (or HTTP as fallback) to retrieve the requested stock information
3. The stock service delegates the call to the external API, parses the response, and returns the information back to the API service.
4. The API service saves the response from the stock service in the database.
5. The data is formatted and returned to the user.

## Implemented Bonuses
* **RabbitMQ Integration**: The services now communicate via RabbitMQ using the Remote Procedure Call (RPC) pattern, with HTTP fallback for reliability.
* **Unit Tests**: Tests for the stock service and RabbitMQ integration are included.

## Additional Bonuses (Not Implemented)
* Use JWT instead of basic authentication for endpoints.

## RabbitMQ Integration
The project now includes RabbitMQ integration for communication between services:

* See [RABBITMQ_SETUP.md](RABBITMQ_SETUP.md) for detailed instructions on setting up and using RabbitMQ.
* A Docker Compose file is provided to run RabbitMQ locally.
* The API service uses RabbitMQ to communicate with the stock service, with fallback to HTTP if RabbitMQ fails.

## How to run the project

This project consists of two separate Django applications that communicate via RabbitMQ:
1. **api_service** - The main API service that handles user authentication and stock queries
2. **stock_service** - The internal service that fetches stock data from external API

### Running with Docker Compose (recommended)

The easiest way to run the complete project is using Docker Compose:

```bash
# Start all services (RabbitMQ, API Service, Stock Service)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

This will:
1. Start a RabbitMQ server on ports 5672 (AMQP) and 15672 (Management UI)
2. Start the Stock Service on port 8001
3. Start the API Service on port 8000

### Docker Compose Configuration

The main `docker-compose.yml` handles:
- Building all services from Dockerfiles
- Setting up a RabbitMQ container
- Configuring environment variables via `.env` file
- Creating proper dependency chains between services
- Setting up healthchecks to ensure services start in the right order
- Configuring networking between services
- Setting up persistent volumes for RabbitMQ

### Running with UV (without Docker)

This project also supports running directly with [uv](https://github.com/astral-sh/uv), a modern Python package installer and resolver.

#### Prerequisites

Install uv:
```bash
pip install uv
```

#### Quick Start with Makefile

A Makefile is provided to simplify running the project:

1. Setup the project (one-time):
   ```bash
   make setup
   ```
   This creates a virtual environment with uv, installs dependencies, runs migrations, and creates a superuser (admin/admin123).

2. Start RabbitMQ (requires Docker):
   ```bash
   make rabbitmq-up
   ```

3. Run both services with a single command:
   ```bash
   make run
   ```
   This starts the stock service on port 8001 and the API service on port 8000.

Available Makefile commands:
- `make setup` - Initial setup
- `make sync` - Sync dependencies using uv
- `make add pkg=name` - Add a new package and update requirements.txt
- `make run` - Run both services
- `make run-stock` - Run only the stock service
- `make run-api` - Run only the API service
- `make rabbitmq-up` - Start RabbitMQ server using Docker Compose
- `make rabbitmq-down` - Stop RabbitMQ server
- `make test-rabbitmq s=AAPL.US` - Test RabbitMQ with a stock code
- `make test` - Run tests for both services
- `make clean` - Remove virtualenv and database files
- `make help` - Show help messages

#### Manual Setup and Installation with uv

If you prefer not to use the Makefile:

1. Create a virtual environment with uv:
   ```bash
   uv venv
   ```

2. Activate the virtual environment (optional when using uv run):
   ```bash
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```

4. Run setup scripts to prepare the databases:
   ```bash
   cd stock_service
   chmod +x setup.sh
   ./setup.sh  # This will run migrations
   cd ..
   
   cd api_service
   chmod +x setup.sh
   ./setup.sh  # This will run migrations and create a superuser (admin/admin123)
   cd ..
   ```
   
   Note: The setup scripts will automatically use `uv run` to execute Django commands.

5. Start RabbitMQ (requires Docker):
   ```bash
   docker-compose up -d rabbitmq
   ```

6. Run both services in separate terminal windows:

   Terminal 1 - Stock Service:
   ```bash
   cd stock_service
   uv run python manage.py runserver 8001
   ```

   Terminal 2 - API Service:
   ```bash
   cd api_service
   uv run python manage.py runserver 8000
   ```

### Testing the API

1. Register a user and get a token:
   ```bash
   curl -X POST -H "Content-Type: application/json" -d '{"username":"testuser","password":"testpass"}' http://localhost:8000/api/register/
   ```

2. Query stock data (replace `<your_token>` with the token from the previous step):
   ```bash
   curl -X GET -H "Authorization: Token <your_token>" http://localhost:8000/stock/?symbol=aapl.us
   ```

3. View query history:
   ```bash
   curl -X GET -H "Authorization: Token <your_token>" http://localhost:8000/history/
   ```

4. View stats (admin only - use admin token):
   ```bash
   curl -X GET -H "Authorization: Token <admin_token>" http://localhost:8000/stats/
   ```

### Available Endpoints

- **Register**: POST `/register/` - Create a user account and get a token
- **Stock**: GET `/stock/?symbol=<stock_symbol>` - Query stock data
- **History**: GET `/history/` - View your stock query history
- **Stats**: GET `/stats/` - View most requested stocks (admin only)

Detailed documentation is available in each project's README file.
