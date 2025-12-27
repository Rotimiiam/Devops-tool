# Deployment Features API Documentation

This document describes the comprehensive deployment features including PR creation, SSH key management, pipeline triggering, and real-time log monitoring.

## Table of Contents

1. [SSH Key Management](#ssh-key-management)
2. [Enhanced Pipeline Features](#enhanced-pipeline-features)
3. [WebSocket Real-time Logs](#websocket-real-time-logs)
4. [Error Handling](#error-handling)

---

## SSH Key Management

### POST /api/ssh-keys

Generate and store SSH key pair for deployment access.

**Request Body:**
```json
{
  "name": "Production Server Key",
  "description": "SSH key for production deployments",
  "key_type": "rsa",    // "rsa" or "ed25519"
  "key_size": 4096      // 2048 or 4096 (for RSA only)
}
```

**Response (201 Created):**
```json
{
  "message": "SSH key pair generated successfully",
  "ssh_key": {
    "id": 1,
    "name": "Production Server Key",
    "description": "SSH key for production deployments",
    "public_key": "ssh-rsa AAAAB3... user@example.com - Production Server Key",
    "fingerprint": "MD5:xx:xx:xx:...",
    "key_type": "rsa",
    "key_size": 4096,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "private_key": "-----BEGIN OPENSSH PRIVATE KEY-----\n..."
}
```

**Note:** The private key is only returned during creation. Store it securely!

---

### GET /api/ssh-keys

List all SSH keys for the authenticated user.

**Query Parameters:**
- `active` (optional): Filter by active status ("true" or "false")

**Response (200 OK):**
```json
{
  "ssh_keys": [
    {
      "id": 1,
      "name": "Production Server Key",
      "description": "SSH key for production deployments",
      "public_key": "ssh-rsa AAAAB3...",
      "fingerprint": "MD5:xx:xx:xx:...",
      "key_type": "rsa",
      "key_size": 4096,
      "deployed_to": [
        {
          "host": "192.168.1.100",
          "port": 22,
          "username": "deploy",
          "deployed_at": "2024-01-15T11:00:00Z"
        }
      ],
      "active": true,
      "last_used": "2024-01-15T12:00:00Z",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T12:00:00Z"
    }
  ]
}
```

---

### GET /api/ssh-keys/{key_id}

Get details of a specific SSH key.

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Production Server Key",
  "description": "SSH key for production deployments",
  "public_key": "ssh-rsa AAAAB3...",
  "fingerprint": "MD5:xx:xx:xx:...",
  "key_type": "rsa",
  "key_size": 4096,
  "deployed_to": [...],
  "active": true,
  "last_used": "2024-01-15T12:00:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T12:00:00Z"
}
```

---

### PUT /api/ssh-keys/{key_id}

Update SSH key metadata (name, description, active status).

**Request Body:**
```json
{
  "name": "Updated Key Name",
  "description": "Updated description",
  "active": false
}
```

**Response (200 OK):**
```json
{
  "message": "SSH key updated successfully",
  "ssh_key": {
    "id": 1,
    "name": "Updated Key Name",
    "description": "Updated description",
    "active": false,
    "updated_at": "2024-01-15T13:00:00Z"
  }
}
```

---

### DELETE /api/ssh-keys/{key_id}

Remove SSH key pair.

**Query Parameters:**
- `remove_from_servers` (optional): If "true", attempts to remove from all deployed servers

**Response (200 OK):**
```json
{
  "message": "SSH key deleted successfully",
  "key_id": 1,
  "removal_results": [
    {
      "server": "deploy@192.168.1.100:22",
      "result": {
        "success": true,
        "message": "SSH key successfully removed from server"
      }
    }
  ]
}
```

---

### POST /api/ssh-keys/{key_id}/deploy

Deploy SSH public key to specified servers.

**Request Body:**
```json
{
  "servers": [
    {
      "host": "192.168.1.100",
      "port": 22,
      "username": "deploy",
      "password": "password123",
      "auth_method": "password"    // "password" or "key"
    },
    {
      "host": "192.168.1.101",
      "port": 22,
      "username": "ubuntu",
      "password": "secure_pass",
      "auth_method": "password"
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "message": "Deployment completed: 2/2 successful",
  "results": [
    {
      "server": "deploy@192.168.1.100:22",
      "success": true,
      "message": "SSH key successfully deployed to deploy@192.168.1.100:22"
    },
    {
      "server": "ubuntu@192.168.1.101:22",
      "success": true,
      "message": "SSH key successfully deployed to ubuntu@192.168.1.101:22"
    }
  ]
}
```

---

### POST /api/ssh-keys/{key_id}/test

Test SSH connection using the key.

**Request Body:**
```json
{
  "host": "192.168.1.100",
  "port": 22,
  "username": "deploy"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "SSH connection successful: SSH connection successful"
}
```

**Response (400 Bad Request - on failure):**
```json
{
  "success": false,
  "message": "Connection test failed: Authentication failed"
}
```

---

### GET /api/ssh-keys/{key_id}/private

Get the private key (use with extreme caution!).

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Production Server Key",
  "private_key": "-----BEGIN OPENSSH PRIVATE KEY-----\n...",
  "warning": "Keep this private key secure. Never share it or commit it to version control."
}
```

---

## Enhanced Pipeline Features

### POST /api/pipelines/{pipeline_id}/create-pr

Create a pull request with the generated pipeline YAML file and configuration changes.

**Request Body (all optional):**
```json
{
  "title": "Custom PR Title",
  "description": "Custom PR description with more details",
  "branch_name": "custom-pipeline-branch",
  "commit_message": "Custom commit message",
  "include_nginx_config": true
}
```

**Response (201 Created):**
```json
{
  "message": "Pull request created successfully",
  "pr_url": "https://bitbucket.org/workspace/repo/pull-requests/123",
  "branch_name": "pipeline-v1-1234567890",
  "pr_title": "Add CI/CD Pipeline Configuration (v1) - Languages: Python, JavaScript"
}
```

**Default PR Content:**
- **Title**: "Add CI/CD Pipeline Configuration (v{version}) - {detected_technologies}"
- **Description**: Comprehensive details including:
  - Pipeline version and status
  - Detected technologies (languages and frameworks)
  - Deployment configuration (server, subdomain, port, SSL, environment variables)
  - Test execution history (last 5 runs)
  - Next steps for the reviewer

**Error Responses:**
- `401`: Not authenticated
- `404`: Pipeline not found
- `400`: Pipeline must be in SUCCESS status
- `400`: PR already created for this pipeline
- `500`: Server error

---

### POST /api/pipelines/{pipeline_id}/trigger

Manually trigger pipeline execution via Bitbucket API with automatic retry mechanism.

**Request Body (all optional):**
```json
{
  "branch": "main",      // Branch to trigger pipeline on
  "retry": true,         // Enable automatic retry on failure
  "max_retries": 3       // Maximum number of retry attempts
}
```

**Response (200 OK):**
```json
{
  "message": "Pipeline triggered successfully",
  "execution": {
    "id": 42,
    "build_number": 123,
    "uuid": "{abc-def-ghi}",
    "status": "BUILDING",
    "started_at": "2024-01-15T14:30:00Z",
    "retry_count": 0
  }
}
```

**Retry Mechanism:**
- Uses exponential backoff: 2^retry_count seconds between retries
- Retry sequence: 2s, 4s, 8s for max_retries=3
- Automatically logs failed attempts in database
- Returns detailed error after all retries exhausted

**Error Response (500 - all retries failed):**
```json
{
  "error": "Failed to connect to Bitbucket API",
  "retry_count": 3,
  "message": "Failed to trigger pipeline after 4 attempts"
}
```

---

### GET /api/pipelines/{pipeline_id}/logs

Get pipeline execution logs with advanced filtering and pagination.

**Query Parameters:**
- `execution_id` (optional): Specific execution ID (defaults to latest)
- `page` (optional, default: 1): Page number for pagination
- `per_page` (optional, default: 10, max: 50): Items per page
- `status` (optional): Filter by execution status (BUILDING, TESTING, DEPLOYING, SUCCESS, FAILED)
- `from_date` (optional): Filter from date (ISO format: 2024-01-15T00:00:00Z)
- `to_date` (optional): Filter to date (ISO format)
- `step_filter` (optional): Filter logs by step name (partial match, case-insensitive)

**Response (200 OK - with specific execution_id):**
```json
{
  "execution": {
    "id": 42,
    "build_number": 123,
    "uuid": "{abc-def}",
    "status": "COMPLETED",
    "started_at": "2024-01-15T14:30:00Z",
    "completed_at": "2024-01-15T14:35:30Z",
    "duration_seconds": 330,
    "trigger_type": "manual"
  },
  "steps": [
    {
      "name": "Build",
      "state": "COMPLETED",
      "started_on": "2024-01-15T14:30:10Z",
      "completed_on": "2024-01-15T14:32:00Z",
      "duration_in_seconds": 110,
      "log": "Step: Build\n...\nBuild completed successfully"
    },
    {
      "name": "Test",
      "state": "COMPLETED",
      "started_on": "2024-01-15T14:32:05Z",
      "completed_on": "2024-01-15T14:34:00Z",
      "duration_in_seconds": 115,
      "log": "Step: Test\n...\nAll tests passed"
    },
    {
      "name": "Deploy",
      "state": "COMPLETED",
      "started_on": "2024-01-15T14:34:05Z",
      "completed_on": "2024-01-15T14:35:30Z",
      "duration_in_seconds": 85,
      "log": "Step: Deploy\n...\nDeployment successful"
    }
  ]
}
```

**Response (200 OK - without execution_id, paginated history):**
```json
{
  "execution": {
    "id": 42,
    "build_number": 123,
    "uuid": "{abc-def}",
    "status": "COMPLETED",
    "started_at": "2024-01-15T14:30:00Z",
    "completed_at": "2024-01-15T14:35:30Z",
    "duration_seconds": 330,
    "trigger_type": "manual"
  },
  "steps": [...],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 25,
    "pages": 3
  },
  "executions_summary": [
    {
      "id": 42,
      "status": "SUCCESS",
      "build_number": 123,
      "started_at": "2024-01-15T14:30:00Z",
      "completed_at": "2024-01-15T14:35:30Z",
      "duration_seconds": 330,
      "trigger_type": "manual"
    },
    {
      "id": 41,
      "status": "FAILED",
      "build_number": 122,
      "started_at": "2024-01-15T13:00:00Z",
      "completed_at": "2024-01-15T13:05:00Z",
      "duration_seconds": 300,
      "trigger_type": "manual"
    }
  ]
}
```

**Filtering Examples:**

1. Get logs with errors only:
   ```
   GET /api/pipelines/123/logs?step_filter=error
   ```

2. Get execution history for last week:
   ```
   GET /api/pipelines/123/logs?from_date=2024-01-08T00:00:00Z&to_date=2024-01-15T23:59:59Z
   ```

3. Get only failed executions:
   ```
   GET /api/pipelines/123/logs?status=FAILED&page=1&per_page=20
   ```

---

## WebSocket Real-time Logs

Connect to WebSocket endpoint for real-time pipeline log streaming.

**WebSocket Connection:**
```javascript
const socket = io('http://your-backend-url', {
  withCredentials: true
});
```

### Event: subscribe_logs

Subscribe to real-time logs for a pipeline execution.

**Emit:**
```javascript
socket.emit('subscribe_logs', {
  pipeline_id: 123,
  execution_id: 42  // optional, will track latest if not provided
});
```

**Receive - subscribed:**
```javascript
socket.on('subscribed', (data) => {
  console.log('Subscribed to pipeline:', data);
  // {
  //   pipeline_id: 123,
  //   execution_id: 42,
  //   room: 'pipeline_123'
  // }
});
```

---

### Event: pipeline_logs

Real-time log updates from pipeline execution.

**Receive:**
```javascript
socket.on('pipeline_logs', (data) => {
  console.log('Log update:', data);
  // {
  //   pipeline_id: 123,
  //   execution_id: 42,
  //   build_number: 123,
  //   status: 'BUILDING',
  //   steps: [
  //     {
  //       name: 'Build',
  //       state: 'RUNNING',
  //       duration_seconds: 45,
  //       log_preview: 'Building application...\nInstalling dependencies...',
  //       log_full: '... complete log text ...',
  //       has_log: true,
  //       started_on: '2024-01-15T14:30:10Z',
  //       completed_on: null,
  //       is_new: true,         // true if step just started
  //       state_changed: false  // true if step state changed
  //     }
  //   ],
  //   total_steps: 3,
  //   duration_seconds: 45,
  //   timestamp: 1705328445.123
  // }
});
```

**Key Features:**
- Only changed steps are included in updates
- `is_new`: Indicates a step just started
- `state_changed`: Indicates step status changed
- `log_preview`: First 1000 characters for quick display
- `log_full`: Complete log for detailed view
- Updates every 5 seconds while pipeline is running

---

### Event: pipeline_status

Status change notifications.

**Receive:**
```javascript
socket.on('pipeline_status', (data) => {
  console.log('Status changed:', data);
  // {
  //   pipeline_id: 123,
  //   execution_id: 42,
  //   status: 'SUCCESS',
  //   previous_status: 'DEPLOYING',
  //   bitbucket_status: 'COMPLETED',  // Original Bitbucket status
  //   duration_seconds: 330,
  //   completed_at: '2024-01-15T14:35:30Z',
  //   final: true,                    // true if pipeline completed
  //   timestamp: 1705328730.456
  // }
});
```

**Status Values:**
- `BUILDING`: Pipeline is building
- `TESTING`: Running tests
- `DEPLOYING`: Deploying to servers
- `SUCCESS`: Pipeline completed successfully
- `FAILED`: Pipeline failed

---

### Event: log_error

Error occurred during log streaming.

**Receive:**
```javascript
socket.on('log_error', (data) => {
  console.error('Log streaming error:', data);
  // {
  //   pipeline_id: 123,
  //   execution_id: 42,
  //   error: 'Failed to fetch logs from Bitbucket',
  //   timestamp: 1705328730.456
  // }
});
```

---

### Event: log_timeout

Log streaming timeout reached.

**Receive:**
```javascript
socket.on('log_timeout', (data) => {
  console.warn('Log streaming timeout:', data);
  // {
  //   pipeline_id: 123,
  //   execution_id: 42,
  //   message: 'Log streaming timeout reached',
  //   timestamp: 1705328730.456
  // }
});
```

---

### Event: unsubscribe_logs

Unsubscribe from pipeline logs.

**Emit:**
```javascript
socket.emit('unsubscribe_logs', {
  pipeline_id: 123
});
```

**Receive:**
```javascript
socket.on('unsubscribed', (data) => {
  console.log('Unsubscribed from pipeline:', data);
  // { pipeline_id: 123 }
});
```

---

### Event: get_execution_status

Get current status of a pipeline execution.

**Emit:**
```javascript
socket.emit('get_execution_status', {
  execution_id: 42
});
```

**Receive:**
```javascript
socket.on('execution_status', (data) => {
  console.log('Execution status:', data);
  // {
  //   execution_id: 42,
  //   pipeline_id: 123,
  //   status: 'SUCCESS',
  //   build_number: 123,
  //   started_at: '2024-01-15T14:30:00Z',
  //   completed_at: '2024-01-15T14:35:30Z',
  //   duration_seconds: 330,
  //   trigger_type: 'manual'
  // }
});
```

---

### Event: subscribe_pipeline_status

Subscribe to status updates for a specific pipeline (not a specific execution).

**Emit:**
```javascript
socket.emit('subscribe_pipeline_status', {
  pipeline_id: 123
});
```

**Receive:**
```javascript
socket.on('subscribed_status', (data) => {
  console.log('Subscribed to pipeline status:', data);
  // {
  //   pipeline_id: 123,
  //   current_status: 'SUCCESS'
  // }
});
```

---

## Error Handling

All endpoints follow consistent error response format:

**Error Response Structure:**
```json
{
  "error": "Detailed error message explaining what went wrong"
}
```

**Common HTTP Status Codes:**
- `200 OK`: Request succeeded
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters or data
- `401 Unauthorized`: Not authenticated or invalid credentials
- `403 Forbidden`: Authenticated but not authorized for this action
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., PR already exists)
- `500 Internal Server Error`: Server error, check logs for details

**Example Error Responses:**

```json
// 401 Unauthorized
{
  "error": "Not authenticated"
}

// 400 Bad Request
{
  "error": "name is required"
}

// 404 Not Found
{
  "error": "Pipeline not found"
}

// 409 Conflict
{
  "error": "PR already created for this pipeline",
  "pr_url": "https://bitbucket.org/workspace/repo/pull-requests/123"
}

// 500 Internal Server Error
{
  "error": "Failed to connect to Bitbucket API"
}
```

---

## Complete Usage Example

### SSH Key Workflow

```javascript
// 1. Create SSH key
const createResponse = await fetch('/api/ssh-keys', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({
    name: 'Production Server',
    description: 'Key for production deployments',
    key_type: 'ed25519'
  })
});
const { ssh_key, private_key } = await createResponse.json();

// 2. Deploy to servers
const deployResponse = await fetch(`/api/ssh-keys/${ssh_key.id}/deploy`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({
    servers: [
      {
        host: '192.168.1.100',
        port: 22,
        username: 'deploy',
        password: 'secure_password',
        auth_method: 'password'
      }
    ]
  })
});

// 3. Test connection
const testResponse = await fetch(`/api/ssh-keys/${ssh_key.id}/test`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({
    host: '192.168.1.100',
    port: 22,
    username: 'deploy'
  })
});
```

### Pipeline Execution with Real-time Logs

```javascript
// 1. Trigger pipeline
const triggerResponse = await fetch(`/api/pipelines/123/trigger`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({
    branch: 'main',
    retry: true,
    max_retries: 3
  })
});
const { execution } = await triggerResponse.json();

// 2. Connect to WebSocket for real-time logs
const socket = io('http://backend-url', { withCredentials: true });

socket.emit('subscribe_logs', {
  pipeline_id: 123,
  execution_id: execution.id
});

// 3. Listen for updates
socket.on('pipeline_logs', (data) => {
  console.log('Logs:', data);
  // Update UI with log data
});

socket.on('pipeline_status', (data) => {
  console.log('Status:', data.status);
  if (data.final) {
    console.log('Pipeline completed!');
    socket.emit('unsubscribe_logs', { pipeline_id: 123 });
  }
});

// 4. Create PR after success
if (finalStatus === 'SUCCESS') {
  const prResponse = await fetch(`/api/pipelines/123/create-pr`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      title: 'Add CI/CD Pipeline Configuration',
      include_nginx_config: true
    })
  });
  const { pr_url } = await prResponse.json();
  console.log('PR created:', pr_url);
}
```

---

## Security Considerations

1. **SSH Private Keys**: Private keys are stored in the database. In production:
   - Encrypt private keys at rest using strong encryption (AES-256)
   - Consider using a secrets management service (HashiCorp Vault, AWS Secrets Manager)
   - Never log or expose private keys in API responses except during initial creation

2. **SSH Key Deployment**: 
   - Requires credentials (password or existing key) to deploy
   - Use temporary credentials when possible
   - Implement IP whitelisting for SSH connections
   - Rotate keys regularly

3. **WebSocket Authentication**:
   - WebSocket connections use session authentication
   - Verify user permissions before sending sensitive data
   - Implement rate limiting to prevent abuse

4. **API Rate Limiting**:
   - Implement rate limiting on all endpoints
   - Especially important for trigger endpoint to prevent abuse

5. **Audit Logging**:
   - Log all SSH key operations (create, deploy, delete)
   - Log all pipeline triggers and who initiated them
   - Store audit logs separately from application logs

---

## Database Migration

To add the new SSH key table to your database:

```bash
cd backend
python migrate_deployment_features.py
```

Or manually create tables:

```python
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
```
