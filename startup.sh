#!/bin/bash

echo "Starting Azure App Service deployment process"

# Create and set permissions for necessary directories
mkdir -p /home/site/wwwroot/instance
chmod 777 /home/site/wwwroot/instance
mkdir -p /home/site/wwwroot/data
chmod 777 /home/site/wwwroot/data

# Create and activate virtual environment
if [ ! -d "/home/antenv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv /home/antenv
fi

echo "Activating virtual environment"
source /home/antenv/bin/activate

# Upgrade pip and install dependencies
echo "Upgrading pip"
pip install --upgrade pip

if [ -f "/home/site/wwwroot/requirements.txt" ]; then
    echo "Installing dependencies"
    pip install -r /home/site/wwwroot/requirements.txt || { echo "Dependency installation failed"; exit 1; }
else
    echo "requirements.txt not found!"
    exit 1
fi

# Initialize database with proper permissions
python - << EOF
from app import initialize_database
initialize_database()
EOF

# Apply migrations if they exist
if [ -d "/home/site/wwwroot/migrations" ]; then
    echo "Applying database migrations"
    flask db upgrade || { echo "Migration failed"; exit 1; }
fi

# Ensure proper permissions again after all operations
chmod 777 /home/site/wwwroot/instance
chmod 666 /home/site/wwwroot/instance/site.db

# Start Gunicorn
echo "Starting Gunicorn"
gunicorn --bind=0.0.0.0 --timeout 600 --workers=4 --chdir=/home/site/wwwroot app:app --log-level debug