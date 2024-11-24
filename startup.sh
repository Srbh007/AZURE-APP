#!/bin/bash

echo "Starting Azure App Service deployment process"

# Activate the virtual environment (if applicable)
if [ -d "/home/site/wwwroot/antenv/bin" ]; then
    echo "Activating virtual environment"
    source /home/site/wwwroot/antenv/bin/activate
else
    echo "Virtual environment not found. Proceeding without it."
fi

# Upgrade pip to the latest version
echo "Upgrading pip"
pip install --upgrade pip

# Install dependencies from requirements.txt
echo "Installing dependencies"
pip install -r /home/site/wwwroot/requirements.txt || { echo "Dependency installation failed"; exit 1; }

# Apply database migrations (if any)
if [ -d "/home/site/wwwroot/migrations" ]; then
    echo "Applying database migrations"
    python -m flask db upgrade || { echo "Database migration failed"; exit 1; }
else
    echo "No migrations directory found. Skipping database migrations."
fi

# Start the Gunicorn server
echo "Starting Gunicorn server"
gunicorn --bind=0.0.0.0 --timeout 600 --workers=4 --chdir=/home/site/wwwroot app:app --log-level debug
