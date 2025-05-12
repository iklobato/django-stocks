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
# On Unix/macOS
source .venv/bin/activate

# On Windows
.venv\Scripts\activate
```

### Install Dependencies

```bash
# Install all dependencies directly from requirements.txt
uv pip install -r requirements.txt

# Make sure setuptools is installed (needed for distutils)
uv pip install setuptools

# OR use uv sync to install from pyproject.toml
uv sync
```

### Service-Specific Dependencies

You can install service-specific dependencies using groups:

```bash
# For API service
uv pip install -G api

# For Stock service
uv pip install -G stock

# For development tools
uv pip install -G dev
```

## Running the Services

After installing dependencies:

### API Service
```bash
cd api_service
python manage.py runserver
```

### Stock Service
```bash
cd stock_service
python manage.py runserver 8001
```

## Development Workflow

To add new dependencies:

```bash
# Add a dependency
uv pip install package_name

# Update requirements.txt
uv pip freeze > requirements.txt

# Update pyproject.toml groups manually
```

## Note on Package Management

This project uses uv for dependency management but is NOT configured as a Python package. It contains two separate Django applications that share dependencies. The pyproject.toml file is used solely for dependency management with uv and development tool configuration.