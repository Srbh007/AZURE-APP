#!/bin/bash

echo "Starting Azure App Service deployment process"

# Create necessary directories in writable location
echo "Creating necessary directories..."
mkdir -p /home/data/instance
mkdir -p /home/data/uploads
chmod -R 777 /home/data/instance
chmod -R 777 /home/data/uploads

# Create and activate virtual environment
if [ ! -d "/home/antenv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv /home/antenv || { echo "Virtual environment creation failed"; exit 1; }
fi

echo "Activating virtual environment"
source /home/antenv/bin/activate || { echo "Virtual environment activation failed"; exit 1; }

# Upgrade pip and install dependencies
echo "Upgrading pip"
pip install --upgrade pip || { echo "Pip upgrade failed"; exit 1; }

if [ -f "/home/site/wwwroot/requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt"
    pip install -r /home/site/wwwroot/requirements.txt || { echo "Dependency installation failed"; exit 1; }
else
    echo "requirements.txt not found!"
    exit 1
fi

# Initialize database
echo "Initializing database..."
python - << EOF
import os
import sys
sys.path.append('/home/site/wwwroot')
from app import initialize_database
if not initialize_database():
    print("Database initialization failed")
    sys.exit(1)
EOF || { echo "Database initialization failed"; exit 1; }

# Apply migrations if migrations folder exists
if [ -d "/home/site/wwwroot/migrations" ]; then
    echo "Applying database migrations..."
    cd /home/site/wwwroot
    export FLASK_APP=app.py
    flask db upgrade || { echo "Database migration failed"; exit 1; }
else
    echo "Migrations folder not found. Skipping migrations."
fi

# Verify database file permissions
if [ -f "/home/data/instance/site.db" ]; then
    echo "Setting database file permissions..."
    chmod 666 /home/data/instance/site.db
else
    echo "Database file not found at /home/data/instance/site.db"
    exit 1
fi

# Start Gunicorn to serve the application
echo "Starting Gunicorn server..."
cd /home/site/wwwroot
gunicorn --bind=0.0.0.0:8000 --timeout 600 --workers=4 app:app --log-level debug || { echo "Gunicorn failed to start"; exit 1; }
