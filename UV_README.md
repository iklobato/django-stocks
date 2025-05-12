# Using Python UV with Django Challenge

This repository has been configured to use [uv](https://github.com/astral-sh/uv), a modern Python package installer and resolver.

## Prerequisites

Install `uv`:

```bash
pip install uv
```

## Setting Up Development Environment

### Create a Virtual Environment

```bash
uv venv
```

### Activate the Virtual Environment

```bash
source .venv/bin/activate
```

### Install Dependencies

```bash
# If requirements.txt exists
uv pip install -r requirements.txt

# Or install core dependencies directly
uv pip install django==3.1.7 djangorestframework==3.12.4 requests==2.25.1 setuptools
```

### Service-Specific Dependencies

The core dependencies are the same for both services, so explicit installation of service-specific dependencies is usually not necessary. However, if you need to add service-specific dependencies:

```bash
# For both services
uv pip install <dependency-name>

# Update requirements.txt for future installs
uv pip freeze > requirements.txt
```

## Running the Services

After installing dependencies:

### API Service
```bash
cd api_service
uv run python manage.py runserver
```

### Stock Service
```bash
cd stock_service
uv run python manage.py runserver 8001
```

## Development Workflow

To add new dependencies:

```bash
# Using the Makefile (recommended)
make add pkg=package_name

# Or manually
uv pip install package_name
uv pip freeze > requirements.txt
```

## Updating Dependencies

To update dependencies to their latest versions:

```bash
# Update a specific package
uv pip install --upgrade package_name
uv pip freeze > requirements.txt

# Update all packages based on requirements.txt
uv pip install --upgrade -r requirements.txt
```

## Note on Package Management

This project uses uv for faster and more reliable dependency installation. It contains two separate Django applications that share the same core dependencies. We use requirements.txt for simplicity while maintaining a standardized pyproject.toml for compatibility with modern Python tools.