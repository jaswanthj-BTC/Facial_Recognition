import os
from dotenv import load_dotenv
from pymongo import MongoClient

from datetime import timedelta

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Configuration class for Flask application
    Loads all configuration from environment variables
    """

    # Flask Configuration
    SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'True') == 'True'

    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)  # Token valid for 24 hours
    JWT_ALGORITHM = 'HS256'

    # MongoDB Configuration
    MONGO_URI = os.getenv('MONGO_URI')

    # Application Settings
    PORT = int(os.getenv('PORT', 5000))
    HOST = os.getenv('HOST', '0.0.0.0')

    # CORS Settings
    CORS_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:5500']  # Add your frontend URLs


class DatabaseConfig:
    """
    Database connection and management class
    Handles MongoDB connection and provides database instance
    """

    _client = None
    _db = None

    @classmethod
    def get_db(cls):
        """
        Singleton pattern to get database instance
        Returns the same database connection throughout the app lifecycle
        """
        if cls._db is None:
            cls._client = MongoClient(Config.MONGO_URI)
            cls._db = cls._client['Facial_Recognition']  # Database name
            print("✅ MongoDB Connected Successfully!")
        return cls._db

    @classmethod
    def close_connection(cls):
        """Close MongoDB connection"""
        if cls._client:
            cls._client.close()
            print(" MongoDB Connection Closed")

    @classmethod
    def test_connection(cls):
        """Test if MongoDB connection is working"""
        try:
            db = cls.get_db()
            # Ping the database
            db.command('ping')
            return True
        except Exception as e:
            print(f"MongoDB Connection Failed: {str(e)}")
            return False


# Initialize database connection when config is imported
def init_database():
    """Initialize database and create indexes"""
    db = DatabaseConfig.get_db()

    # Create indexes for better query performance
    db.users.create_index('email', unique=True)
    db.users.create_index('username', unique=True)

    print("✅ Database indexes created successfully")