import os
from dotenv import load_dotenv
import secrets

# Load environment variables from the .env file
load_dotenv()

class Config:
    # General Flask settings
    SECRET_KEY = secrets.token_hex(16)  # Secure key generation
    DEBUG = True

    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Azure OpenAI API settings
    AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')  # Loaded from .env
    AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')  # Loaded from .env
    DEPLOYMENT_NAME = os.getenv('DEPLOYMENT_NAME')  # Loaded from .env
    API_VERSION = "2024-05-01-preview"  # API version for Azure OpenAI

    # Path to the folder containing PDF files
    PDF_FOLDER = 'data'  # Adjust the path if your PDF files are in a different folder
