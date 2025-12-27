# Pipeline Management API Documentation

## Overview

The enhanced pipeline management system provides full CRUD operations and monitoring capabilities for CI/CD pipelines with support for multiple project types.

## Authentication

All endpoints require authentication via session cookies. Users must be logged in through the OAuth flow (Bitbucket/GitHub).

## Endpoints

### 1. List All Pipelines
**GET** `/api/pipelines`

List all pipelines for the authenticated user with pagination support.

**Query Parameters:**
- `page` (integer, default: 1) - Page number
- `per_page` (integer, default: 20) - Items per page
- `status` (string, optional) - Filter by status (PLANNED, BUILDING, TESTING, DEPLOYING, SUCCESS, FAILED)

**Response:**
```json
{
  "pipelines": [
    {
      "id": 1,
      "repository": {
        "id": 1,
        "name": "my-app",
        "source": "bitbucket"
      },
      "version": 1,
      "status": "SUCCESS",
      "is_active": true,
      "deployment_server": "prod-server.example.com",
      "subdomain": "myapp",
      "port": 8080,
      "server_ip": "192.168.1.100",
      "ssl_enabled": true,
      "pr_created": true,
      "pr_url": "https://bitbucket.org/...",
      "last_execution_timestamp": "2024-01-15T10:30:00Z",
      "created_at": "2024-01-10T08:00:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 45,
    "pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

### 2. Get Pipeline Details
**GET** `/api/pipelines/{pipeline_id}`

Get complete pipeline configuration including status, config YAML, repository info, and execution history.

**Response:**
```json
{
  "id": 1,
  "repository": {
    "id": 1,
    "name": "my-app",
    "source": "bitbucket",
    "bitbucket_workspace": "myworkspace",
    "detected_languages": {"Python": {"count": 25, "confidence": 95}},
    "detected_frameworks": {"Flask": {"confidence": 90}}
  },
  "version": 1,
  "config": "image: python:3.11\npipelines:\n  default:\n    ...",
  "status": "SUCCESS",
  "is_active": true,
  "deployment_server": "prod-server.example.com",
  "server_ip": "192.168.1.100",
  "subdomain": "myapp",
  "port": 8080,
  "environment_variables": {
    "DATABASE_URL": "postgresql://...",
    "API_KEY": "***"
  },
  "nginx_config": "server {\n  listen 443 ssl http2;\n  ...",
  "ssl_enabled": true,
  "execution_history": [
    {
      "id": 10,
      "status": "SUCCESS",
      "trigger_type": "manual",
      "bitbucket_build_number": 42,
      "started_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T10:35:00Z",
      "duration_seconds": 300,
      "error_message": null,
      "rolled_back": false
    }
  ]
}
```

### 3. Update Pipeline Configuration
**PUT** `/api/pipelines/{pipeline_id}`

Update pipeline configuration (subdomain, port, server IP, environment variables).

**Request Body:**
```json
{
  "subdomain": "newsubdomain",
  "port": 8081,
  "server_ip": "192.168.1.101",
  "deployment_server": "new-server.example.com",
  "environment_variables": {
    "DATABASE_URL": "postgresql://newdb",
    "NEW_VAR": "value"
  },
  "ssl_enabled": true,
  "config": "image: python:3.11\n..."  // Optional: Update YAML config
}
```

**Response:**
```json
{
  "message": "Pipeline updated successfully",
  "pipeline": {
    "id": 1,
    "subdomain": "newsubdomain",
    "port": 8081,
    "server_ip": "192.168.1.101",
    "deployment_server": "new-server.example.com",
    "environment_variables": {...},
    "ssl_enabled": true,
    "nginx_config": "server {\n...",
    "updated_at": "2024-01-15T11:00:00Z"
  }
}
```

### 4. Delete Pipeline
**DELETE** `/api/pipelines/{pipeline_id}`

Remove pipeline records and optionally clean up remote configurations.

**Query Parameters:**
- `cleanup_remote` (boolean, default: false) - Clean up Bitbucket configurations

**Response:**
```json
{
  "message": "Pipeline deleted successfully",
  "pipeline_id": 1
}
```

### 5. Regenerate Pipeline
**POST** `/api/pipelines/{pipeline_id}/regenerate`

Re-analyze the repository and generate updated pipeline configuration based on latest code changes.

**Response:**
```json
{
  "message": "Pipeline regenerated successfully",
  "pipeline": {
    "id": 1,
    "version": 2,
    "config": "image: python:3.11\n...",
    "status": "PLANNED",
    "updated_at": "2024-01-15T11:30:00Z"
  },
  "analysis": {
    "languages": {"Python": {"count": 30, "confidence": 95}},
    "frameworks": {"Flask": {"confidence": 90}, "React": {"confidence": 85}},
    "confidence": 92.5
  }
}
```

### 6. Trigger Pipeline Execution
**POST** `/api/pipelines/{pipeline_id}/trigger`

Manually trigger pipeline execution via Bitbucket API.

**Request Body:**
```json
{
  "branch": "main"  // Optional, defaults to "main"
}
```

**Response:**
```json
{
  "message": "Pipeline triggered successfully",
  "execution": {
    "id": 11,
    "build_number": 43,
    "uuid": "{abc-123-def-456}",
    "status": "BUILDING",
    "started_at": "2024-01-15T12:00:00Z"
  }
}
```

### 7. Get Pipeline Logs
**GET** `/api/pipelines/{pipeline_id}/logs`

Retrieve execution logs from Bitbucket pipeline runs.

**Query Parameters:**
- `execution_id` (integer, optional) - Specific execution ID, defaults to latest

**Response:**
```json
{
  "execution_id": 11,
  "build_number": 43,
  "uuid": "{abc-123-def-456}",
  "status": "COMPLETED",
  "started_at": "2024-01-15T12:00:00Z",
  "completed_at": "2024-01-15T12:05:00Z",
  "duration_seconds": 300,
  "steps": [
    {
      "name": "Build Application",
      "state": "COMPLETED",
      "started_on": "2024-01-15T12:00:10Z",
      "completed_on": "2024-01-15T12:03:00Z",
      "duration_in_seconds": 170,
      "log": "Installing dependencies...\nBuild successful"
    },
    {
      "name": "Deploy to Server",
      "state": "COMPLETED",
      "started_on": "2024-01-15T12:03:10Z",
      "completed_on": "2024-01-15T12:05:00Z",
      "duration_in_seconds": 110,
      "log": "Deploying to server...\nDeployment successful"
    }
  ]
}
```

### 8. Sync Environment Variables
**POST** `/api/pipelines/{pipeline_id}/sync-env`

Sync environment variables to Bitbucket repository variables.

**Response:**
```json
{
  "message": "Environment variables synced successfully",
  "synced": [
    {"key": "DATABASE_URL", "action": "updated"},
    {"key": "NEW_VAR", "action": "created"}
  ],
  "errors": []
}
```

### 9. Generate Pipeline
**POST** `/api/pipelines/generate`

Generate a new pipeline configuration for a repository.

**Request Body:**
```json
{
  "repository_id": 1,
  "deployment_server": "prod-server.example.com",
  "subdomain": "myapp",
  "port": 8080,
  "server_ip": "192.168.1.100",
  "environment_variables": {
    "DATABASE_URL": "postgresql://...",
    "API_KEY": "secret"
  }
}
```

**Response:**
```json
{
  "message": "Pipeline generated successfully",
  "pipeline": {
    "id": 1,
    "version": 1,
    "config": "image: python:3.11\n...",
    "status": "PLANNED",
    "nginx_config": "server {\n..."
  }
}
```

**Error Response (409):**
```json
{
  "error": "An active pipeline already exists for this repository",
  "existing_pipeline_id": 5
}
```

## WebSocket Support for Real-Time Logs

Connect to WebSocket endpoint at `/socket.io` for live log updates.

### Events

#### Client → Server

**subscribe_logs**
```json
{
  "pipeline_id": 1,
  "execution_id": 11
}
```

**unsubscribe_logs**
```json
{
  "pipeline_id": 1
}
```

#### Server → Client

**subscribed**
```json
{
  "pipeline_id": 1,
  "execution_id": 11,
  "room": "pipeline_1"
}
```

**log_update**
```json
{
  "pipeline_id": 1,
  "execution_id": 11,
  "status": "BUILDING",
  "steps": [
    {
      "name": "Build Application",
      "state": "RUNNING",
      "duration_seconds": 45,
      "log_preview": "Installing dependencies..."
    }
  ]
}
```

**log_complete**
```json
{
  "pipeline_id": 1,
  "execution_id": 11,
  "status": "COMPLETED",
  "duration_seconds": 300
}
```

**log_error**
```json
{
  "pipeline_id": 1,
  "execution_id": 11,
  "error": "Failed to fetch logs"
}
```

## Supported Project Types

The pipeline generator intelligently detects and creates optimized pipelines for:

1. **React** - Build optimization, static asset serving, nginx configuration
2. **Vue** - Build optimization, static asset serving
3. **Angular** - AOT compilation, production builds
4. **Django** - WSGI server setup, database migrations, static file collection
5. **Flask/FastAPI** - WSGI/ASGI server setup, dependency management
6. **Node.js/Express** - PM2 process management, dependency management
7. **Next.js** - SSR/SSG builds, PM2 management
8. **Docker** - Multi-stage builds, image optimization
9. **Full-stack** - Coordinated frontend and backend deployment

## Pipeline Status States

- `draft` - Initial state, not yet configured
- `PLANNED` - Configuration ready, not yet executed
- `BUILDING` - Currently building
- `TESTING` - Running tests
- `DEPLOYING` - Deploying to server
- `SUCCESS` - Successfully completed
- `FAILED` - Execution failed

## Uniqueness Constraint

Only **ONE active pipeline** is allowed per repository. To create a new pipeline for a repository with an existing active pipeline:

1. Delete the existing pipeline, OR
2. Mark the existing pipeline as inactive (is_active=false)

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (not authenticated)
- `404` - Not Found
- `409` - Conflict (uniqueness constraint violation)
- `500` - Internal Server Error

Error responses include a descriptive message:
```json
{
  "error": "Detailed error message here"
}
```
