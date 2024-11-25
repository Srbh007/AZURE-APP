#!/bin/bash

echo "Starting Azure App Service deployment process"

# Check or create the virtual environment
if [ ! -d "/home/site/wwwroot/antenv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv /home/site/wwwroot/antenv
fi

# Activate the virtual environment
echo "Activating virtual environment"
source /home/site/wwwroot/antenv/bin/activate

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
   
