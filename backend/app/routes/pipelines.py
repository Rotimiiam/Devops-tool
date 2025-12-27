from flask import Blueprint, request, jsonify, session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from ..models import User, Repository, Pipeline, PipelineExecution, db
from ..services.pipeline_generator import PipelineGenerator
from ..services.pipeline_runner import PipelineRunner
from ..services.gemini_service import GeminiService
from ..services.bitbucket_service import BitbucketService
from ..services.repository_analyzer import RepositoryAnalyzer

bp = Blueprint('pipelines', __name__)


def get_current_user():
    """Get current authenticated user"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)


@bp.route('', methods=['GET'])
def list_all_pipelines():
    """List all pipelines for the authenticated user with pagination"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status_filter = request.args.get('status')
    
    # Query pipelines through user's repositories
    query = Pipeline.query.join(Repository).filter(Repository.user_id == user.id)
    
    if status_filter:
        query = query.filter(Pipeline.status == status_filter)
    
    query = query.order_by(Pipeline.updated_at.desc())
    
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    pipelines = [{
        'id': p.id,
        'repository': {
            'id': p.repository.id,
            'name': p.repository.name,
            'source': p.repository.source
        },
        'version': p.version,
        'status': p.status,
        'is_active': p.is_active,
        'deployment_server': p.deployment_server,
        'subdomain': p.subdomain,
        'port': p.port,
        'server_ip': p.server_ip,
        'ssl_enabled': p.ssl_enabled,
        'pr_created': p.pr_created,
        'pr_url': p.pr_url,
        'last_execution_timestamp': p.last_execution_timestamp.isoformat() if p.last_execution_timestamp else None,
        'created_at': p.created_at.isoformat() if p.created_at else None,
        'updated_at': p.updated_at.isoformat() if p.updated_at else None
    } for p in paginated.items]
    
    return jsonify({
        'pipelines': pipelines,
        'pagination': {
            'page': paginated.page,
            'per_page': paginated.per_page,
            'total': paginated.total,
            'pages': paginated.pages,
            'has_next': paginated.has_next,
            'has_prev': paginated.has_prev
        }
    }), 200


