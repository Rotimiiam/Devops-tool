import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///devops_tool.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OAuth Configuration
    BITBUCKET_CLIENT_ID = os.getenv('BITBUCKET_CLIENT_ID')
    BITBUCKET_CLIENT_SECRET = os.getenv('BITBUCKET_CLIENT_SECRET')
    BITBUCKET_CALLBACK_URL = os.getenv('BITBUCKET_CALLBACK_URL', 'http://localhost:5000/api/auth/bitbucket/callback')
    
    GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
    GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')
    GITHUB_CALLBACK_URL = os.getenv('GITHUB_CALLBACK_URL', 'http://localhost:5000/api/auth/github/callback')
    
    # API Keys
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Domain Configuration
    ROOT_DOMAIN = os.getenv('ROOT_DOMAIN', 'localhost')
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Celery
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    
    # Coolify Configuration
    COOLIFY_BASE_URL = os.getenv('COOLIFY_BASE_URL', 'http://coolify:9000')
    COOLIFY_API_TOKEN = os.getenv('COOLIFY_API_TOKEN', '')
    COOLIFY_AUTO_CLEANUP_HOURS = int(os.getenv('COOLIFY_AUTO_CLEANUP_HOURS', '24'))


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FLASK_ENV = 'production'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
