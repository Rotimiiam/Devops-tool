from app import create_app, db, socketio
import os

app = create_app()

# Initialize OAuth with app context
with app.app_context():
    from app.routes.auth import init_oauth
    init_oauth(app)
    
    # Create tables
    db.create_all()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
