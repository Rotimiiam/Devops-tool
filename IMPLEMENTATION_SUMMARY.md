# Pipeline Management System Enhancement - Implementation Summary

## Overview
Enhanced the pipeline management system with full CRUD operations, monitoring capabilities, and support for multiple project types.

## Changes Made

### 1. Database Models (`backend/app/models.py`)

#### Enhanced Pipeline Model
- Added `is_active` field for uniqueness constraint
- Added deployment configuration fields:
  - `server_ip` - Target server IP address
  - `subdomain` - Subdomain for the application
  - `port` - Application port number
  - `environment_variables` - JSON field for environment variables
- Added nginx configuration fields:
  - `nginx_config` - Generated nginx reverse proxy configuration
  - `ssl_enabled` - SSL/TLS certificate flag
- Added Bitbucket integration fields:
  - `bitbucket_pipeline_uuid` - UUID of the Bitbucket pipeline
  - `last_execution_timestamp` - Timestamp of last execution
- Updated status values to support: PLANNED, BUILDING, TESTING, DEPLOYING, SUCCESS, FAILED
- Added uniqueness constraint: only ONE active pipeline per repository

#### New PipelineExecution Model
Tracks pipeline execution history with:
- `status` - Execution status (BUILDING, TESTING, DEPLOYING, SUCCESS, FAILED)
- `trigger_type` - How the pipeline was triggered (manual, webhook, scheduled)
- `bitbucket_build_number` - Build number from Bitbucket
- `bitbucket_pipeline_uuid` - UUID from Bitbucket
- `bitbucket_commit_hash` - Git commit hash
- `logs` - Complete execution logs
- `error_message` - Error details if failed
- `rolled_back` - Rollback flag
- `rollback_reason` - Reason for rollback
- `previous_execution_id` - Reference to previous execution for rollback
- Timestamps: `started_at`, `completed_at`, `duration_seconds`

### 2. Pipeline Generator Service (`backend/app/services/pipeline_generator.py`)

#### Enhanced with Multiple Project Type Support
- **React** - Build optimization, static asset serving, nginx configuration
- **Vue** - Build optimization with npm/yarn support
- **Angular** - AOT compilation, production builds
- **Django** - WSGI server setup, database migrations, static file collection
- **Flask/FastAPI** - WSGI/ASGI server setup
- **Node.js/Express** - PM2 process management
- **Next.js** - SSR/SSG builds with PM2
- **Docker** - Multi-stage builds, image optimization
- **Full-stack** - Coordinated frontend and backend deployment

#### New Methods
- `_detect_project_type()` - Auto-detect project type from frameworks
- `generate_nginx_config()` - Generate nginx reverse proxy configuration with SSL
- `generate_certbot_command()` - Generate Let's Encrypt SSL setup command
- Individual pipeline generators for each project type

### 3. Bitbucket Service Enhancement (`backend/app/services/bitbucket_service.py`)

#### New Methods
- `trigger_pipeline()` - Trigger pipeline execution via Bitbucket API
- `get_pipeline_runs()` - Get recent pipeline runs
- `get_pipeline_logs()` - Get detailed logs for a specific pipeline run
- `sync_environment_variables()` - Sync environment variables to Bitbucket repository variables
- `get_repository_variables()` - Get all repository pipeline variables

### 4. API Endpoints (`backend/app/routes/pipelines.py`)

#### New CRUD Endpoints
- **GET** `/api/pipelines` - List all pipelines with pagination
- **GET** `/api/pipelines/{id}` - Get pipeline details with execution history
- **PUT** `/api/pipelines/{id}` - Update pipeline configuration
- **DELETE** `/api/pipelines/{id}` - Delete pipeline with optional remote cleanup

#### New Management Endpoints
- **POST** `/api/pipelines/{id}/regenerate` - Re-analyze repository and regenerate pipeline
- **POST** `/api/pipelines/{id}/trigger` - Manually trigger pipeline execution
- **GET** `/api/pipelines/{id}/logs` - Get pipeline execution logs
- **POST** `/api/pipelines/{id}/sync-env` - Sync environment variables to Bitbucket

#### Enhanced Existing Endpoints
- **POST** `/api/pipelines/generate` - Now supports:
  - Multiple project types
  - Subdomain and port configuration
  - Environment variables
  - Nginx configuration generation
  - Uniqueness validation (409 error if active pipeline exists)

### 5. WebSocket Support (`backend/app/websocket_handlers.py`)

#### Real-time Log Streaming
- `connect` - WebSocket connection handler
- `disconnect` - WebSocket disconnection handler
- `subscribe_logs` - Subscribe to real-time logs for a pipeline execution
- `unsubscribe_logs` - Unsubscribe from pipeline logs
- Background task for streaming logs from Bitbucket API

#### Events
- `subscribed` - Confirmation of subscription
- `log_update` - Real-time log updates (every 5 seconds)
- `log_complete` - Pipeline execution completed
- `log_error` - Error occurred while streaming logs

### 6. Application Updates

#### `backend/app/__init__.py`
- Added Flask-SocketIO initialization
- Registered WebSocket handlers

#### `backend/app/main.py`
- Updated to use `socketio.run()` instead of `app.run()`

#### `backend/requirements.txt`
- Added `Flask-SocketIO==5.3.5`
- Added `python-socketio==5.10.0`
- Added `eventlet==0.33.3`

### 7. Documentation

#### `PIPELINE_API.md`
Comprehensive API documentation including:
- All endpoints with request/response examples
- WebSocket event documentation
- Supported project types
- Error handling
- Authentication requirements

