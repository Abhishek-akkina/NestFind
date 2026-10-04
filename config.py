import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask security
    SECRET_KEY = os.getenv("SECRET_KEY")

    # PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cloudinary
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

    # Production settings
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
    TESTING = False