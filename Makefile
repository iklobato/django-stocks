.PHONY: setup sync add run run-stock run-api test clean help rabbitmq-up rabbitmq-down test-rabbitmq

# Default target
help:
	@echo "Available commands:"
	@echo "  make setup           - Setup the project (create virtualenv with uv, install dependencies, run migrations)"
	@echo "  make sync            - Sync dependencies using uv (for updating dependencies)"
	@echo "  make add pkg=name    - Add a new package and update requirements.txt"
	@echo "  make run             - Run both services (stock service on port 8001, API service on port 8000)"
	@echo "  make run-stock       - Run only the stock service on port 8001"
	@echo "  make run-api         - Run only the API service on port 8000"
	@echo "  make rabbitmq-up     - Start RabbitMQ server using Docker Compose"
	@echo "  make rabbitmq-down   - Stop RabbitMQ server"
	@echo "  make test-rabbitmq s=AAPL.US - Test RabbitMQ with a stock code"
	@echo "  make test            - Run tests for both services"
	@echo "  make clean           - Remove virtualenv and database files"
	@echo "  make help            - Show this help message"

# Check if uv is installed
check-uv:
	@command -v uv >/dev/null 2>&1 || { echo "uv is not installed. Please install it with 'pip install uv'"; exit 1; }

# Setup the project with uv
setup: check-uv
	@echo "Setting up the project with uv..."
	@uv venv
	@echo "Installing dependencies using uv..."
	@uv pip install -r requirements.txt
	@chmod +x stock_project/setup.sh stock_service/setup.sh
	@echo "Running setup scripts..."
	@cd stock_project && ./setup.sh
	@cd stock_service && ./setup.sh
	@echo "Setup complete! Use 'make run' to start both services."

# Sync dependencies using uv
sync: check-uv
	@echo "Syncing dependencies using uv..."
	@uv pip install -r requirements.txt
	@echo "Dependencies synced successfully!"

# Add a package using uv
add: check-uv
	@if [ -z "$(pkg)" ]; then \
		echo "Usage: make add pkg=<package_name>"; \
		exit 1; \
	fi
	@echo "Installing package $(pkg) using uv..."
	@uv pip install --upgrade $(pkg)
	@echo "Updating requirements.txt..."
	@uv pip freeze > requirements.txt
	@echo "Package $(pkg) installed successfully!"

# Run both services
run: check-uv
	@echo "Starting both services with uv run..."
	@echo "Stock service will run on port 8001"
	@echo "API service will run on port 8000"
	@echo "Use Ctrl+C to stop both services"
	@echo "--------------------------------------------"
	@trap 'kill %1 %2' SIGINT; \
	cd stock_service && uv run python manage.py runserver 8001 & \
	cd stock_project && uv run python manage.py runserver 8000 & \
	wait

# Run only the stock service
run-stock: check-uv
	@echo "Starting stock service on port 8001 with uv run..."
	@cd stock_service && uv run python manage.py runserver 8001

# Run only the API service
run-api: check-uv
	@echo "Starting API service on port 8000 with uv run..."
	@cd stock_project && uv run python manage.py runserver 8000

# Run tests
test: check-uv
	@echo "Running tests for stock service with uv run..."
	@cd stock_service && uv run python manage.py test
	@echo "Running tests for API service with uv run..."
	@cd stock_project && uv run python manage.py test

# Start RabbitMQ using Docker Compose
rabbitmq-up:
	@echo "Starting RabbitMQ with Docker Compose..."
	@docker-compose up -d
	@echo "RabbitMQ is running. Management UI available at http://localhost:15672 (guest/guest)"

# Stop RabbitMQ
rabbitmq-down:
	@echo "Stopping RabbitMQ..."
	@docker-compose down
	@echo "RabbitMQ stopped"

# Test RabbitMQ
test-rabbitmq: check-uv
	@if [ -z "$(s)" ]; then \
		echo "Usage: make test-rabbitmq s=<stock_code> (e.g., make test-rabbitmq s=AAPL.US)"; \
		exit 1; \
	fi
	@echo "Testing RabbitMQ with stock code $(s)..."
	@cd stock_service && uv run python manage.py test_rabbitmq $(s)

# Clean up
clean:
	@echo "Cleaning up..."
	@rm -rf .venv
	@rm -f stock_project/db.sqlite3
	@rm -f stock_service/db.sqlite3
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@echo "Cleanup complete!"