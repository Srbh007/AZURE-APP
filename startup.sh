#!/bin/bash

echo "Starting Azure App Service deployment process"

# Check if the virtual environment already exists, if not, create it
if [ ! -d "/home/antenv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv /home/antenv  # Create the virtual environment in the writable directory
fi

# Activate the virtual environment
echo "Activating virtual environment"
source /home/antenv/bin/activate

# Upgrade pip
echo "Upgrading pip"
pip install --upgrade pip

# Install dependencies
if [ -f "/home/site/wwwroot/requirements.txt" ]; then
    echo "Installing dependencies"
    pip install -r /home/site/wwwroot/requirements.txt || { echo "Dependency installation failed"; exit 1; }
else
    echo "requirements.txt not found! Exiting..."
    exit 1
fi

# Apply database migrations (if applicable)
if [ -d "/home/site/wwwroot/migrations" ]; then
    echo "Applying database migrations"
    python -m flask db upgrade || { echo "Database migration failed"; exit 1; }
else
    echo "No migrations directory found. Skipping database migrations."
fi

# Start the Gunicorn server
echo "Starting Gunicorn server"
gunicorn --bind=0.0.0.0 --timeout 600 --workers=4 --chdir=/home/site/wwwroot app:app --log-level debug
