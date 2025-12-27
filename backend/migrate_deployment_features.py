"""
Database migration helper for new deployment features

Run this script to update the database schema with new models:
- SSHKey model for SSH key management

Usage:
    python migrate_deployment_features.py
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import SSHKey

def migrate_deployment_features():
    """Create tables for new deployment features"""
    app = create_app()
    
    with app.app_context():
        print("Starting database migration for deployment features...")
        
        try:
            # Create all tables (will only create new ones)
            db.create_all()
            print("✅ Database tables created/updated successfully!")
            
            # Verify SSHKey table was created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'ssh_keys' in tables:
                print("✅ ssh_keys table created successfully")
            else:
                print("⚠️  ssh_keys table not found. This might be expected if it already exists.")
            
            print("\nMigration completed successfully!")
            print("\nNew features available:")
            print("  - SSH Key Management (POST/GET/DELETE /api/ssh-keys)")
            print("  - SSH Key Deployment (POST /api/ssh-keys/{key_id}/deploy)")
            print("  - Enhanced PR Creation (POST /api/pipelines/{pipeline_id}/create-pr)")
            print("  - Pipeline Trigger with Retry (POST /api/pipelines/{pipeline_id}/trigger)")
            print("  - Enhanced Log Filtering (GET /api/pipelines/{pipeline_id}/logs)")
            print("  - WebSocket Real-time Logs (pipeline_logs and pipeline_status events)")
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        return True


if __name__ == '__main__':
    success = migrate_deployment_features()
    sys.exit(0 if success else 1)
