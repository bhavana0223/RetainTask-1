"""
Application configuration module.
Centralizes all configuration settings for better maintainability.
"""
import os


class Config:
    """Base configuration class."""
    
    # Database settings
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'users.db')
    
    # Server settings
    HOST = os.getenv('HOST', '127.0.0.1')  # Changed from 0.0.0.0 for security
    PORT = int(os.getenv('PORT', 5009))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Security settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Password policy
    MIN_PASSWORD_LENGTH = int(os.getenv('MIN_PASSWORD_LENGTH', 8))  # Increased from 6
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    HOST = '0.0.0.0'  # Only in production when properly secured


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class TestingConfig(Config):
    """Testing configuration."""
    DATABASE_PATH = ':memory:'  # Use in-memory database for tests
    DEBUG = True


def get_config():
    """Get configuration based on environment."""
    env = os.getenv('FLASK_ENV', 'development')
    
    config_map = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig,
    }
    
    return config_map.get(env, DevelopmentConfig)
