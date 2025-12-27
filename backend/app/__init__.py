from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from .config import config
import os

db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()


def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Configure CORS to allow both development and production domains
    allowed_origins = [app.config['FRONTEND_URL']]
    # Add production HTTPS domain if not already included
    production_domain = 'https://launchpad.crl.to'
    if production_domain not in allowed_origins:
        allowed_origins.append(production_domain)
    
    CORS(app, origins=allowed_origins, supports_credentials=True)
    socketio.init_app(app, cors_allowed_origins=allowed_origins)
    
    # Register blueprints
    from .routes import auth, repositories, pipelines, domains, settings, ssh_keys, coolify
    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(repositories.bp, url_prefix='/api/repositories')
    app.register_blueprint(pipelines.bp, url_prefix='/api/pipelines')
    app.register_blueprint(domains.bp, url_prefix='/api/domains')
    app.register_blueprint(settings.bp, url_prefix='/api/settings')
    app.register_blueprint(ssh_keys.bp, url_prefix='/api/ssh-keys')
    app.register_blueprint(coolify.bp, url_prefix='/api/coolify')
    
    # Register WebSocket handlers
    from . import websocket_handlers
    
    # Health check endpoint with comprehensive checks
    @app.route('/health')
    def health():
        """
        Health check endpoint that verifies all critical services
        Returns 200 if all services are healthy, 503 if any service is down
        """
        health_status = {
            'status': 'healthy',
            'services': {}
        }
        
        # Check database connection
        try:
            db.session.execute('SELECT 1')
            health_status['services']['database'] = 'healthy'
        except Exception as e:
            health_status['services']['database'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'unhealthy'
        
        # Check Redis connection
        try:
            import redis
            redis_client = redis.from_url(app.config['REDIS_URL'])
            redis_client.ping()
            health_status['services']['redis'] = 'healthy'
        except Exception as e:
            health_status['services']['redis'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'unhealthy'
        
        # Return appropriate status code
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return health_status, status_code
    
    # Readiness check endpoint
    @app.route('/ready')
    def ready():
        """
        Readiness check endpoint for Kubernetes/container orchestration
        """
        return {'status': 'ready'}, 200
    
    return app
