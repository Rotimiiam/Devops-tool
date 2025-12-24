from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import config
import os

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, origins=[app.config['FRONTEND_URL']], supports_credentials=True)
    
    # Register blueprints
    from .routes import auth, repositories, pipelines, domains, settings
    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(repositories.bp, url_prefix='/api/repositories')
    app.register_blueprint(pipelines.bp, url_prefix='/api/pipelines')
    app.register_blueprint(domains.bp, url_prefix='/api/domains')
    app.register_blueprint(settings.bp, url_prefix='/api/settings')
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'healthy'}, 200
    
    return app
