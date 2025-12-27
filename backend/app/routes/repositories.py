from flask import Blueprint, request, jsonify, session
from datetime import datetime
from ..models import User, Repository, db
from ..services.github_service import GitHubService
from ..services.bitbucket_service import BitbucketService
from ..services.repository_analyzer import RepositoryAnalyzer
from ..services.gemini_service import GeminiService

bp = Blueprint('repositories', __name__)


def get_current_user():
    """Get current authenticated user"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)


@bp.route('/github', methods=['GET'])
def list_github_repos():
    """List user's GitHub repositories"""
    user = get_current_user()
    if not user or not user.github_token:
        return jsonify({'error': 'Not authenticated with GitHub'}), 401
    
    try:
        github_service = GitHubService(user.github_token)
        repos = github_service.list_repositories()
        return jsonify({'repositories': repos}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/bitbucket', methods=['GET'])
def list_bitbucket_repos():
    """List user's Bitbucket repositories"""
    user = get_current_user()
    if not user or not user.bitbucket_token:
        return jsonify({'error': 'Not authenticated with Bitbucket'}), 401
    
    try:
        bitbucket_service = BitbucketService(user.bitbucket_token)
        repos = bitbucket_service.list_repositories()
        return jsonify({'repositories': repos}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/migrate', methods=['POST'])
def migrate_repository():
    """Migrate a GitHub repository to Bitbucket"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if not user.github_token or not user.bitbucket_token:
        return jsonify({'error': 'Both GitHub and Bitbucket must be connected'}), 400
    
    data = request.json
    repo_name = data.get('repo_name')
    source = data.get('source', 'github')
    workspace = data.get('workspace')
    
    if not repo_name:
        return jsonify({'error': 'repo_name is required'}), 400
    
    try:
        github_service = GitHubService(user.github_token)
        bitbucket_service = BitbucketService(user.bitbucket_token)
        
        if source == 'github':
            # Get GitHub repo details
            github_repo = github_service.get_repository(repo_name)
            
            # Create repository in Bitbucket
            bitbucket_repo = bitbucket_service.create_repository(
                repo_name=github_repo['name'],
                description=github_repo.get('description', ''),
                is_private=github_repo.get('private', False),
                workspace=workspace
            )
            
            # Clone and push (in background task ideally)
            clone_url = github_repo['clone_url']
            bitbucket_service.mirror_repository(clone_url, bitbucket_repo['links']['clone'][1]['href'])
            
            # Save to database
            repository = Repository(
                user_id=user.id,
                name=repo_name,
                source='github',
                source_repo_id=github_repo['id'],
                source_repo_url=github_repo['html_url'],
                bitbucket_repo_id=bitbucket_repo['uuid'],
                bitbucket_repo_url=bitbucket_repo['links']['html']['href'],
                bitbucket_workspace=workspace or bitbucket_repo['workspace']['slug'],
                status='migrated'
            )
            db.session.add(repository)
            db.session.commit()
            
            return jsonify({
                'message': 'Repository migrated successfully',
                'repository': {
                    'id': repository.id,
                    'name': repository.name,
                    'bitbucket_url': repository.bitbucket_repo_url
                }
            }), 201
        else:
            return jsonify({'error': 'Only GitHub to Bitbucket migration is supported'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/', methods=['GET'])
def list_repositories():
    """List all repositories for the current user"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    repositories = Repository.query.filter_by(user_id=user.id).all()
    
    repo_list = []
    for repo in repositories:
        repo_data = {
            'id': repo.id,
            'name': repo.name,
            'source': repo.source,
            'source_url': repo.source_repo_url,
            'bitbucket_url': repo.bitbucket_repo_url,
            'status': repo.status,
            'created_at': repo.created_at.isoformat() if repo.created_at else None,
            'updated_at': repo.updated_at.isoformat() if repo.updated_at else None,
            'has_analysis': repo.analysis_timestamp is not None,
            'analysis_confidence': repo.analysis_confidence if repo.analysis_timestamp else None
        }
        repo_list.append(repo_data)
    
    return jsonify({'repositories': repo_list}), 200


@bp.route('/<int:repo_id>', methods=['GET'])
def get_repository(repo_id):
    """Get repository details"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    repository = Repository.query.filter_by(id=repo_id, user_id=user.id).first()
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
    
    repo_data = {
        'id': repository.id,
        'name': repository.name,
        'source': repository.source,
        'source_url': repository.source_repo_url,
        'bitbucket_url': repository.bitbucket_repo_url,
        'bitbucket_workspace': repository.bitbucket_workspace,
        'status': repository.status,
        'created_at': repository.created_at.isoformat() if repository.created_at else None,
        'updated_at': repository.updated_at.isoformat() if repository.updated_at else None,
    }
    
    # Include analysis data if available
    if repository.analysis_timestamp:
        repo_data['analysis'] = {
            'detected_languages': repository.detected_languages,
            'detected_frameworks': repository.detected_frameworks,
            'required_env_vars': repository.required_env_vars,
            'analysis_confidence': repository.analysis_confidence,
            'analysis_timestamp': repository.analysis_timestamp.isoformat(),
            'ai_recommendations': repository.ai_recommendations
        }
    
    return jsonify(repo_data), 200


@bp.route('/<int:repo_id>', methods=['DELETE'])
def delete_repository(repo_id):
    """Delete repository record"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    repository = Repository.query.filter_by(id=repo_id, user_id=user.id).first()
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
    
    db.session.delete(repository)
    db.session.commit()
    
    return jsonify({'message': 'Repository deleted successfully'}), 200


@bp.route('/<int:repo_id>/analyze', methods=['POST'])
def analyze_repository(repo_id):
    """Trigger comprehensive analysis for a specific repository"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    repository = Repository.query.filter_by(id=repo_id, user_id=user.id).first()
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
    
    # Determine which URL to use for cloning
    clone_url = repository.source_repo_url
    access_token = None
    
    if repository.source == 'github' and user.github_token:
        # Convert HTML URL to clone URL if needed
        if clone_url and 'github.com' in clone_url:
            if not clone_url.endswith('.git'):
                clone_url = clone_url.replace('github.com/', 'github.com/') + '.git'
            if clone_url.startswith('http'):
                clone_url = clone_url.replace('http://', 'https://')
        access_token = user.github_token
    elif repository.source == 'bitbucket' and user.bitbucket_token:
        # Use Bitbucket clone URL
        clone_url = repository.bitbucket_repo_url
        access_token = user.bitbucket_token
    
    if not clone_url:
        return jsonify({'error': 'Repository URL not available'}), 400
    
    try:
        # Initialize analyzer
        analyzer = RepositoryAnalyzer(clone_url, access_token)
        
        # Perform analysis
        analysis_results = analyzer.analyze()
        
        # Generate AI recommendations if Gemini API key is available
        ai_recommendations = None
        if user.gemini_api_key:
            try:
                gemini_service = GeminiService(user.gemini_api_key)
                ai_recommendations = analyzer.generate_ai_recommendations(
                    analysis_results, gemini_service
                )
            except Exception as e:
                # Continue without AI recommendations if Gemini fails
                print(f"Warning: AI recommendations generation failed: {str(e)}")
        
        # Update repository with analysis results
        repository.detected_languages = analysis_results.get('detected_languages')
        repository.detected_frameworks = analysis_results.get('detected_frameworks')
        repository.required_env_vars = analysis_results.get('required_env_vars')
        repository.analysis_confidence = analysis_results.get('analysis_confidence')
        repository.analysis_timestamp = datetime.utcnow()
        repository.ai_recommendations = ai_recommendations
        
        db.session.commit()
        
        return jsonify({
            'message': 'Repository analysis completed successfully',
            'analysis': {
                'detected_languages': repository.detected_languages,
                'detected_frameworks': repository.detected_frameworks,
                'required_env_vars': repository.required_env_vars,
                'analysis_confidence': repository.analysis_confidence,
                'analysis_timestamp': repository.analysis_timestamp.isoformat() if repository.analysis_timestamp else None,
                'ai_recommendations': repository.ai_recommendations,
                'file_count': analysis_results.get('file_count'),
                'total_size': analysis_results.get('total_size')
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Repository analysis failed',
            'details': str(e)
        }), 500


@bp.route('/<int:repo_id>/analysis', methods=['GET'])
def get_repository_analysis(repo_id):
    """Retrieve stored analysis results for a specific repository"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    repository = Repository.query.filter_by(id=repo_id, user_id=user.id).first()
    if not repository:
        return jsonify({'error': 'Repository not found'}), 404
    
    # Check if analysis has been performed
    if not repository.analysis_timestamp:
        return jsonify({
            'message': 'No analysis available for this repository',
            'analysis_performed': False
        }), 200
    
    return jsonify({
        'analysis_performed': True,
        'analysis': {
            'detected_languages': repository.detected_languages,
            'detected_frameworks': repository.detected_frameworks,
            'required_env_vars': repository.required_env_vars,
            'analysis_confidence': repository.analysis_confidence,
            'analysis_timestamp': repository.analysis_timestamp.isoformat() if repository.analysis_timestamp else None,
            'ai_recommendations': repository.ai_recommendations
        }
    }), 200

