"""
Database Migration Script for Pipeline Management Enhancement

This script documents the database schema changes needed for the enhanced pipeline management system.

To apply these changes, use Flask-Migrate:

1. Generate migration:
   flask db migrate -m "Enhanced pipeline management with CRUD and monitoring"

2. Review the generated migration file in migrations/versions/

3. Apply migration:
   flask db upgrade

Manual SQL commands (if needed):

-- Add new columns to pipelines table
ALTER TABLE pipelines ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE pipelines ADD COLUMN IF NOT EXISTS server_ip VARCHAR(100);
ALTER TABLE pipelines ADD COLUMN IF NOT EXISTS subdomain VARCHAR(255);
ALTER TABLE pipelines ADD COLUMN IF NOT EXISTS port INTEGER;
ALTER TABLE pipelines ADD COLUMN IF NOT EXISTS environment_variables JSON;
ALTER TABLE pipelines ADD COLUMN IF NOT EXISTS nginx_config TEXT;
ALTER TABLE pipelines ADD COLUMN IF NOT EXISTS ssl_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE pipelines ADD COLUMN IF NOT EXISTS bitbucket_pipeline_uuid VARCHAR(255);
ALTER TABLE pipelines ADD COLUMN IF NOT EXISTS last_execution_timestamp TIMESTAMP;

-- Update status column to support new states
-- (PLANNED, BUILDING, TESTING, DEPLOYING, SUCCESS, FAILED)

-- Add unique constraint for active pipelines per repository
-- Note: This will fail if there are duplicate active pipelines
-- You may need to deactivate duplicates first
ALTER TABLE pipelines 
ADD CONSTRAINT unique_active_pipeline_per_repo 
UNIQUE (repository_id, is_active);

-- Create pipeline_executions table
CREATE TABLE IF NOT EXISTS pipeline_executions (
    id SERIAL PRIMARY KEY,
    pipeline_id INTEGER NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL,
    trigger_type VARCHAR(50) DEFAULT 'manual',
    bitbucket_build_number INTEGER,
    bitbucket_pipeline_uuid VARCHAR(255),
    bitbucket_commit_hash VARCHAR(100),
    logs TEXT,
    error_message TEXT,
    rolled_back BOOLEAN DEFAULT FALSE,
    rollback_reason TEXT,
    previous_execution_id INTEGER REFERENCES pipeline_executions(id),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_pipeline_executions_pipeline_id ON pipeline_executions(pipeline_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_executions_started_at ON pipeline_executions(started_at DESC);

"""

if __name__ == '__main__':
    print(__doc__)
    print("\nTo apply these migrations:")
    print("1. cd /projects/sandbox/Devops-tool/backend")
    print("2. flask db migrate -m 'Enhanced pipeline management'")
    print("3. flask db upgrade")
