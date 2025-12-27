"""
Celery tasks for background job processing
"""
from celery import Celery
from datetime import datetime, timedelta
from sqlalchemy import and_
import os
import logging

logger = logging.getLogger(__name__)

# Initialize Celery
celery = Celery(
    'devops_tool',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
)

# Configure Celery
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        'cleanup-old-coolify-deployments': {
            'task': 'app.tasks.cleanup_old_coolify_deployments',
            'schedule': 3600.0,  # Run every hour
        },
    }
)


@celery.task(name='app.tasks.cleanup_old_coolify_deployments')
def cleanup_old_coolify_deployments():
    """
    Background task to cleanup Coolify deployments older than 24 hours
    """
    try:
        # Import here to avoid circular dependencies
        from app import create_app, db
        from app.models import CoolifyDeployment, Pipeline
        from app.services.coolify_integration import get_coolify_service
        
        app = create_app()
        
        with app.app_context():
            # Get cleanup age from config
            cleanup_hours = int(os.getenv('COOLIFY_AUTO_CLEANUP_HOURS', '24'))
            cutoff_time = datetime.utcnow() - timedelta(hours=cleanup_hours)
            
            logger.info(f"Starting cleanup of Coolify deployments older than {cleanup_hours} hours")
            
            # Find old deployments that haven't been cleaned yet
            old_deployments = CoolifyDeployment.query.filter(
                and_(
                    CoolifyDeployment.created_at < cutoff_time,
                    CoolifyDeployment.cleaned_at.is_(None),
                    CoolifyDeployment.status.notin_(['stopped'])
                )
            ).all()
            
            logger.info(f"Found {len(old_deployments)} deployments to clean up")
            
            coolify_service = get_coolify_service()
            cleaned_count = 0
            failed_count = 0
            
            for deployment in old_deployments:
                try:
                    logger.info(f"Cleaning up deployment {deployment.id} ({deployment.application_name})")
                    
                    # Delete from Coolify
                    coolify_service.delete_deployment(deployment.coolify_deployment_id)
                    
                    # Mark as cleaned
                    deployment.status = 'stopped'
                    deployment.cleaned_at = datetime.utcnow()
                    cleaned_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to cleanup deployment {deployment.id}: {str(e)}")
                    deployment.error_message = f"Cleanup failed: {str(e)}"
                    failed_count += 1
            
            # Commit all changes
            db.session.commit()
            
            logger.info(f"Cleanup complete: {cleaned_count} cleaned, {failed_count} failed")
            
            return {
                'success': True,
                'cleaned_count': cleaned_count,
                'failed_count': failed_count,
                'cutoff_time': cutoff_time.isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error in cleanup task: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@celery.task(name='app.tasks.poll_deployment_status')
def poll_deployment_status(deployment_id: int):
    """
    Background task to poll deployment status periodically
    
    Args:
        deployment_id: Database ID of the CoolifyDeployment
    """
    try:
        from app import create_app, db
        from app.models import CoolifyDeployment
        from app.services.coolify_integration import get_coolify_service
        
        app = create_app()
        
        with app.app_context():
            deployment = CoolifyDeployment.query.get(deployment_id)
            if not deployment:
                logger.warning(f"Deployment {deployment_id} not found")
                return {'success': False, 'error': 'Deployment not found'}
            
            # Don't poll if already in terminal state
            terminal_states = ['running', 'failed', 'stopped']
            if deployment.status in terminal_states:
                return {'success': True, 'status': deployment.status, 'message': 'Already in terminal state'}
            
            coolify_service = get_coolify_service()
            
            # Get current status
            status_result = coolify_service.get_deployment_status(deployment.coolify_deployment_id)
            
            # Update deployment record
            deployment.status = status_result['status']
            deployment.deployment_url = status_result.get('deployment_url') or deployment.deployment_url
            deployment.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Schedule next poll if not in terminal state
            if deployment.status not in terminal_states:
                poll_deployment_status.apply_async(args=[deployment_id], countdown=10)
            
            return {
                'success': True,
                'deployment_id': deployment_id,
                'status': deployment.status
            }
            
    except Exception as e:
        logger.error(f"Error polling deployment status: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == '__main__':
    celery.start()
