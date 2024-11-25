import os
from dotenv import load_dotenv
import secrets

# Load environment variables from the .env file
load_dotenv()

class Config:
    # General Flask settings
    SECRET_KEY = secrets.token_hex(16)  # Secure key generation
    DEBUG = os.environ.get('FLASK_ENV') != 'production'  # Set DEBUG based on environment

    # Database configuration
    if os.environ.get('FLASK_ENV') == 'production':
        # In production (Azure), use a database path in the writable Azure directory
        SQLALCHEMY_DATABASE_URI = 'sqlite:////home/site/wwwroot/instance/site.db'  # Azure DB path
    else:
        # In development (local), use the site.db in the root project directory
        SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'  # Local DB path

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Azure OpenAI API settings (Loaded from .env file)
    AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')  # Loaded from .env
    AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')  # Loaded from .env
    DEPLOYMENT_NAME = os.getenv('DEPLOYMENT_NAME')  # Loaded from .env
    API_VERSION = "2024-05-01-preview"  # API version for Azure OpenAI

    # Path to the folder containing PDF files (adjust path depending on environment)
    if os.environ.get('FLASK_ENV') == 'production':
        PDF_FOLDER = '/home/site/wwwroot/data'  # Path for production in Azure
    else:
        PDF_FOLDER = 'data'  # Path for local development
