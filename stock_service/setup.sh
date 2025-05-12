#!/bin/bash
# Setup script for the stock service

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "UV is not installed. Please install it with 'pip install uv'"
    exit 1
fi

# Make migrations
echo "Making migrations using uv run..."
uv run python manage.py makemigrations

# Apply migrations
echo "Applying migrations using uv run..."
uv run python manage.py migrate

echo "Setup complete!"