from datetime import datetime
from . import db


class User(db.Model):
    """User model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # OAuth connections
    bitbucket_token = db.Column(db.Text)
    bitbucket_refresh_token = db.Column(db.Text)
    bitbucket_username = db.Column(db.String(255))
    
    github_token = db.Column(db.Text)
    github_refresh_token = db.Column(db.Text)
    github_username = db.Column(db.String(255))
    
    # API Keys
    gemini_api_key = db.Column(db.Text)
    
    # Relationships
    repositories = db.relationship('Repository', backref='user', lazy=True, cascade='all, delete-orphan')
    domains = db.relationship('Domain', backref='user', lazy=True, cascade='all, delete-orphan')


class Repository(db.Model):
    """Repository model"""
    __tablename__ = 'repositories'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    name = db.Column(db.String(255), nullable=False)
    source = db.Column(db.String(50), nullable=False)  # 'github' or 'bitbucket'
    source_repo_id = db.Column(db.String(255))
    source_repo_url = db.Column(db.String(500))
    
    bitbucket_repo_id = db.Column(db.String(255))
    bitbucket_repo_url = db.Column(db.String(500))
    bitbucket_workspace = db.Column(db.String(255))
    
    status = db.Column(db.String(50), default='pending')  # pending, migrated, pipeline_generated, pipeline_testing, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Analysis fields
    detected_languages = db.Column(db.JSON)  # {language: {count: int, confidence: float}}
    detected_frameworks = db.Column(db.JSON)  # {framework: {version: str, confidence: float}}
    required_env_vars = db.Column(db.JSON)  # {var_name: {source_files: [], confidence: float}}
    analysis_confidence = db.Column(db.Float)  # Overall confidence score 0-100
    analysis_timestamp = db.Column(db.DateTime)
    ai_recommendations = db.Column(db.Text)  # AI-generated recommendations
    
    # Relationships
    pipelines = db.relationship('Pipeline', backref='repository', lazy=True, cascade='all, delete-orphan')


class Pipeline(db.Model):
    """Pipeline model"""
    __tablename__ = 'pipelines'
    
    id = db.Column(db.Integer, primary_key=True)
    repository_id = db.Column(db.Integer, db.ForeignKey('repositories.id'), nullable=False)
    
    version = db.Column(db.Integer, default=1)
    config = db.Column(db.Text, nullable=False)  # YAML content
    status = db.Column(db.String(50), default='draft')  # draft, PLANNED, BUILDING, TESTING, DEPLOYING, SUCCESS, FAILED
    is_active = db.Column(db.Boolean, default=True)  # For uniqueness constraint
    
    test_output = db.Column(db.Text)
    error_message = db.Column(db.Text)
    
    # Deployment configuration
    deployment_server = db.Column(db.String(500))
    server_ip = db.Column(db.String(100))
    subdomain = db.Column(db.String(255))
    port = db.Column(db.Integer)
    environment_variables = db.Column(db.JSON)  # {var_name: var_value}
    
    # Nginx configuration
    nginx_config = db.Column(db.Text)
    ssl_enabled = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # PR information
    pr_created = db.Column(db.Boolean, default=False)
    pr_url = db.Column(db.String(500))
    
    # Bitbucket pipeline information
    bitbucket_pipeline_uuid = db.Column(db.String(255))
    last_execution_timestamp = db.Column(db.DateTime)
    
    # Relationships
    executions = db.relationship('PipelineExecution', backref='pipeline', lazy=True, cascade='all, delete-orphan', order_by='PipelineExecution.started_at.desc()')
    
    # Uniqueness constraint: only one active pipeline per repository
    __table_args__ = (
        db.UniqueConstraint('repository_id', 'is_active', name='unique_active_pipeline_per_repo'),
    )


class PipelineExecution(db.Model):
    """Pipeline execution history model"""
    __tablename__ = 'pipeline_executions'
    
    id = db.Column(db.Integer, primary_key=True)
    pipeline_id = db.Column(db.Integer, db.ForeignKey('pipelines.id'), nullable=False)
    
    # Execution details
    status = db.Column(db.String(50), nullable=False)  # BUILDING, TESTING, DEPLOYING, SUCCESS, FAILED
    trigger_type = db.Column(db.String(50), default='manual')  # manual, webhook, scheduled
    
    # Bitbucket pipeline run information
    bitbucket_build_number = db.Column(db.Integer)
    bitbucket_pipeline_uuid = db.Column(db.String(255))
    bitbucket_commit_hash = db.Column(db.String(100))
    
    # Execution logs and output
    logs = db.Column(db.Text)
    error_message = db.Column(db.Text)
    
    # Rollback information
    rolled_back = db.Column(db.Boolean, default=False)
    rollback_reason = db.Column(db.Text)
    previous_execution_id = db.Column(db.Integer, db.ForeignKey('pipeline_executions.id'), nullable=True)
    
    # Timestamps
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    duration_seconds = db.Column(db.Integer)
    
    # Relationships
    previous_execution = db.relationship('PipelineExecution', remote_side=[id], backref='rollback_executions')


class Domain(db.Model):
    """Domain model for managing root domain and subdomains"""
    __tablename__ = 'domains'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    name = db.Column(db.String(255), nullable=False)
    is_root = db.Column(db.Boolean, default=False)
    parent_domain_id = db.Column(db.Integer, db.ForeignKey('domains.id'), nullable=True)
    
    description = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subdomains = db.relationship('Domain', backref=db.backref('parent', remote_side=[id]), lazy=True)
