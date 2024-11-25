#!/bin/bash

echo "Starting Azure App Service deployment process"

# Check or create the virtual environment in a writable directory
if [ ! -d "/tmp/antenv" ]; then
    echo "Virtual environment not found. Creating one in /tmp..."
    python3 -m venv /tmp/antenv
fi

# Activate the virtual environment
echo "Activating virtual environment"
source /tmp/antenv/bin/activate

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