@bp.route('/<int:pipeline_id>', methods=['GET'])
def get_pipeline_details(pipeline_id):
    """Get complete pipeline details including execution history"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    pipeline = Pipeline.query.get(pipeline_id)
    if not pipeline or pipeline.repository.user_id != user.id:
        return jsonify({'error': 'Pipeline not found'}), 404
    
    # Get execution history
    executions = PipelineExecution.query.filter_by(pipeline_id=pipeline.id)\
        .order_by(PipelineExecution.started_at.desc()).limit(10).all()
    
    execution_history = [{
        'id': ex.id,
        'status': ex.status,
        'trigger_type': ex.trigger_type,
        'bitbucket_build_number': ex.bitbucket_build_number,
        'started_at': ex.started_at.isoformat() if ex.started_at else None,
        'completed_at': ex.completed_at.isoformat() if ex.completed_at else None,
        'duration_seconds': ex.duration_seconds,
        'error_message': ex.error_message,
        'rolled_back': ex.rolled_back
    } for ex in executions]
    
    return jsonify({
        'id': pipeline.id,
        'repository': {
            'id': pipeline.repository.id,
            'name': pipeline.repository.name,
            'source': pipeline.repository.source,
            'bitbucket_workspace': pipeline.repository.bitbucket_workspace,
            'detected_languages': pipeline.repository.detected_languages,
            'detected_frameworks': pipeline.repository.detected_frameworks
        },
        'version': pipeline.version,
        'config': pipeline.config,
        'status': pipeline.status,
        'is_active': pipeline.is_active,
        'test_output': pipeline.test_output,
        'error_message': pipeline.error_message,
        'deployment_server': pipeline.deployment_server,
        'server_ip': pipeline.server_ip,
        'subdomain': pipeline.subdomain,
        'port': pipeline.port,
        'environment_variables': pipeline.environment_variables,
        'nginx_config': pipeline.nginx_config,
        'ssl_enabled': pipeline.ssl_enabled,
        'pr_created': pipeline.pr_created,
        'pr_url': pipeline.pr_url,
        'bitbucket_pipeline_uuid': pipeline.bitbucket_pipeline_uuid,
        'last_execution_timestamp': pipeline.last_execution_timestamp.isoformat() if pipeline.last_execution_timestamp else None,
        'created_at': pipeline.created_at.isoformat() if pipeline.created_at else None,
        'updated_at': pipeline.updated_at.isoformat() if pipeline.updated_at else None,
        'execution_history': execution_history
    }), 200


@bp.route('/<int:pipeline_id>', methods=['PUT'])
def update_pipeline(pipeline_id):
    """Update pipeline configuration"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    pipeline = Pipeline.query.get(pipeline_id)
    if not pipeline or pipeline.repository.user_id != user.id:
        return jsonify({'error': 'Pipeline not found'}), 404
    
    data = request.json
    
    try:
        # Validate and update configuration fields
        if 'subdomain' in data:
            pipeline.subdomain = data['subdomain']
        
        if 'port' in data:
            port = data['port']
            if not isinstance(port, int) or port < 1 or port > 65535:
                return jsonify({'error': 'Invalid port number'}), 400
            pipeline.port = port
        
        if 'server_ip' in data:
            pipeline.server_ip = data['server_ip']
        
        if 'deployment_server' in data:
            pipeline.deployment_server = data['deployment_server']
        
        if 'environment_variables' in data:
            env_vars = data['environment_variables']
            if not isinstance(env_vars, dict):
                return jsonify({'error': 'environment_variables must be a dictionary'}), 400
            pipeline.environment_variables = env_vars
        
        if 'ssl_enabled' in data:
            pipeline.ssl_enabled = data['ssl_enabled']
        
        # If config YAML is provided, validate it
        if 'config' in data:
            generator = PipelineGenerator()
            if not generator.validate_pipeline_yaml(data['config']):
                return jsonify({'error': 'Invalid YAML configuration'}), 400
            pipeline.config = data['config']
        
        # Regenerate nginx config if relevant fields changed
        if any(k in data for k in ['subdomain', 'port', 'ssl_enabled']):
            if pipeline.subdomain and pipeline.port:
                generator = PipelineGenerator()
                # Get domain from first available domain or use default
                domain = 'example.com'  # TODO: Get from user's domains
                pipeline.nginx_config = generator.generate_nginx_config(
                    subdomain=pipeline.subdomain,
                    domain=domain,
                    port=pipeline.port,
                    server_ip=pipeline.server_ip or '127.0.0.1',
                    ssl_enabled=pipeline.ssl_enabled
                )
        
        pipeline.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Pipeline updated successfully',
            'pipeline': {
                'id': pipeline.id,
                'subdomain': pipeline.subdomain,
                'port': pipeline.port,
                'server_ip': pipeline.server_ip,
                'deployment_server': pipeline.deployment_server,
                'environment_variables': pipeline.environment_variables,
                'ssl_enabled': pipeline.ssl_enabled,
                'nginx_config': pipeline.nginx_config,
                'updated_at': pipeline.updated_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:pipeline_id>', methods=['DELETE'])
def delete_pipeline(pipeline_id):
    """Delete a pipeline"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    pipeline = Pipeline.query.get(pipeline_id)
    if not pipeline or pipeline.repository.user_id != user.id:
        return jsonify({'error': 'Pipeline not found'}), 404
    
    cleanup_remote = request.args.get('cleanup_remote', 'false').lower() == 'true'
    
    try:
        # Optional: cleanup remote configurations
        if cleanup_remote and user.bitbucket_token and pipeline.repository.bitbucket_workspace:
            try:
                bitbucket_service = BitbucketService(user.bitbucket_token)
                # Could implement removal of bitbucket-pipelines.yml here
                # For now, just log that we would clean up
                pass
            except Exception as e:
                # Don't fail deletion if remote cleanup fails
                print(f"Warning: Remote cleanup failed: {str(e)}")
        
        db.session.delete(pipeline)
        db.session.commit()
        
        return jsonify({
            'message': 'Pipeline deleted successfully',
            'pipeline_id': pipeline_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:pipeline_id>/regenerate', methods=['POST'])
def regenerate_pipeline(pipeline_id):
    """Regenerate pipeline configuration based on latest repository analysis"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    pipeline = Pipeline.query.get(pipeline_id)
    if not pipeline or pipeline.repository.user_id != user.id:
        return jsonify({'error': 'Pipeline not found'}), 404
    
    repository = pipeline.repository
    
    try:
        # Re-analyze repository
        analyzer = RepositoryAnalyzer(
            clone_url=repository.bitbucket_repo_url or repository.source_repo_url,
            access_token=user.bitbucket_token or user.github_token
        )
        analysis_results = analyzer.analyze()
        
        # Update repository analysis
        repository.detected_languages = analysis_results['detected_languages']
        repository.detected_frameworks = analysis_results['detected_frameworks']
        repository.required_env_vars = analysis_results['required_env_vars']
        repository.analysis_confidence = analysis_results['analysis_confidence']
        repository.analysis_timestamp = datetime.utcnow()
        
        # Generate new pipeline configuration
        generator = PipelineGenerator()
        new_config = generator.generate_deployment_pipeline(
            repo_name=repository.name,
            deployment_server=pipeline.deployment_server,
            detected_frameworks=repository.detected_frameworks,
            detected_languages=repository.detected_languages,
            subdomain=pipeline.subdomain,
            port=pipeline.port,
            server_ip=pipeline.server_ip,
            environment_variables=pipeline.environment_variables
        )
        
        # Update pipeline with new configuration
        pipeline.config = new_config
        pipeline.version += 1
        pipeline.status = 'PLANNED'
        pipeline.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Pipeline regenerated successfully',
            'pipeline': {
                'id': pipeline.id,
                'version': pipeline.version,
                'config': pipeline.config,
                'status': pipeline.status,
                'updated_at': pipeline.updated_at.isoformat()
            },
            'analysis': {
                'languages': repository.detected_languages,
                'frameworks': repository.detected_frameworks,
                'confidence': repository.analysis_confidence
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:pipeline_id>/trigger', methods=['POST'])
def trigger_pipeline_execution(pipeline_id):
    """
    Manually trigger pipeline execution via Bitbucket API with retry mechanism
    
    Request body:
    {
        "branch": "main",  // optional, default: "main"
        "retry": true,     // optional, enable retry mechanism
        "max_retries": 3   // optional, default: 3
    }
    """
    user = get_current_user()
    if not user or not user.bitbucket_token:
        return jsonify({'error': 'Not authenticated with Bitbucket'}), 401
    
    pipeline = Pipeline.query.get(pipeline_id)
    if not pipeline or pipeline.repository.user_id != user.id:
        return jsonify({'error': 'Pipeline not found'}), 404
    
    repository = pipeline.repository
    
    if not repository.bitbucket_workspace or not repository.name:
        return jsonify({'error': 'Repository not configured for Bitbucket'}), 400
    
    data = request.json or {}
    branch = data.get('branch', 'main')
    enable_retry = data.get('retry', True)
    max_retries = data.get('max_retries', 3)
    
    bitbucket_service = BitbucketService(user.bitbucket_token)
    
    # Retry logic with exponential backoff
    import time
    retry_count = 0
    last_error = None
    
    while retry_count <= (max_retries if enable_retry else 0):
        try:
            # Trigger pipeline via Bitbucket API
            result = bitbucket_service.trigger_pipeline(
                workspace=repository.bitbucket_workspace,
                repo_slug=repository.name,
                branch=branch
            )
            
            # Create execution record
            execution = PipelineExecution(
                pipeline_id=pipeline.id,
                status='BUILDING',
                trigger_type='manual',
                bitbucket_build_number=result['build_number'],
                bitbucket_pipeline_uuid=result['uuid'],
                started_at=datetime.utcnow()
            )
            db.session.add(execution)
            
            # Update pipeline status
            pipeline.status = 'BUILDING'
            pipeline.bitbucket_pipeline_uuid = result['uuid']
            pipeline.last_execution_timestamp = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({
                'message': 'Pipeline triggered successfully',
                'execution': {
                    'id': execution.id,
                    'build_number': result['build_number'],
                    'uuid': result['uuid'],
                    'status': execution.status,
                    'started_at': execution.started_at.isoformat(),
                    'retry_count': retry_count
                }
            }), 200
            
        except Exception as e:
            last_error = str(e)
            retry_count += 1
            
            if retry_count <= max_retries and enable_retry:
                # Exponential backoff: 2^retry_count seconds
                wait_time = 2 ** retry_count
                print(f"Pipeline trigger failed (attempt {retry_count}/{max_retries + 1}). Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                # All retries exhausted or retry disabled
                db.session.rollback()
                
                # Log the failed attempt
                execution = PipelineExecution(
                    pipeline_id=pipeline.id,
                    status='FAILED',
                    trigger_type='manual',
                    error_message=f"Failed to trigger pipeline after {retry_count} attempts: {last_error}",
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow()
                )
                db.session.add(execution)
                
                pipeline.status = 'FAILED'
                pipeline.error_message = last_error
                
                try:
                    db.session.commit()
                except:
                    db.session.rollback()
                
                return jsonify({
                    'error': last_error,
                    'retry_count': retry_count - 1,
                    'message': f'Failed to trigger pipeline after {retry_count} attempts'
                }), 500
    
    # Should not reach here, but just in case
    return jsonify({'error': 'Unexpected error in pipeline trigger'}), 500


@bp.route('/<int:pipeline_id>/logs', methods=['GET'])
def get_pipeline_logs(pipeline_id):
    """
    Get pipeline execution logs from Bitbucket with filtering and pagination
    
    Query parameters:
    - execution_id: Specific execution ID (optional, uses latest if not provided)
    - page: Page number for pagination (default: 1)
    - per_page: Items per page (default: 10, max: 50)
    - status: Filter by execution status (BUILDING, TESTING, DEPLOYING, SUCCESS, FAILED)
    - from_date: Filter executions from date (ISO format)
    - to_date: Filter executions to date (ISO format)
    - step_filter: Filter logs by step name (partial match)
    """
    user = get_current_user()
    if not user or not user.bitbucket_token:
        return jsonify({'error': 'Not authenticated with Bitbucket'}), 401
    
    pipeline = Pipeline.query.get(pipeline_id)
    if not pipeline or pipeline.repository.user_id != user.id:
        return jsonify({'error': 'Pipeline not found'}), 404
    
    repository = pipeline.repository
    
    # Get query parameters
    execution_id = request.args.get('execution_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)
    status_filter = request.args.get('status')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    step_filter = request.args.get('step_filter', '').lower()
    
    if execution_id:
        # Get specific execution
        execution = PipelineExecution.query.get(execution_id)
        if not execution or execution.pipeline_id != pipeline.id:
            return jsonify({'error': 'Execution not found'}), 404
        
        executions = [execution]
        total_executions = 1
    else:
        # Build query for historical executions
        query = PipelineExecution.query.filter_by(pipeline_id=pipeline.id)
        
        # Apply filters
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        if from_date:
            try:
                from datetime import datetime as dt
                from_dt = dt.fromisoformat(from_date.replace('Z', '+00:00'))
                query = query.filter(PipelineExecution.started_at >= from_dt)
            except ValueError:
                return jsonify({'error': 'Invalid from_date format. Use ISO format.'}), 400
        
        if to_date:
            try:
                from datetime import datetime as dt
                to_dt = dt.fromisoformat(to_date.replace('Z', '+00:00'))
                query = query.filter(PipelineExecution.started_at <= to_dt)
            except ValueError:
                return jsonify({'error': 'Invalid to_date format. Use ISO format.'}), 400
        
        # Order by start time (newest first)
        query = query.order_by(PipelineExecution.started_at.desc())
        
        # Get total count
        total_executions = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        executions = query.limit(per_page).offset(offset).all()
    
    if not executions:
        return jsonify({'error': 'No executions found'}), 404
    
    # Process the first/selected execution
    execution = executions[0]
    
    try:
        bitbucket_service = BitbucketService(user.bitbucket_token)
        
        if execution.bitbucket_pipeline_uuid:
            # Get logs from Bitbucket
            logs_data = bitbucket_service.get_pipeline_logs(
                workspace=repository.bitbucket_workspace,
                repo_slug=repository.name,
                pipeline_uuid=execution.bitbucket_pipeline_uuid
            )
            
            # Update execution with latest data
            execution.status = logs_data['state']
            if logs_data.get('completed_on'):
                from datetime import datetime as dt
                execution.completed_at = dt.fromisoformat(logs_data['completed_on'].replace('Z', '+00:00'))
            execution.duration_seconds = logs_data.get('duration_in_seconds')
            
            # Filter steps if step_filter is provided
            steps = logs_data['steps']
            if step_filter:
                steps = [
                    step for step in steps 
                    if step_filter in step['name'].lower()
                ]
            
            # Store logs
            full_log = '\n\n'.join([
                f"=== {step['name']} ===\nStatus: {step['state']}\n{step['log'] or 'No log available'}"
                for step in logs_data['steps']
            ])
            execution.logs = full_log
            
            db.session.commit()
            
            # Build response
            response = {
                'execution': {
                    'id': execution.id,
                    'build_number': logs_data['build_number'],
                    'uuid': logs_data['uuid'],
                    'status': logs_data['state'],
                    'started_at': logs_data['created_on'],
                    'completed_at': logs_data.get('completed_on'),
                    'duration_seconds': logs_data.get('duration_in_seconds'),
                    'trigger_type': execution.trigger_type
                },
                'steps': steps
            }
            
            # Add pagination info if listing multiple executions
            if not execution_id:
                response['pagination'] = {
                    'page': page,
                    'per_page': per_page,
                    'total': total_executions,
                    'pages': (total_executions + per_page - 1) // per_page
                }
                
                # Add summary of all executions in current page
                response['executions_summary'] = [{
                    'id': ex.id,
                    'status': ex.status,
                    'build_number': ex.bitbucket_build_number,
                    'started_at': ex.started_at.isoformat() if ex.started_at else None,
                    'completed_at': ex.completed_at.isoformat() if ex.completed_at else None,
                    'duration_seconds': ex.duration_seconds,
                    'trigger_type': ex.trigger_type
                } for ex in executions]
            
            return jsonify(response), 200
        else:
            # Return stored logs if available
            response = {
                'execution': {
                    'id': execution.id,
                    'status': execution.status,
                    'started_at': execution.started_at.isoformat() if execution.started_at else None,
                    'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
                    'duration_seconds': execution.duration_seconds,
                    'trigger_type': execution.trigger_type
                },
                'logs': execution.logs or 'No logs available',
                'error_message': execution.error_message
            }
            
            if not execution_id:
                response['pagination'] = {
                    'page': page,
                    'per_page': per_page,
                    'total': total_executions,
                    'pages': (total_executions + per_page - 1) // per_page
                }
            
            return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:pipeline_id>/sync-env', methods=['POST'])
def sync_environment_variables(pipeline_id):
    """Sync environment variables to Bitbucket repository"""
    user = get_current_user()
    if not user or not user.bitbucket_token:
        return jsonify({'error': 'Not authenticated with Bitbucket'}), 401
    
    pipeline = Pipeline.query.get(pipeline_id)
    if not pipeline or pipeline.repository.user_id != user.id:
        return jsonify({'error': 'Pipeline not found'}), 404
    
    repository = pipeline.repository
    
    if not repository.bitbucket_workspace or not repository.name:
        return jsonify({'error': 'Repository not configured for Bitbucket'}), 400
    
    if not pipeline.environment_variables:
        return jsonify({'error': 'No environment variables to sync'}), 400
    
    try:
        bitbucket_service = BitbucketService(user.bitbucket_token)
        result = bitbucket_service.sync_environment_variables(
            workspace=repository.bitbucket_workspace,
            repo_slug=repository.name,
            environment_variables=pipeline.environment_variables
        )
        
        return jsonify({
            'message': 'Environment variables synced successfully',
            'synced': result['synced'],
            'errors': result['errors']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Keep existing endpoints from original file
@bp.route('/generate', methods=['POST'])
def generate_pipeline():
    """Generate a pipeline configuration for a repository"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    repo_id = data.get('repository_id')
    deployment_server = data.get('deployment_server')
    subdomain = data.get('subdomain')
    port = data.get('port', 8080)
    server_ip = data.get('server_ip')
    environment_variables = data.get('environment_variables', {})
    
    if not repo_id:
        return jsonify({'error': 'repository_id is required'}), 400
    
    repository = Repository.query.filter_by(id=repo_id, user_id=user.id).first()
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
    
    try:
        # Check for existing active pipeline (uniqueness constraint)
        existing_active = Pipeline.query.filter_by(
            repository_id=repository.id,
            is_active=True
        ).first()
        
        if existing_active:
            return jsonify({
                'error': 'An active pipeline already exists for this repository',
                'existing_pipeline_id': existing_active.id
            }), 409
        
        # Generate pipeline configuration
        generator = PipelineGenerator()
        pipeline_config = generator.generate_deployment_pipeline(
            repo_name=repository.name,
            deployment_server=deployment_server,
            detected_frameworks=repository.detected_frameworks,
            detected_languages=repository.detected_languages,
            subdomain=subdomain,
            port=port,
            server_ip=server_ip,
            environment_variables=environment_variables
        )
        
        # Generate nginx config if applicable
        nginx_config = None
        if subdomain and port:
            domain = 'example.com'  # TODO: Get from user's domains
            nginx_config = generator.generate_nginx_config(
                subdomain=subdomain,
                domain=domain,
                port=port,
                server_ip=server_ip or '127.0.0.1',
                ssl_enabled=True
            )
        
        # Create pipeline record
        pipeline = Pipeline(
            repository_id=repository.id,
            version=1,
            config=pipeline_config,
            status='PLANNED',
            is_active=True,
            deployment_server=deployment_server,
            subdomain=subdomain,
            port=port,
            server_ip=server_ip,
            environment_variables=environment_variables,
            nginx_config=nginx_config,
            ssl_enabled=True
        )
        db.session.add(pipeline)
        
        repository.status = 'pipeline_generated'
        db.session.commit()
        
        return jsonify({
            'message': 'Pipeline generated successfully',
            'pipeline': {
                'id': pipeline.id,
                'version': pipeline.version,
                'config': pipeline.config,
                'status': pipeline.status,
                'nginx_config': pipeline.nginx_config
            }
        }), 201
        
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({'error': 'An active pipeline already exists for this repository'}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/test', methods=['POST'])
def test_pipeline():
    """Test a pipeline configuration"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    pipeline_id = data.get('pipeline_id')
    
    if not pipeline_id:
        return jsonify({'error': 'pipeline_id is required'}), 400
    
    pipeline = Pipeline.query.get(pipeline_id)
    if not pipeline or pipeline.repository.user_id != user.id:
        return jsonify({'error': 'Pipeline not found'}), 404
    
    try:
        pipeline.status = 'TESTING'
        db.session.commit()
        
        # Run pipeline in self-hosted runner
        runner = PipelineRunner()
        result = runner.run_pipeline(
            pipeline_config=pipeline.config,
            repository_url=pipeline.repository.bitbucket_repo_url
        )
        
        pipeline.status = 'SUCCESS' if result['success'] else 'FAILED'
        pipeline.test_output = result['output']
        pipeline.error_message = result.get('error')
        
        if result['success']:
            pipeline.repository.status = 'completed'
        else:
            pipeline.repository.status = 'pipeline_testing'
        
        db.session.commit()
        
        return jsonify({
            'message': 'Pipeline test completed',
            'result': {
                'success': result['success'],
                'output': result['output'],
                'error': result.get('error')
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        pipeline.status = 'FAILED'
        pipeline.error_message = str(e)
        db.session.commit()
        return jsonify({'error': str(e)}), 500


@bp.route('/iterate', methods=['POST'])
def iterate_pipeline():
    """Use Gemini to iterate and fix a failed pipeline"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if not user.gemini_api_key:
        return jsonify({'error': 'Gemini API key not configured'}), 400
    
    data = request.json
    pipeline_id = data.get('pipeline_id')
    
    if not pipeline_id:
        return jsonify({'error': 'pipeline_id is required'}), 400
    
    pipeline = Pipeline.query.get(pipeline_id)
    if not pipeline or pipeline.repository.user_id != user.id:
        return jsonify({'error': 'Pipeline not found'}), 404
    
    if pipeline.status not in ['FAILED', 'failed']:
        return jsonify({'error': 'Pipeline must be in failed state to iterate'}), 400
    
    try:
        # Use Gemini to analyze and fix the pipeline
        gemini_service = GeminiService(user.gemini_api_key)
        new_config = gemini_service.fix_pipeline(
            current_config=pipeline.config,
            error_output=pipeline.test_output,
            error_message=pipeline.error_message
        )
        
        # Create new pipeline version
        new_version = pipeline.version + 1
        new_pipeline = Pipeline(
            repository_id=pipeline.repository_id,
            version=new_version,
            config=new_config,
            status='PLANNED',
            is_active=False,
            deployment_server=pipeline.deployment_server,
            subdomain=pipeline.subdomain,
            port=pipeline.port,
            server_ip=pipeline.server_ip,
            environment_variables=pipeline.environment_variables,
            nginx_config=pipeline.nginx_config,
            ssl_enabled=pipeline.ssl_enabled
        )
        db.session.add(new_pipeline)
        db.session.commit()
        
        return jsonify({
            'message': 'New pipeline version created',
            'pipeline': {
                'id': new_pipeline.id,
                'version': new_pipeline.version,
                'config': new_pipeline.config,
                'status': new_pipeline.status
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:pipeline_id>/create-pr', methods=['POST'])
def create_pull_request(pipeline_id):
    """
    Create a pull request with the working pipeline configuration
    
    Request body:
    {
        "title": "Custom PR title",  // optional
        "description": "Custom description",  // optional
        "branch_name": "custom-branch-name",  // optional
        "include_nginx_config": true  // optional, default: false
    }
    """
    user = get_current_user()
    if not user or not user.bitbucket_token:
        return jsonify({'error': 'Not authenticated with Bitbucket'}), 401
    
    data = request.json or {}
    
    pipeline = Pipeline.query.get(pipeline_id)
    if not pipeline or pipeline.repository.user_id != user.id:
        return jsonify({'error': 'Pipeline not found'}), 404
    
    if pipeline.status not in ['SUCCESS', 'success']:
        return jsonify({'error': 'Pipeline must be successful before creating PR'}), 400
    
    if pipeline.pr_created:
        return jsonify({'error': 'PR already created for this pipeline', 'pr_url': pipeline.pr_url}), 400
    
    repository = pipeline.repository
    
    try:
        # Generate commit message based on pipeline configuration
        detected_techs = []
        if repository.detected_languages:
            langs = ', '.join(repository.detected_languages.keys())
            detected_techs.append(f"Languages: {langs}")
        if repository.detected_frameworks:
            frameworks = ', '.join(repository.detected_frameworks.keys())
            detected_techs.append(f"Frameworks: {frameworks}")
        
        tech_summary = ' | '.join(detected_techs) if detected_techs else 'Multiple technologies'
        
        # Build commit message
        commit_message = data.get('commit_message', 
            f"""Add automated CI/CD pipeline configuration

Pipeline Version: {pipeline.version}
Status: {pipeline.status}
Technologies: {tech_summary}

This pipeline configuration was automatically generated and tested.
"""
        )
        
        # Build PR title
        pr_title = data.get('title',
            f"Add CI/CD Pipeline Configuration (v{pipeline.version}) - {tech_summary}"
        )
        
        # Build detailed PR description
        config_details = []
        if pipeline.deployment_server:
            config_details.append(f"- **Deployment Server**: {pipeline.deployment_server}")
        if pipeline.subdomain:
            config_details.append(f"- **Subdomain**: {pipeline.subdomain}")
        if pipeline.port:
            config_details.append(f"- **Port**: {pipeline.port}")
        if pipeline.server_ip:
            config_details.append(f"- **Server IP**: {pipeline.server_ip}")
        if pipeline.ssl_enabled:
            config_details.append(f"- **SSL**: Enabled")
        if pipeline.environment_variables:
            env_count = len(pipeline.environment_variables)
            config_details.append(f"- **Environment Variables**: {env_count} configured")
        
        config_summary = '\n'.join(config_details) if config_details else 'Standard configuration'
        
        execution_history = PipelineExecution.query.filter_by(
            pipeline_id=pipeline.id
        ).order_by(PipelineExecution.started_at.desc()).limit(5).all()
        
        execution_summary = ""
        if execution_history:
            execution_summary = "\n\n## Test Execution History\n\n"
            for ex in execution_history:
                status_emoji = "✅" if ex.status in ['SUCCESS', 'COMPLETED'] else "❌"
                execution_summary += f"- {status_emoji} Build #{ex.bitbucket_build_number or 'N/A'} - {ex.status} "
                if ex.duration_seconds:
                    execution_summary += f"({ex.duration_seconds}s)"
                execution_summary += f" - {ex.started_at.strftime('%Y-%m-%d %H:%M:%S') if ex.started_at else 'N/A'}\n"
        
        pr_description = data.get('description',
            f"""## Automated CI/CD Pipeline Configuration

This pull request adds a fully tested Bitbucket Pipelines configuration for automated CI/CD.

### Pipeline Details

**Version**: {pipeline.version}
**Status**: {pipeline.status}
**Generated**: {pipeline.created_at.strftime('%Y-%m-%d %H:%M:%S') if pipeline.created_at else 'N/A'}
**Last Updated**: {pipeline.updated_at.strftime('%Y-%m-%d %H:%M:%S') if pipeline.updated_at else 'N/A'}

### Detected Technologies

{tech_summary}

### Deployment Configuration

{config_summary}
{execution_summary}

### What's Included

- ✅ Automated build and test steps
- ✅ Deployment to configured server
- ✅ Environment variable configuration
{"- ✅ Nginx reverse proxy configuration" if pipeline.nginx_config and data.get('include_nginx_config') else ""}

### Next Steps

1. Review the pipeline configuration
2. Merge this PR to enable automated deployments
3. Configure any additional environment variables in Bitbucket repository settings
4. Monitor the first deployment run

---

*This PR was automatically generated and tested by the DevOps Tool.*
"""
        )
        
        bitbucket_service = BitbucketService(user.bitbucket_token)
        
        # Custom branch name or default
        branch_name = data.get('branch_name', f'pipeline-v{pipeline.version}-{int(datetime.utcnow().timestamp())}')
        
        # Create branch and commit pipeline configuration
        pr_url = bitbucket_service.create_pipeline_pr(
            workspace=repository.bitbucket_workspace,
            repo_slug=repository.name,
            pipeline_config=pipeline.config,
            branch_name=branch_name,
            commit_message=commit_message,
            pr_title=pr_title,
            pr_description=pr_description
        )
        
        pipeline.pr_created = True
        pipeline.pr_url = pr_url
        db.session.commit()
        
        return jsonify({
            'message': 'Pull request created successfully',
            'pr_url': pr_url,
            'branch_name': branch_name,
            'pr_title': pr_title
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/repository/<int:repo_id>', methods=['GET'])
def list_pipelines(repo_id):
    """List all pipelines for a repository"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    repository = Repository.query.filter_by(id=repo_id, user_id=user.id).first()
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
    
    pipelines = Pipeline.query.filter_by(repository_id=repo_id).order_by(Pipeline.version.desc()).all()
    
    return jsonify({
        'pipelines': [{
            'id': p.id,
            'version': p.version,
            'status': p.status,
            'is_active': p.is_active,
            'deployment_server': p.deployment_server,
            'subdomain': p.subdomain,
            'port': p.port,
            'pr_created': p.pr_created,
            'pr_url': p.pr_url,
            'created_at': p.created_at.isoformat() if p.created_at else None
        } for p in pipelines]
    }), 200
