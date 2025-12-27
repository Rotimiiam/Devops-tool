"""
Coolify Integration Service
Handles all interactions with Coolify REST API for test deployment management
"""
import requests
import os
import time
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CoolifyAPIException(Exception):
    """Custom exception for Coolify API errors"""
    pass


class CoolifyIntegrationService:
    """Service for integrating with Coolify deployment platform"""
    
    def __init__(self, base_url: str = None, api_token: str = None):
        """
        Initialize Coolify integration service
        
        Args:
            base_url: Base URL for Coolify API (default: http://coolify:9000)
            api_token: API token for Coolify authentication
        """
        self.base_url = base_url or os.getenv('COOLIFY_BASE_URL', 'http://coolify:9000')
        self.api_token = api_token or os.getenv('COOLIFY_API_TOKEN', '')
        self.api_url = f"{self.base_url}/api/v1"
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.max_retries = 3
        self.retry_delay = 2  # seconds
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, 
                     params: Dict = None, retry_count: int = 0) -> Dict:
        """
        Make HTTP request to Coolify API with retry mechanism
        
        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint path
            data: Request payload
            params: Query parameters
            retry_count: Current retry attempt
            
        Returns:
            Response data as dictionary
            
        Raises:
            CoolifyAPIException: If request fails after all retries
        """
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params,
                timeout=30
            )
            
            response.raise_for_status()
            
            # Handle empty responses
            if response.status_code == 204 or not response.content:
                return {'success': True}
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Coolify API request failed: {str(e)}")
            
            # Retry logic
            if retry_count < self.max_retries:
                logger.info(f"Retrying request (attempt {retry_count + 1}/{self.max_retries})")
                time.sleep(self.retry_delay * (retry_count + 1))
                return self._make_request(method, endpoint, data, params, retry_count + 1)
            
            raise CoolifyAPIException(f"Coolify API request failed: {str(e)}")
    
    def check_health(self) -> Dict:
        """
        Check Coolify service health and availability
        
        Returns:
            Dictionary with health status
        """
        try:
            response = self._make_request('GET', '/health')
            return {
                'available': True,
                'status': 'healthy',
                'version': response.get('version', 'unknown'),
                'message': 'Coolify service is available'
            }
        except Exception as e:
            logger.error(f"Coolify health check failed: {str(e)}")
            return {
                'available': False,
                'status': 'unhealthy',
                'error': str(e),
                'message': 'Coolify service is not available'
            }
    
    def create_deployment(self, application_name: str, config: Dict) -> Dict:
        """
        Create a new test deployment in Coolify
        
        Args:
            application_name: Name for the deployment application
            config: Deployment configuration including:
                - docker_image: Docker image to deploy (optional)
                - dockerfile_path: Path to Dockerfile (optional)
                - git_repository: Git repository URL (optional)
                - git_branch: Git branch to deploy (optional)
                - environment_variables: Dict of environment variables
                - port_mappings: List of port mappings
                - build_pack: Build pack to use (dockerfile, docker, nixpacks, etc.)
                
        Returns:
            Dictionary with deployment details including deployment_id
        """
        try:
            # Prepare deployment payload
            payload = {
                'name': application_name,
                'type': 'application',
                'build_pack': config.get('build_pack', 'dockerfile'),
                'ports_exposes': ','.join([str(p['container_port']) for p in config.get('port_mappings', [{'container_port': 3000}])]),
                'environment_variables': config.get('environment_variables', {}),
                'instant_deploy': False  # Don't auto-deploy, wait for manual trigger
            }
            
            # Add Docker image if provided
            if config.get('docker_image'):
                payload['docker_image'] = config['docker_image']
                payload['build_pack'] = 'docker'
            
            # Add Dockerfile path if provided
            if config.get('dockerfile_path'):
                payload['dockerfile_location'] = config['dockerfile_path']
            
            # Add Git repository if provided
            if config.get('git_repository'):
                payload['git_repository'] = config['git_repository']
                payload['git_branch'] = config.get('git_branch', 'main')
            
            # Create application in Coolify
            response = self._make_request('POST', '/applications', data=payload)
            
            deployment_id = response.get('uuid') or response.get('id')
            
            return {
                'success': True,
                'deployment_id': deployment_id,
                'application_id': response.get('id'),
                'application_name': application_name,
                'status': 'pending',
                'deployment_url': response.get('url'),
                'created_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create deployment: {str(e)}")
            raise CoolifyAPIException(f"Failed to create deployment: {str(e)}")
    
    def get_deployment_status(self, deployment_id: str) -> Dict:
        """
        Get current status of a deployment
        
        Args:
            deployment_id: Coolify deployment/application UUID
            
        Returns:
            Dictionary with deployment status details
        """
        try:
            response = self._make_request('GET', f'/applications/{deployment_id}')
            
            # Map Coolify status to our status
            coolify_status = response.get('status', 'unknown')
            status_mapping = {
                'starting': 'building',
                'restarting': 'deploying',
                'running': 'running',
                'exited': 'failed',
                'stopped': 'stopped',
                'created': 'pending'
            }
            
            status = status_mapping.get(coolify_status.lower(), coolify_status)
            
            return {
                'deployment_id': deployment_id,
                'status': status,
                'coolify_status': coolify_status,
                'health_status': response.get('health_status'),
                'deployment_url': response.get('fqdn'),
                'updated_at': response.get('updated_at', datetime.utcnow().isoformat())
            }
            
        except Exception as e:
            logger.error(f"Failed to get deployment status: {str(e)}")
            raise CoolifyAPIException(f"Failed to get deployment status: {str(e)}")
    
    def get_deployment_logs(self, deployment_id: str, log_type: str = 'combined') -> Dict:
        """
        Get build and runtime logs for a deployment
        
        Args:
            deployment_id: Coolify deployment/application UUID
            log_type: Type of logs to retrieve (build, runtime, or combined)
            
        Returns:
            Dictionary with logs
        """
        try:
            logs = {
                'deployment_id': deployment_id,
                'log_type': log_type,
                'build_logs': '',
                'runtime_logs': '',
                'combined_logs': ''
            }
            
            # Get build logs
            if log_type in ['build', 'combined']:
                try:
                    build_response = self._make_request('GET', f'/applications/{deployment_id}/logs/build')
                    logs['build_logs'] = build_response.get('logs', '')
                except:
                    logs['build_logs'] = 'Build logs not available'
            
            # Get runtime logs
            if log_type in ['runtime', 'combined']:
                try:
                    runtime_response = self._make_request('GET', f'/applications/{deployment_id}/logs/container')
                    logs['runtime_logs'] = runtime_response.get('logs', '')
                except:
                    logs['runtime_logs'] = 'Runtime logs not available'
            
            # Combine logs
            if log_type == 'combined':
                logs['combined_logs'] = f"=== BUILD LOGS ===\n{logs['build_logs']}\n\n=== RUNTIME LOGS ===\n{logs['runtime_logs']}"
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get deployment logs: {str(e)}")
            raise CoolifyAPIException(f"Failed to get deployment logs: {str(e)}")
    
    def start_deployment(self, deployment_id: str) -> Dict:
        """
        Start/trigger a deployment
        
        Args:
            deployment_id: Coolify deployment/application UUID
            
        Returns:
            Dictionary with deployment trigger result
        """
        try:
            response = self._make_request('POST', f'/applications/{deployment_id}/deploy')
            
            return {
                'success': True,
                'deployment_id': deployment_id,
                'status': 'building',
                'message': 'Deployment started successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to start deployment: {str(e)}")
            raise CoolifyAPIException(f"Failed to start deployment: {str(e)}")
    
    def stop_deployment(self, deployment_id: str) -> Dict:
        """
        Stop a running deployment
        
        Args:
            deployment_id: Coolify deployment/application UUID
            
        Returns:
            Dictionary with stop result
        """
        try:
            response = self._make_request('POST', f'/applications/{deployment_id}/stop')
            
            return {
                'success': True,
                'deployment_id': deployment_id,
                'status': 'stopped',
                'message': 'Deployment stopped successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to stop deployment: {str(e)}")
            raise CoolifyAPIException(f"Failed to stop deployment: {str(e)}")
    
    def delete_deployment(self, deployment_id: str) -> Dict:
        """
        Delete a deployment from Coolify
        
        Args:
            deployment_id: Coolify deployment/application UUID
            
        Returns:
            Dictionary with deletion result
        """
        try:
            # First stop the deployment
            try:
                self.stop_deployment(deployment_id)
                time.sleep(2)  # Wait for graceful shutdown
            except:
                pass  # Continue even if stop fails
            
            # Delete the application
            response = self._make_request('DELETE', f'/applications/{deployment_id}')
            
            return {
                'success': True,
                'deployment_id': deployment_id,
                'message': 'Deployment deleted successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to delete deployment: {str(e)}")
            raise CoolifyAPIException(f"Failed to delete deployment: {str(e)}")
    
    def list_deployments(self, filters: Dict = None) -> List[Dict]:
        """
        List all deployments with optional filters
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            List of deployment dictionaries
        """
        try:
            response = self._make_request('GET', '/applications', params=filters)
            
            applications = response.get('data', []) if isinstance(response, dict) else response
            
            deployments = []
            for app in applications:
                deployments.append({
                    'deployment_id': app.get('uuid') or app.get('id'),
                    'application_id': app.get('id'),
                    'name': app.get('name'),
                    'status': app.get('status'),
                    'deployment_url': app.get('fqdn'),
                    'created_at': app.get('created_at'),
                    'updated_at': app.get('updated_at')
                })
            
            return deployments
            
        except Exception as e:
            logger.error(f"Failed to list deployments: {str(e)}")
            raise CoolifyAPIException(f"Failed to list deployments: {str(e)}")
    
    def poll_deployment_status(self, deployment_id: str, interval: int = 10, 
                              max_duration: int = 600) -> Dict:
        """
        Poll deployment status until it reaches a terminal state
        
        Args:
            deployment_id: Coolify deployment/application UUID
            interval: Polling interval in seconds
            max_duration: Maximum time to poll in seconds
            
        Returns:
            Dictionary with final deployment status
        """
        start_time = time.time()
        terminal_states = ['running', 'failed', 'stopped']
        
        while (time.time() - start_time) < max_duration:
            try:
                status = self.get_deployment_status(deployment_id)
                
                if status['status'] in terminal_states:
                    return status
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error polling deployment status: {str(e)}")
                time.sleep(interval)
        
        # Timeout reached
        return {
            'deployment_id': deployment_id,
            'status': 'timeout',
            'error': f'Deployment status polling timed out after {max_duration} seconds'
        }


# Singleton instance
_coolify_service = None


def get_coolify_service() -> CoolifyIntegrationService:
    """Get or create Coolify service singleton instance"""
    global _coolify_service
    if _coolify_service is None:
        _coolify_service = CoolifyIntegrationService()
    return _coolify_service
