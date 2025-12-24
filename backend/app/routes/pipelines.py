from flask import Blueprint, request, jsonify, session
from ..models import User, Repository, Pipeline, db
from ..services.pipeline_generator import PipelineGenerator
from ..services.pipeline_runner import PipelineRunner
from ..services.gemini_service import GeminiService
from ..services.bitbucket_service import BitbucketService

bp = Blueprint('pipelines', __name__)


def get_current_user():
    """Get current authenticated user"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)


@bp.route('/generate', methods=['POST'])
def generate_pipeline():
    """Generate a pipeline configuration for a repository"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    repo_id = data.get('repository_id')
    deployment_server = data.get('deployment_server')
    
    if not repo_id:
        return jsonify({'error': 'repository_id is required'}), 400
    
    repository = Repository.query.filter_by(id=repo_id, user_id=user.id).first()
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
    
    try:
        # Generate initial pipeline configuration
        generator = PipelineGenerator()
        pipeline_config = generator.generate_deployment_pipeline(
            repo_name=repository.name,
            deployment_server=deployment_server
        )
        
        # Create pipeline record
        pipeline = Pipeline(
            repository_id=repository.id,
            version=1,
            config=pipeline_config,
            status='draft',
            deployment_server=deployment_server
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
                'status': pipeline.status
            }
        }), 201
        
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
        # Run pipeline in self-hosted runner
        runner = PipelineRunner()
        result = runner.run_pipeline(
            pipeline_config=pipeline.config,
            repository_url=pipeline.repository.bitbucket_repo_url
        )
        
        pipeline.status = 'success' if result['success'] else 'failed'
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
    
    if pipeline.status != 'failed':
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
            status='draft',
            deployment_server=pipeline.deployment_server
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


@bp.route('/create-pr', methods=['POST'])
def create_pull_request():
    """Create a pull request with the working pipeline configuration"""
    user = get_current_user()
    if not user or not user.bitbucket_token:
        return jsonify({'error': 'Not authenticated with Bitbucket'}), 401
    
    data = request.json
    pipeline_id = data.get('pipeline_id')
    
    if not pipeline_id:
        return jsonify({'error': 'pipeline_id is required'}), 400
    
    pipeline = Pipeline.query.get(pipeline_id)
    if not pipeline or pipeline.repository.user_id != user.id:
        return jsonify({'error': 'Pipeline not found'}), 404
    
    if pipeline.status != 'success':
        return jsonify({'error': 'Pipeline must be successful before creating PR'}), 400
    
    if pipeline.pr_created:
        return jsonify({'error': 'PR already created for this pipeline', 'pr_url': pipeline.pr_url}), 400
    
    try:
        bitbucket_service = BitbucketService(user.bitbucket_token)
        
        # Create branch and commit pipeline configuration
        pr_url = bitbucket_service.create_pipeline_pr(
            workspace=pipeline.repository.bitbucket_workspace,
            repo_slug=pipeline.repository.name,
            pipeline_config=pipeline.config,
            branch_name=f'add-pipeline-v{pipeline.version}'
        )
        
        pipeline.pr_created = True
        pipeline.pr_url = pr_url
        db.session.commit()
        
        return jsonify({
            'message': 'Pull request created successfully',
            'pr_url': pr_url
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
            'deployment_server': p.deployment_server,
            'pr_created': p.pr_created,
            'pr_url': p.pr_url,
            'created_at': p.created_at.isoformat() if p.created_at else None
        } for p in pipelines]
    }), 200


@bp.route('/<int:pipeline_id>', methods=['GET'])
def get_pipeline(pipeline_id):
    """Get pipeline details"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    pipeline = Pipeline.query.get(pipeline_id)
    if not pipeline or pipeline.repository.user_id != user.id:
        return jsonify({'error': 'Pipeline not found'}), 404
    
    return jsonify({
        'id': pipeline.id,
        'version': pipeline.version,
        'config': pipeline.config,
        'status': pipeline.status,
        'test_output': pipeline.test_output,
        'error_message': pipeline.error_message,
        'deployment_server': pipeline.deployment_server,
        'pr_created': pipeline.pr_created,
        'pr_url': pipeline.pr_url,
        'created_at': pipeline.created_at.isoformat() if pipeline.created_at else None,
        'updated_at': pipeline.updated_at.isoformat() if pipeline.updated_at else None
    }), 200
