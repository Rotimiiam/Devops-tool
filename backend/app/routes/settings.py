from flask import Blueprint, request, jsonify, session
from ..models import User, db

bp = Blueprint('settings', __name__)


def get_current_user():
    """Get current authenticated user"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)


@bp.route('/', methods=['GET'])
def get_settings():
    """Get user settings"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    return jsonify({
        'gemini_api_key_configured': bool(user.gemini_api_key),
        'bitbucket_connected': bool(user.bitbucket_token),
        'github_connected': bool(user.github_token)
    }), 200


@bp.route('/gemini-api-key', methods=['POST'])
def update_gemini_api_key():
    """Update Gemini API key"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    api_key = data.get('api_key')
    
    if not api_key:
        return jsonify({'error': 'api_key is required'}), 400
    
    try:
        user.gemini_api_key = api_key
        db.session.commit()
        
        return jsonify({'message': 'Gemini API key updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/gemini-api-key', methods=['DELETE'])
def delete_gemini_api_key():
    """Remove Gemini API key"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user.gemini_api_key = None
        db.session.commit()
        
        return jsonify({'message': 'Gemini API key removed successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
