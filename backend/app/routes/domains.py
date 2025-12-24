from flask import Blueprint, request, jsonify, session
from ..models import User, Domain, db

bp = Blueprint('domains', __name__)


def get_current_user():
    """Get current authenticated user"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)


@bp.route('/', methods=['GET'])
def list_domains():
    """List all domains for the current user"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    domains = Domain.query.filter_by(user_id=user.id).all()
    
    return jsonify({
        'domains': [{
            'id': domain.id,
            'name': domain.name,
            'is_root': domain.is_root,
            'parent_domain_id': domain.parent_domain_id,
            'description': domain.description,
            'active': domain.active,
            'created_at': domain.created_at.isoformat() if domain.created_at else None
        } for domain in domains]
    }), 200


@bp.route('/', methods=['POST'])
def create_domain():
    """Create a new domain or subdomain"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    name = data.get('name')
    is_root = data.get('is_root', False)
    parent_domain_id = data.get('parent_domain_id')
    description = data.get('description', '')
    
    if not name:
        return jsonify({'error': 'name is required'}), 400
    
    # Validate root domain logic
    if is_root:
        existing_root = Domain.query.filter_by(user_id=user.id, is_root=True).first()
        if existing_root:
            return jsonify({'error': 'Root domain already exists'}), 400
    
    # Validate parent domain
    if parent_domain_id:
        parent = Domain.query.filter_by(id=parent_domain_id, user_id=user.id).first()
        if not parent:
            return jsonify({'error': 'Parent domain not found'}), 404
    
    try:
        domain = Domain(
            user_id=user.id,
            name=name,
            is_root=is_root,
            parent_domain_id=parent_domain_id,
            description=description,
            active=True
        )
        db.session.add(domain)
        db.session.commit()
        
        return jsonify({
            'message': 'Domain created successfully',
            'domain': {
                'id': domain.id,
                'name': domain.name,
                'is_root': domain.is_root,
                'parent_domain_id': domain.parent_domain_id,
                'description': domain.description,
                'active': domain.active
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:domain_id>', methods=['GET'])
def get_domain(domain_id):
    """Get domain details including subdomains"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    domain = Domain.query.filter_by(id=domain_id, user_id=user.id).first()
    if not domain:
        return jsonify({'error': 'Domain not found'}), 404
    
    subdomains = [{
        'id': sub.id,
        'name': sub.name,
        'description': sub.description,
        'active': sub.active
    } for sub in domain.subdomains]
    
    return jsonify({
        'id': domain.id,
        'name': domain.name,
        'is_root': domain.is_root,
        'parent_domain_id': domain.parent_domain_id,
        'description': domain.description,
        'active': domain.active,
        'subdomains': subdomains,
        'created_at': domain.created_at.isoformat() if domain.created_at else None
    }), 200


@bp.route('/<int:domain_id>', methods=['PUT'])
def update_domain(domain_id):
    """Update domain details"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    domain = Domain.query.filter_by(id=domain_id, user_id=user.id).first()
    if not domain:
        return jsonify({'error': 'Domain not found'}), 404
    
    data = request.json
    
    if 'name' in data:
        domain.name = data['name']
    if 'description' in data:
        domain.description = data['description']
    if 'active' in data:
        domain.active = data['active']
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Domain updated successfully',
            'domain': {
                'id': domain.id,
                'name': domain.name,
                'description': domain.description,
                'active': domain.active
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:domain_id>', methods=['DELETE'])
def delete_domain(domain_id):
    """Delete a domain"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    domain = Domain.query.filter_by(id=domain_id, user_id=user.id).first()
    if not domain:
        return jsonify({'error': 'Domain not found'}), 404
    
    # Check if domain has subdomains
    if domain.subdomains:
        return jsonify({'error': 'Cannot delete domain with active subdomains'}), 400
    
    try:
        db.session.delete(domain)
        db.session.commit()
        return jsonify({'message': 'Domain deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
