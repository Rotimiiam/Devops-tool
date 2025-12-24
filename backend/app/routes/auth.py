from flask import Blueprint, request, jsonify, session, redirect, current_app
from authlib.integrations.flask_client import OAuth
from ..models import User, db
import secrets

bp = Blueprint('auth', __name__)
oauth = OAuth()


def init_oauth(app):
    """Initialize OAuth clients"""
    oauth.init_app(app)
    
    # Bitbucket OAuth
    oauth.register(
        name='bitbucket',
        client_id=app.config['BITBUCKET_CLIENT_ID'],
        client_secret=app.config['BITBUCKET_CLIENT_SECRET'],
        access_token_url='https://bitbucket.org/site/oauth2/access_token',
        authorize_url='https://bitbucket.org/site/oauth2/authorize',
        api_base_url='https://api.bitbucket.org/2.0/',
        client_kwargs={'scope': 'repository repository:write account'},
    )
    
    # GitHub OAuth
    oauth.register(
        name='github',
        client_id=app.config['GITHUB_CLIENT_ID'],
        client_secret=app.config['GITHUB_CLIENT_SECRET'],
        access_token_url='https://github.com/login/oauth/access_token',
        authorize_url='https://github.com/login/oauth/authorize',
        api_base_url='https://api.github.com/',
        client_kwargs={'scope': 'repo user'},
    )


@bp.route('/bitbucket/login')
def bitbucket_login():
    """Initiate Bitbucket OAuth flow"""
    redirect_uri = current_app.config['BITBUCKET_CALLBACK_URL']
    return oauth.bitbucket.authorize_redirect(redirect_uri)


@bp.route('/bitbucket/callback')
def bitbucket_callback():
    """Handle Bitbucket OAuth callback"""
    try:
        token = oauth.bitbucket.authorize_access_token()
        
        # Get user info
        resp = oauth.bitbucket.get('user')
        user_info = resp.json()
        
        email = user_info.get('email') or f"{user_info['username']}@bitbucket.local"
        
        # Find or create user
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email)
            db.session.add(user)
        
        # Update Bitbucket tokens
        user.bitbucket_token = token['access_token']
        user.bitbucket_refresh_token = token.get('refresh_token')
        user.bitbucket_username = user_info['username']
        
        db.session.commit()
        
        # Store user in session
        session['user_id'] = user.id
        
        return redirect(f"{current_app.config['FRONTEND_URL']}/dashboard?auth=success")
    except Exception as e:
        return redirect(f"{current_app.config['FRONTEND_URL']}/dashboard?auth=error&message={str(e)}")


@bp.route('/github/login')
def github_login():
    """Initiate GitHub OAuth flow"""
    redirect_uri = current_app.config['GITHUB_CALLBACK_URL']
    return oauth.github.authorize_redirect(redirect_uri)


@bp.route('/github/callback')
def github_callback():
    """Handle GitHub OAuth callback"""
    try:
        token = oauth.github.authorize_access_token()
        
        # Get user info
        resp = oauth.github.get('user')
        user_info = resp.json()
        
        email = user_info.get('email')
        if not email:
            # Fetch email separately if not in profile
            emails_resp = oauth.github.get('user/emails')
            emails = emails_resp.json()
            email = next((e['email'] for e in emails if e['primary']), emails[0]['email'] if emails else None)
        
        if not email:
            return redirect(f"{current_app.config['FRONTEND_URL']}/dashboard?auth=error&message=No email found")
        
        # Find or create user
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email)
            db.session.add(user)
        
        # Update GitHub tokens
        user.github_token = token['access_token']
        user.github_refresh_token = token.get('refresh_token')
        user.github_username = user_info['login']
        
        db.session.commit()
        
        # Store user in session
        session['user_id'] = user.id
        
        return redirect(f"{current_app.config['FRONTEND_URL']}/dashboard?auth=success")
    except Exception as e:
        return redirect(f"{current_app.config['FRONTEND_URL']}/dashboard?auth=error&message={str(e)}")


@bp.route('/status')
def auth_status():
    """Check authentication status"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'authenticated': False}), 200
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'authenticated': False}), 200
    
    return jsonify({
        'authenticated': True,
        'user': {
            'id': user.id,
            'email': user.email,
            'bitbucket_connected': bool(user.bitbucket_token),
            'bitbucket_username': user.bitbucket_username,
            'github_connected': bool(user.github_token),
            'github_username': user.github_username,
            'gemini_configured': bool(user.gemini_api_key)
        }
    }), 200


@bp.route('/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200
