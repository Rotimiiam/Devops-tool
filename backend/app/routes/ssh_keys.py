from flask import Blueprint, request, jsonify, session
from datetime import datetime
from ..models import User, SSHKey, db
from ..services.ssh_service import SSHService

bp = Blueprint('ssh_keys', __name__)


def get_current_user():
    """Get current authenticated user"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)


@bp.route('', methods=['POST'])
def create_ssh_key():
    """
    Generate and store SSH key pair for deployment access
    
    Request body:
    {
        "name": "Production Server Key",
        "description": "SSH key for production deployments",
        "key_type": "rsa",  // or "ed25519"
        "key_size": 4096    // only for RSA
    }
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    
    # Validate required fields
    name = data.get('name')
    if not name:
        return jsonify({'error': 'name is required'}), 400
    
    # Optional parameters
    description = data.get('description', '')
    key_type = data.get('key_type', 'rsa').lower()
    key_size = data.get('key_size', 4096)
    
    # Validate key type
    if key_type not in ['rsa', 'ed25519']:
        return jsonify({'error': 'key_type must be "rsa" or "ed25519"'}), 400
    
    # Validate key size for RSA
    if key_type == 'rsa' and key_size not in [2048, 4096]:
        return jsonify({'error': 'key_size must be 2048 or 4096 for RSA keys'}), 400
    
    try:
        # Generate SSH key pair
        comment = f"{user.email} - {name}"
        key_data = SSHService.generate_ssh_key_pair(
            key_type=key_type,
            key_size=key_size if key_type == 'rsa' else None,
            comment=comment
        )
        
        # Create SSH key record
        ssh_key = SSHKey(
            user_id=user.id,
            name=name,
            description=description,
            public_key=key_data['public_key'],
            private_key=key_data['private_key'],  # In production, encrypt this!
            fingerprint=key_data['fingerprint'],
            key_type=key_type,
            key_size=key_size if key_type == 'rsa' else None,
            deployed_to=[],
            active=True
        )
        
        db.session.add(ssh_key)
        db.session.commit()
        
        return jsonify({
            'message': 'SSH key pair generated successfully',
            'ssh_key': {
                'id': ssh_key.id,
                'name': ssh_key.name,
                'description': ssh_key.description,
                'public_key': ssh_key.public_key,
                'fingerprint': ssh_key.fingerprint,
                'key_type': ssh_key.key_type,
                'key_size': ssh_key.key_size,
                'created_at': ssh_key.created_at.isoformat()
            },
            'private_key': key_data['private_key']  # Only returned on creation
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('', methods=['GET'])
def list_ssh_keys():
    """
    List all SSH keys for the authenticated user
    
    Query parameters:
    - active: Filter by active status (true/false)
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get filter parameters
    active_filter = request.args.get('active')
    
    # Build query
    query = SSHKey.query.filter_by(user_id=user.id)
    
    if active_filter is not None:
        is_active = active_filter.lower() == 'true'
        query = query.filter_by(active=is_active)
    
    # Order by creation date (newest first)
    ssh_keys = query.order_by(SSHKey.created_at.desc()).all()
    
    return jsonify({
        'ssh_keys': [{
            'id': key.id,
            'name': key.name,
            'description': key.description,
            'public_key': key.public_key,
            'fingerprint': key.fingerprint,
            'key_type': key.key_type,
            'key_size': key.key_size,
            'deployed_to': key.deployed_to or [],
            'active': key.active,
            'last_used': key.last_used.isoformat() if key.last_used else None,
            'created_at': key.created_at.isoformat(),
            'updated_at': key.updated_at.isoformat()
        } for key in ssh_keys]
    }), 200


@bp.route('/<int:key_id>', methods=['GET'])
def get_ssh_key(key_id):
    """Get details of a specific SSH key"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    ssh_key = SSHKey.query.filter_by(id=key_id, user_id=user.id).first()
    if not ssh_key:
        return jsonify({'error': 'SSH key not found'}), 404
    
    return jsonify({
        'id': ssh_key.id,
        'name': ssh_key.name,
        'description': ssh_key.description,
        'public_key': ssh_key.public_key,
        'fingerprint': ssh_key.fingerprint,
        'key_type': ssh_key.key_type,
        'key_size': ssh_key.key_size,
        'deployed_to': ssh_key.deployed_to or [],
        'active': ssh_key.active,
        'last_used': ssh_key.last_used.isoformat() if ssh_key.last_used else None,
        'created_at': ssh_key.created_at.isoformat(),
        'updated_at': ssh_key.updated_at.isoformat()
    }), 200


@bp.route('/<int:key_id>', methods=['DELETE'])
def delete_ssh_key(key_id):
    """
    Remove SSH key pair
    
    Query parameters:
    - remove_from_servers: If true, attempt to remove from all deployed servers
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    ssh_key = SSHKey.query.filter_by(id=key_id, user_id=user.id).first()
    if not ssh_key:
        return jsonify({'error': 'SSH key not found'}), 404
    
    remove_from_servers = request.args.get('remove_from_servers', 'false').lower() == 'true'
    
    removal_results = []
    
    # Optionally remove from deployed servers
    if remove_from_servers and ssh_key.deployed_to:
        for server_info in ssh_key.deployed_to:
            try:
                result = SSHService.remove_key_from_server(
                    server_host=server_info.get('host'),
                    server_port=server_info.get('port', 22),
                    username=server_info.get('username'),
                    password=server_info.get('password', ''),  # This is a limitation
                    public_key_fingerprint=ssh_key.fingerprint
                )
                removal_results.append({
                    'server': f"{server_info.get('host')}:{server_info.get('port', 22)}",
                    'result': result
                })
            except Exception as e:
                removal_results.append({
                    'server': f"{server_info.get('host')}:{server_info.get('port', 22)}",
                    'result': {'success': False, 'message': str(e)}
                })
    
    try:
        db.session.delete(ssh_key)
        db.session.commit()
        
        return jsonify({
            'message': 'SSH key deleted successfully',
            'key_id': key_id,
            'removal_results': removal_results if removal_results else None
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:key_id>', methods=['PUT'])
def update_ssh_key(key_id):
    """
    Update SSH key metadata (name, description, active status)
    
    Request body:
    {
        "name": "Updated name",
        "description": "Updated description",
        "active": false
    }
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    ssh_key = SSHKey.query.filter_by(id=key_id, user_id=user.id).first()
    if not ssh_key:
        return jsonify({'error': 'SSH key not found'}), 404
    
    data = request.json
    
    try:
        # Update allowed fields
        if 'name' in data:
            ssh_key.name = data['name']
        
        if 'description' in data:
            ssh_key.description = data['description']
        
        if 'active' in data:
            ssh_key.active = data['active']
        
        ssh_key.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'SSH key updated successfully',
            'ssh_key': {
                'id': ssh_key.id,
                'name': ssh_key.name,
                'description': ssh_key.description,
                'active': ssh_key.active,
                'updated_at': ssh_key.updated_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:key_id>/deploy', methods=['POST'])
def deploy_ssh_key(key_id):
    """
    Deploy SSH public key to specified servers
    
    Request body:
    {
        "servers": [
            {
                "host": "192.168.1.100",
                "port": 22,
                "username": "deploy",
                "password": "password123",  // or use existing key for auth
                "auth_method": "password"   // "password" or "key"
            }
        ]
    }
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    ssh_key = SSHKey.query.filter_by(id=key_id, user_id=user.id).first()
    if not ssh_key:
        return jsonify({'error': 'SSH key not found'}), 404
    
    if not ssh_key.active:
        return jsonify({'error': 'SSH key is inactive'}), 400
    
    data = request.json
    servers = data.get('servers', [])
    
    if not servers:
        return jsonify({'error': 'servers list is required'}), 400
    
    deployment_results = []
    deployed_to = ssh_key.deployed_to or []
    
    for server in servers:
        host = server.get('host')
        port = server.get('port', 22)
        username = server.get('username')
        password = server.get('password')
        auth_method = server.get('auth_method', 'password')
        
        if not host or not username:
            deployment_results.append({
                'server': f"{host}:{port}",
                'success': False,
                'message': 'Missing required fields: host and username'
            })
            continue
        
        # Deploy the key
        result = SSHService.deploy_key_to_server(
            server_host=host,
            server_port=port,
            username=username,
            password=password,
            public_key=ssh_key.public_key,
            auth_method=auth_method
        )
        
        deployment_results.append({
            'server': f"{username}@{host}:{port}",
            'success': result['success'],
            'message': result['message']
        })
        
        # Track successful deployments
        if result['success']:
            server_entry = {
                'host': host,
                'port': port,
                'username': username,
                'deployed_at': datetime.utcnow().isoformat()
            }
            # Add to deployed_to list if not already there
            if not any(s['host'] == host and s['port'] == port and s['username'] == username 
                      for s in deployed_to):
                deployed_to.append(server_entry)
    
    # Update deployed_to list
    try:
        ssh_key.deployed_to = deployed_to
        ssh_key.last_used = datetime.utcnow()
        ssh_key.updated_at = datetime.utcnow()
        db.session.commit()
        
        success_count = sum(1 for r in deployment_results if r['success'])
        
        return jsonify({
            'message': f'Deployment completed: {success_count}/{len(servers)} successful',
            'results': deployment_results
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:key_id>/test', methods=['POST'])
def test_ssh_key(key_id):
    """
    Test SSH connection using the key
    
    Request body:
    {
        "host": "192.168.1.100",
        "port": 22,
        "username": "deploy"
    }
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    ssh_key = SSHKey.query.filter_by(id=key_id, user_id=user.id).first()
    if not ssh_key:
        return jsonify({'error': 'SSH key not found'}), 404
    
    data = request.json
    host = data.get('host')
    port = data.get('port', 22)
    username = data.get('username')
    
    if not host or not username:
        return jsonify({'error': 'host and username are required'}), 400
    
    # Test the connection
    result = SSHService.test_ssh_connection(
        server_host=host,
        server_port=port,
        username=username,
        private_key_str=ssh_key.private_key
    )
    
    # Update last_used if successful
    if result['success']:
        try:
            ssh_key.last_used = datetime.utcnow()
            db.session.commit()
        except:
            pass
    
    return jsonify(result), 200 if result['success'] else 400


@bp.route('/<int:key_id>/private', methods=['GET'])
def get_private_key(key_id):
    """
    Get the private key (use with caution!)
    This endpoint should be heavily restricted in production
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    ssh_key = SSHKey.query.filter_by(id=key_id, user_id=user.id).first()
    if not ssh_key:
        return jsonify({'error': 'SSH key not found'}), 404
    
    return jsonify({
        'id': ssh_key.id,
        'name': ssh_key.name,
        'private_key': ssh_key.private_key,
        'warning': 'Keep this private key secure. Never share it or commit it to version control.'
    }), 200