#### `backend/migration_guide.py`
Database migration instructions and SQL commands for:
- Adding new columns to pipelines table
- Creating pipeline_executions table
- Adding indexes for performance
- Adding uniqueness constraint

## Features Implemented

### ✅ Full CRUD Operations
- Create pipelines with intelligent project type detection
- Read pipeline details with execution history
- Update pipeline configuration (subdomain, port, environment variables)
- Delete pipelines with optional remote cleanup

### ✅ Pipeline Monitoring
- Track execution history
- Real-time log streaming via WebSocket
- Pipeline status tracking (PLANNED → BUILDING → TESTING → DEPLOYING → SUCCESS/FAILED)
- Error handling and rollback mechanisms

### ✅ Multi-Project Type Support
- Intelligent detection of 9+ project types
- Optimized build and deployment configurations per project type
- Framework-specific optimizations (caching, build tools, etc.)

### ✅ Nginx & SSL Configuration
- Auto-generate nginx reverse proxy configurations
- SSL certificate setup with certbot integration
- Security headers and optimization settings

### ✅ Environment Variable Management
- Store environment variables per pipeline
- Sync variables to Bitbucket repository
- Secure handling of sensitive variables

### ✅ Uniqueness Validation
- Database-level constraint: ONE active pipeline per repository
- API-level validation with helpful error messages
- Conflict resolution (409 status code)

### ✅ Bitbucket Integration
- Trigger pipelines remotely
- Fetch real-time logs
- Sync environment variables
- Track build numbers and commit hashes

## Migration Instructions

1. **Update Dependencies**
   ```bash
   cd /projects/sandbox/Devops-tool/backend
   pip install -r requirements.txt
   ```

2. **Apply Database Migrations**
   ```bash
   flask db migrate -m "Enhanced pipeline management"
   flask db upgrade
   ```

3. **Restart Application**
   ```bash
   # Development
   python app/main.py
   
   # Production (with gunicorn)
   gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app.main:app
   ```

## Testing the Implementation

### Test Endpoints
```bash
# List all pipelines
curl -X GET http://localhost:5000/api/pipelines \
  --cookie "session=..."

# Get pipeline details
curl -X GET http://localhost:5000/api/pipelines/1 \
  --cookie "session=..."

# Update pipeline
curl -X PUT http://localhost:5000/api/pipelines/1 \
  -H "Content-Type: application/json" \
  -d '{"port": 8081, "subdomain": "newapp"}' \
  --cookie "session=..."

# Trigger pipeline
curl -X POST http://localhost:5000/api/pipelines/1/trigger \
  -H "Content-Type: application/json" \
  -d '{"branch": "main"}' \
  --cookie "session=..."

# Get logs
curl -X GET http://localhost:5000/api/pipelines/1/logs \
  --cookie "session=..."
```

### Test WebSocket
```javascript
import io from 'socket.io-client';

const socket = io('http://localhost:5000');

socket.on('connect', () => {
  console.log('Connected');
  socket.emit('subscribe_logs', {
    pipeline_id: 1,
    execution_id: 10
  });
});

socket.on('log_update', (data) => {
  console.log('Log update:', data);
});

socket.on('log_complete', (data) => {
  console.log('Pipeline completed:', data);
});
```

## Known Limitations

1. **Docker Validation Skipped**: Running in INTEGRATIONS_ONLY network mode, so Docker validation was skipped as per requirements.

2. **Domain Management**: The nginx config generation currently uses a placeholder domain. Integration with the Domain model would be needed for production use.

3. **SSH Key Management**: Deployment steps assume SSH keys are stored in Bitbucket repository variables as `$SSH_PRIVATE_KEY`.

4. **WebSocket Scalability**: Current implementation uses threading for log streaming. For high-scale deployments, consider using Celery background tasks with Redis pub/sub.

## Security Considerations

1. **Environment Variables**: Stored as JSON in database. Consider encryption for sensitive values.
2. **SSH Keys**: Never stored in database, only referenced from Bitbucket variables.
3. **Authentication**: All endpoints require session authentication.
4. **Authorization**: All operations verify user owns the repository/pipeline.
5. **Input Validation**: Port numbers, YAML configs, and other inputs are validated.

## Next Steps

1. **Frontend Integration**: Build UI components for the new CRUD operations
2. **Domain Integration**: Connect nginx config generation with user's domain records
3. **Rollback Implementation**: Implement automatic rollback on deployment failures
4. **Notification System**: Add email/webhook notifications for pipeline events
5. **Advanced Monitoring**: Add metrics, performance tracking, and alerting
6. **Multi-environment Support**: Add staging, QA, production environment management

## Files Modified/Created

### Modified
- `backend/app/models.py` - Enhanced Pipeline model, added PipelineExecution model
- `backend/app/services/pipeline_generator.py` - Added multi-project type support
- `backend/app/services/bitbucket_service.py` - Added pipeline management methods
- `backend/app/routes/pipelines.py` - Complete rewrite with new endpoints
- `backend/app/__init__.py` - Added SocketIO initialization
- `backend/app/main.py` - Updated to use SocketIO
- `backend/requirements.txt` - Added WebSocket dependencies

### Created
- `backend/app/websocket_handlers.py` - WebSocket event handlers
- `backend/migration_guide.py` - Database migration instructions
- `PIPELINE_API.md` - Comprehensive API documentation
- `IMPLEMENTATION_SUMMARY.md` - This file

## Conclusion

The pipeline management system has been successfully enhanced with comprehensive CRUD operations, real-time monitoring, and support for multiple project types. The implementation follows best practices for API design, includes proper error handling, and maintains backward compatibility with existing functionality.
