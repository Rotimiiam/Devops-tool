"""
Coolify API Routes
Provides endpoints for Coolify deployment management
"""
from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
from sqlalchemy import and_
from ..models import User, Pipeline, CoolifyDeployment, db
from ..services.coolify_integration import get_coolify_service, CoolifyAPIException
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('coolify', __name__)


def get_current_user():
    """Get current authenticated user"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)


@bp.route('/health', methods=['GET'])
def check_coolify_health():
    """
    Check Coolify service health and availability
    GET /api/coolify/health
    
    Returns:
        JSON response with Coolify health status
    """
    try:
        coolify_service = get_coolify_service()
        health_status = coolify_service.check_health()
        
        status_code = 200 if health_status['available'] else 503
        return jsonify(health_status), status_code
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({
            'available': False,
            'status': 'error',
            'error': str(e),
            'message': 'Failed to check Coolify health'
        }), 503


@bp.route('/deployments', methods=['POST'])
def create_deployment():
    """
    Create a new test deployment in Coolify
    POST /api/coolify/deployments
    
    Request body:
        {
            "pipeline_id": int,
            "application_name": str (optional),
            "docker_image": str (optional),
            "dockerfile_path": str (optional),
            "git_repository": str (optional),
            "git_branch": str (optional),
            "environment_variables": dict (optional),
            "port_mappings": list (optional),
            "auto_start": bool (optional, default: true)
        }
    
    Returns:
        JSON response with created deployment details
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        
        # Validate required fields
        pipeline_id = data.get('pipeline_id')
        if not pipeline_id:
            return jsonify({'error': 'pipeline_id is required'}), 400
        
        # Get pipeline and verify ownership
        pipeline = Pipeline.query.get(pipeline_id)
        if not pipeline or pipeline.repository.user_id != user.id:
            return jsonify({'error': 'Pipeline not found'}), 404
        
        # Check Coolify availability
        coolify_service = get_coolify_service()
        health = coolify_service.check_health()
        if not health['available']:
            return jsonify({
                'error': 'Coolify service is not available',
                'details': health
            }), 503
        
        # Prepare deployment configuration
        application_name = data.get('application_name') or f"{pipeline.repository.name}-test-{pipeline.id}"
        
        config = {
            'docker_image': data.get('docker_image'),
            'dockerfile_path': data.get('dockerfile_path', './Dockerfile'),
            'git_repository': data.get('git_repository'),
            'git_branch': data.get('git_branch', 'main'),
            'environment_variables': data.get('environment_variables') or pipeline.environment_variables or {},
            'port_mappings': data.get('port_mappings') or [{'container_port': pipeline.port or 3000}],
            'build_pack': data.get('build_pack', 'dockerfile')
        }
        
        # Create deployment in Coolify
        deployment_result = coolify_service.create_deployment(application_name, config)
        
        # Store deployment record in database
        coolify_deployment = CoolifyDeployment(
            pipeline_id=pipeline_id,
            coolify_deployment_id=deployment_result['deployment_id'],
            coolify_application_id=deployment_result.get('application_id'),
            application_name=application_name,
            docker_image=config.get('docker_image'),
            dockerfile_path=config.get('dockerfile_path'),
            environment_variables=config['environment_variables'],
            port_mappings=config['port_mappings'],
            deployment_url=deployment_result.get('deployment_url'),
            status='pending'
        )
        
        db.session.add(coolify_deployment)
        db.session.commit()
        
        # Auto-start deployment if requested
        auto_start = data.get('auto_start', True)
        if auto_start:
            try:
                coolify_service.start_deployment(deployment_result['deployment_id'])
                coolify_deployment.status = 'building'
                db.session.commit()
            except Exception as e:
                logger.error(f"Failed to auto-start deployment: {str(e)}")
                # Continue even if auto-start fails
        
        return jsonify({
            'success': True,
            'deployment': {
                'id': coolify_deployment.id,
                'deployment_id': coolify_deployment.coolify_deployment_id,
                'application_name': coolify_deployment.application_name,
                'status': coolify_deployment.status,
                'deployment_url': coolify_deployment.deployment_url,
                'created_at': coolify_deployment.created_at.isoformat() if coolify_deployment.created_at else None
            }
        }), 201
        
    except CoolifyAPIException as e:
        logger.error(f"Coolify API error: {str(e)}")
        return jsonify({
            'error': 'Failed to create deployment in Coolify',
            'details': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error creating deployment: {str(e)}")
        db.session.rollback()
        return jsonify({
            'error': 'Failed to create deployment',
            'details': str(e)
        }), 500


@bp.route('/deployments/<int:deployment_id>', methods=['GET'])
def get_deployment_status(deployment_id):
    """
    Get deployment status and details
    GET /api/coolify/deployments/<deployment_id>
    
    Returns:
        JSON response with deployment status
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Get deployment record
        deployment = CoolifyDeployment.query.get(deployment_id)
        if not deployment or deployment.pipeline.repository.user_id != user.id:
            return jsonify({'error': 'Deployment not found'}), 404
        
        # Get current status from Coolify
        coolify_service = get_coolify_service()
        try:
            status_result = coolify_service.get_deployment_status(deployment.coolify_deployment_id)
            
            # Update local record
            deployment.status = status_result['status']
            deployment.deployment_url = status_result.get('deployment_url') or deployment.deployment_url
            deployment.updated_at = datetime.utcnow()
            db.session.commit()
            
        except CoolifyAPIException as e:
            logger.warning(f"Failed to get status from Coolify: {str(e)}")
            # Return cached status if Coolify is unavailable
            status_result = {
                'status': deployment.status,
                'deployment_id': deployment.coolify_deployment_id,
                'cached': True
            }
        
        return jsonify({
            'deployment': {
                'id': deployment.id,
                'deployment_id': deployment.coolify_deployment_id,
                'application_id': deployment.coolify_application_id,
                'application_name': deployment.application_name,
                'status': deployment.status,
                'deployment_url': deployment.deployment_url,
                'pipeline_id': deployment.pipeline_id,
                'created_at': deployment.created_at.isoformat() if deployment.created_at else None,
                'updated_at': deployment.updated_at.isoformat() if deployment.updated_at else None,
                'cleaned_at': deployment.cleaned_at.isoformat() if deployment.cleaned_at else None
            },
            'coolify_status': status_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting deployment status: {str(e)}")
        return jsonify({
            'error': 'Failed to get deployment status',
            'details': str(e)
        }), 500


@bp.route('/deployments/<int:deployment_id>/logs', methods=['GET'])
def get_deployment_logs(deployment_id):
    """
    Get deployment build and runtime logs
    GET /api/coolify/deployments/<deployment_id>/logs?type=<log_type>
    
    Query params:
        type: Log type (build, runtime, or combined) - default: combined
    
    Returns:
        JSON response with deployment logs
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Get deployment record
        deployment = CoolifyDeployment.query.get(deployment_id)
        if not deployment or deployment.pipeline.repository.user_id != user.id:
            return jsonify({'error': 'Deployment not found'}), 404
        
        log_type = request.args.get('type', 'combined')
        
        # Get logs from Coolify
        coolify_service = get_coolify_service()
        try:
            logs_result = coolify_service.get_deployment_logs(
                deployment.coolify_deployment_id,
                log_type
            )
            
            # Update local cache
            if logs_result.get('build_logs'):
                deployment.build_logs = logs_result['build_logs']
            if logs_result.get('runtime_logs'):
                deployment.runtime_logs = logs_result['runtime_logs']
            db.session.commit()
            
        except CoolifyAPIException as e:
            logger.warning(f"Failed to get logs from Coolify: {str(e)}")
            # Return cached logs if Coolify is unavailable
            logs_result = {
                'build_logs': deployment.build_logs or 'No build logs available',
                'runtime_logs': deployment.runtime_logs or 'No runtime logs available',
                'combined_logs': f"=== BUILD LOGS ===\n{deployment.build_logs or 'N/A'}\n\n=== RUNTIME LOGS ===\n{deployment.runtime_logs or 'N/A'}",
                'cached': True
            }
        
        return jsonify({
            'deployment_id': deployment_id,
            'logs': logs_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting deployment logs: {str(e)}")
        return jsonify({
            'error': 'Failed to get deployment logs',
            'details': str(e)
        }), 500


@bp.route('/deployments/<int:deployment_id>', methods=['DELETE'])
def delete_deployment(deployment_id):
    """
    Stop and delete a test deployment
    DELETE /api/coolify/deployments/<deployment_id>
    
    Returns:
        JSON response with deletion result
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Get deployment record
        deployment = CoolifyDeployment.query.get(deployment_id)
        if not deployment or deployment.pipeline.repository.user_id != user.id:
            return jsonify({'error': 'Deployment not found'}), 404
        
        # Delete from Coolify
        coolify_service = get_coolify_service()
        try:
            coolify_service.delete_deployment(deployment.coolify_deployment_id)
        except CoolifyAPIException as e:
            logger.warning(f"Failed to delete from Coolify (continuing anyway): {str(e)}")
        
        # Mark as cleaned in database
        deployment.status = 'stopped'
        deployment.cleaned_at = datetime.utcnow()
        db.session.commit()
        
        # Optionally delete the record
        # db.session.delete(deployment)
        # db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Deployment deleted successfully',
            'deployment_id': deployment_id
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting deployment: {str(e)}")
        return jsonify({
            'error': 'Failed to delete deployment',
            'details': str(e)
        }), 500


@bp.route('/deployments', methods=['GET'])
def list_deployments():
    """
    List all deployments for the authenticated user
    GET /api/coolify/deployments?pipeline_id=<id>&status=<status>
    
    Query params:
        pipeline_id: Filter by pipeline ID (optional)
        status: Filter by status (optional)
        include_cleaned: Include cleaned deployments (optional, default: false)
    
    Returns:
        JSON response with list of deployments
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Build query
        query = CoolifyDeployment.query.join(Pipeline).join(Pipeline.repository).filter(
            Pipeline.repository.has(user_id=user.id)
        )
        
        # Apply filters
        pipeline_id = request.args.get('pipeline_id', type=int)
        if pipeline_id:
            query = query.filter(CoolifyDeployment.pipeline_id == pipeline_id)
        
        status = request.args.get('status')
        if status:
            query = query.filter(CoolifyDeployment.status == status)
        
        include_cleaned = request.args.get('include_cleaned', 'false').lower() == 'true'
        if not include_cleaned:
            query = query.filter(CoolifyDeployment.cleaned_at.is_(None))
        
        # Order by most recent first
        query = query.order_by(CoolifyDeployment.created_at.desc())
        
        deployments = query.all()
        
        return jsonify({
            'deployments': [{
                'id': d.id,
                'deployment_id': d.coolify_deployment_id,
                'application_id': d.coolify_application_id,
                'application_name': d.application_name,
                'status': d.status,
                'deployment_url': d.deployment_url,
                'pipeline_id': d.pipeline_id,
                'pipeline_version': d.pipeline.version,
                'repository_name': d.pipeline.repository.name,
                'created_at': d.created_at.isoformat() if d.created_at else None,
                'updated_at': d.updated_at.isoformat() if d.updated_at else None,
                'cleaned_at': d.cleaned_at.isoformat() if d.cleaned_at else None
            } for d in deployments]
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing deployments: {str(e)}")
        return jsonify({
            'error': 'Failed to list deployments',
            'details': str(e)
        }), 500


@bp.route('/deployments/<int:deployment_id>/start', methods=['POST'])
def start_deployment(deployment_id):
    """
    Start/trigger a deployment
    POST /api/coolify/deployments/<deployment_id>/start
    
    Returns:
        JSON response with start result
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Get deployment record
        deployment = CoolifyDeployment.query.get(deployment_id)
        if not deployment or deployment.pipeline.repository.user_id != user.id:
            return jsonify({'error': 'Deployment not found'}), 404
        
        # Start deployment in Coolify
        coolify_service = get_coolify_service()
        result = coolify_service.start_deployment(deployment.coolify_deployment_id)
        
        # Update status
        deployment.status = 'building'
        deployment.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Deployment started successfully',
            'deployment_id': deployment_id,
            'status': deployment.status
        }), 200
        
    except CoolifyAPIException as e:
        logger.error(f"Coolify API error: {str(e)}")
        return jsonify({
            'error': 'Failed to start deployment',
            'details': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Error starting deployment: {str(e)}")
        return jsonify({
            'error': 'Failed to start deployment',
            'details': str(e)
        }), 500


@bp.route('/deployments/<int:deployment_id>/stop', methods=['POST'])
def stop_deployment(deployment_id):
    """
    Stop a running deployment
    POST /api/coolify/deployments/<deployment_id>/stop
    
    Returns:
        JSON response with stop result
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Get deployment record
        deployment = CoolifyDeployment.query.get(deployment_id)
        if not deployment or deployment.pipeline.repository.user_id != user.id:
            return jsonify({'error': 'Deployment not found'}), 404
        
        # Stop deployment in Coolify
        coolify_service = get_coolify_service()
        result = coolify_service.stop_deployment(deployment.coolify_deployment_id)
        
        # Update status
        deployment.status = 'stopped'
        deployment.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Deployment stopped successfully',
            'deployment_id': deployment_id,
            'status': deployment.status
        }), 200
        
    except CoolifyAPIException as e:
        logger.error(f"Coolify API error: {str(e)}")
        return jsonify({
            'error': 'Failed to stop deployment',
            'details': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Error stopping deployment: {str(e)}")
        return jsonify({
            'error': 'Failed to stop deployment',
            'details': str(e)
        }), 500


@bp.route('/cleanup/old', methods=['POST'])
def cleanup_old_deployments():
    """
    Manually trigger cleanup of old deployments
    POST /api/coolify/cleanup/old?age_hours=<hours>
    
    Query params:
        age_hours: Age threshold in hours (default: 24)
    
    Returns:
        JSON response with cleanup results
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        age_hours = request.args.get('age_hours', 24, type=int)
        cutoff_time = datetime.utcnow() - timedelta(hours=age_hours)
        
        # Find old deployments
        old_deployments = CoolifyDeployment.query.join(Pipeline).join(Pipeline.repository).filter(
            and_(
                Pipeline.repository.has(user_id=user.id),
                CoolifyDeployment.created_at < cutoff_time,
                CoolifyDeployment.cleaned_at.is_(None),
                CoolifyDeployment.status.notin_(['stopped'])
            )
        ).all()
        
        coolify_service = get_coolify_service()
        cleaned_count = 0
        failed_count = 0
        
        for deployment in old_deployments:
            try:
                # Delete from Coolify
                coolify_service.delete_deployment(deployment.coolify_deployment_id)
                
                # Mark as cleaned
                deployment.status = 'stopped'
                deployment.cleaned_at = datetime.utcnow()
                cleaned_count += 1
                
            except Exception as e:
                logger.error(f"Failed to cleanup deployment {deployment.id}: {str(e)}")
                failed_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up {cleaned_count} old deployments',
            'cleaned_count': cleaned_count,
            'failed_count': failed_count,
            'age_hours': age_hours
        }), 200
        
    except Exception as e:
        logger.error(f"Error cleaning up old deployments: {str(e)}")
        db.session.rollback()
        return jsonify({
            'error': 'Failed to cleanup old deployments',
            'details': str(e)
        }), 500
