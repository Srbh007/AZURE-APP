import os
import secrets

class Config:
    # General Flask settings
    SECRET_KEY = secrets.token_hex(16)  # Replace with a secure key
    DEBUG = True


    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Azure OpenAI API settings
    AZURE_OPENAI_API_KEY = "GGaIMnCjhkm5fOeONK5Z8UoteQYnVqGa9WfCZXFvkwC31YyeMPqOJQQJ99AKACYeBjFXJ3w3AAABACOGY4ub"  # Replace with your actual API key
    AZURE_OPENAI_ENDPOINT = "https://egpt123.openai.azure.com/"  # Replace with your endpoint URL
    DEPLOYMENT_NAME = "gpt-35-turbo"  # Replace with your deployment name
    API_VERSION = "2024-05-01-preview"

    # Path to the folder containing PDF files
    PDF_FOLDER = 'data'
# Adjust the path if your PDF files are in a different folder

