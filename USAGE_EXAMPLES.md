# Pipeline Management System - Usage Examples

## Prerequisites
- User must be authenticated via OAuth (Bitbucket/GitHub)
- Bitbucket token must be configured for Bitbucket operations

## 1. Create a New Pipeline

```bash
curl -X POST http://localhost:5000/api/pipelines/generate \
  -H "Content-Type: application/json" \
  -d '{
    "repository_id": 1,
    "deployment_server": "prod-server.example.com",
    "subdomain": "myapp",
    "port": 8080,
    "server_ip": "192.168.1.100",
    "environment_variables": {
      "DATABASE_URL": "postgresql://user:pass@localhost/db",
      "API_KEY": "secret-key-123",
      "DEBUG": "false"
    }
  }' \
  --cookie "session=your_session_cookie"
```

**Response:**
```json
{
  "message": "Pipeline generated successfully",
  "pipeline": {
    "id": 5,
    "version": 1,
    "config": "image: python:3.11\npipelines:\n  ...",
    "status": "PLANNED",
    "nginx_config": "server {\n  listen 443 ssl http2;\n  ..."
  }
}
```

## 2. List All Pipelines

```bash
# Get first page (20 items)
curl -X GET "http://localhost:5000/api/pipelines?page=1&per_page=20" \
  --cookie "session=your_session_cookie"

# Filter by status
curl -X GET "http://localhost:5000/api/pipelines?status=SUCCESS" \
  --cookie "session=your_session_cookie"
```

## 3. Get Pipeline Details

```bash
curl -X GET http://localhost:5000/api/pipelines/5 \
  --cookie "session=your_session_cookie"
```

**Response includes:**
- Complete pipeline configuration (YAML)
- Repository information
- Execution history (last 10 executions)
- Environment variables
- Nginx configuration
- All deployment settings

## 4. Update Pipeline Configuration

```bash
curl -X PUT http://localhost:5000/api/pipelines/5 \
  -H "Content-Type: application/json" \
  -d '{
    "subdomain": "newsubdomain",
    "port": 8081,
    "server_ip": "192.168.1.200",
    "environment_variables": {
      "DATABASE_URL": "postgresql://newdb",
      "NEW_VAR": "new_value"
    },
    "ssl_enabled": true
  }' \
  --cookie "session=your_session_cookie"
```

## 5. Regenerate Pipeline (After Code Changes)

When repository code changes and you want to regenerate the pipeline based on new analysis:

```bash
curl -X POST http://localhost:5000/api/pipelines/5/regenerate \
  --cookie "session=your_session_cookie"
```

This will:
1. Re-clone and analyze the repository
2. Detect updated languages/frameworks
3. Generate new optimized pipeline configuration
4. Increment pipeline version
5. Keep existing deployment settings

## 6. Trigger Pipeline Execution

```bash
# Trigger on main branch (default)
curl -X POST http://localhost:5000/api/pipelines/5/trigger \
  -H "Content-Type: application/json" \
  -d '{"branch": "main"}' \
  --cookie "session=your_session_cookie"

# Trigger on feature branch
curl -X POST http://localhost:5000/api/pipelines/5/trigger \
  -H "Content-Type: application/json" \
  -d '{"branch": "feature/new-feature"}' \
  --cookie "session=your_session_cookie"
```

**Response:**
```json
{
  "message": "Pipeline triggered successfully",
  "execution": {
    "id": 42,
    "build_number": 15,
    "uuid": "{abc-123-def-456}",
    "status": "BUILDING",
    "started_at": "2024-01-15T12:00:00Z"
  }
}
```

## 7. Get Pipeline Logs

```bash
# Get logs for latest execution
curl -X GET http://localhost:5000/api/pipelines/5/logs \
  --cookie "session=your_session_cookie"

# Get logs for specific execution
curl -X GET "http://localhost:5000/api/pipelines/5/logs?execution_id=42" \
  --cookie "session=your_session_cookie"
```

## 8. Sync Environment Variables to Bitbucket

```bash
curl -X POST http://localhost:5000/api/pipelines/5/sync-env \
  --cookie "session=your_session_cookie"
```

This will sync all environment variables from the pipeline to Bitbucket repository variables (secured).

## 9. Delete Pipeline

```bash
# Delete without remote cleanup
curl -X DELETE http://localhost:5000/api/pipelines/5 \
  --cookie "session=your_session_cookie"

# Delete with remote cleanup (removes bitbucket-pipelines.yml)
curl -X DELETE "http://localhost:5000/api/pipelines/5?cleanup_remote=true" \
  --cookie "session=your_session_cookie"
```

## 10. WebSocket Real-Time Logs

### JavaScript Example

```javascript
import io from 'socket.io-client';

// Connect to WebSocket server
const socket = io('http://localhost:5000', {
  withCredentials: true
});

// Handle connection
socket.on('connect', () => {
  console.log('Connected to WebSocket');
  
  // Subscribe to logs for pipeline execution
  socket.emit('subscribe_logs', {
    pipeline_id: 5,
    execution_id: 42  // Optional: specific execution
  });
});

// Handle subscription confirmation
socket.on('subscribed', (data) => {
  console.log('Subscribed to pipeline:', data.pipeline_id);
});

// Handle real-time log updates (every 5 seconds)
socket.on('log_update', (data) => {
  console.log('Status:', data.status);
  data.steps.forEach(step => {
    console.log(`  - ${step.name}: ${step.state}`);
    if (step.log_preview) {
      console.log(`    ${step.log_preview}`);
    }
  });
});

// Handle completion
socket.on('log_complete', (data) => {
  console.log('Pipeline completed!');
  console.log('Final status:', data.status);
  console.log('Duration:', data.duration_seconds, 'seconds');
  
  // Unsubscribe
  socket.emit('unsubscribe_logs', {
    pipeline_id: 5
  });
});

// Handle errors
socket.on('log_error', (data) => {
  console.error('Error streaming logs:', data.error);
});

// Handle disconnection
socket.on('disconnect', () => {
  console.log('Disconnected from WebSocket');
});
```

### Python Example

```python
import socketio

# Create a Socket.IO client
sio = socketio.Client()

# Connect to the server
@sio.event
def connect():
    print('Connected to WebSocket')
    sio.emit('subscribe_logs', {
        'pipeline_id': 5,
        'execution_id': 42
    })

@sio.event
def subscribed(data):
    print(f"Subscribed to pipeline {data['pipeline_id']}")

@sio.event
def log_update(data):
    print(f"Status: {data['status']}")
    for step in data['steps']:
        print(f"  - {step['name']}: {step['state']}")

@sio.event
def log_complete(data):
    print(f"Pipeline completed: {data['status']}")
    print(f"Duration: {data['duration_seconds']} seconds")
    sio.emit('unsubscribe_logs', {'pipeline_id': 5})
    sio.disconnect()

@sio.event
def log_error(data):
    print(f"Error: {data['error']}")

@sio.event
def disconnect():
    print('Disconnected from WebSocket')

# Connect to the server
sio.connect('http://localhost:5000')
sio.wait()
```

## Common Workflows

### Workflow 1: Initial Setup for New Repository

1. Authenticate via OAuth
2. Create/import repository
3. Generate pipeline with deployment settings
4. Review generated pipeline configuration
5. Sync environment variables to Bitbucket
6. Create Pull Request with pipeline config
7. Merge PR
8. Trigger first deployment

### Workflow 2: Update Existing Pipeline

1. Update pipeline configuration (new subdomain/port)
2. Regenerate pipeline if code changed
3. Test pipeline locally
4. Trigger deployment
5. Monitor via WebSocket logs
6. Verify deployment success

### Workflow 3: Troubleshooting Failed Pipeline

1. Get pipeline logs for failed execution
2. Review error messages in execution history
3. Update configuration if needed
4. Use Gemini to iterate and fix (existing endpoint)
5. Re-trigger pipeline
6. Monitor until success

## Tips

1. **Uniqueness Constraint**: Each repository can only have ONE active pipeline. If you try to create a second active pipeline, you'll get a 409 error. Delete the old one first or set is_active=false.

2. **Environment Variables**: Store sensitive values in Bitbucket variables instead of in the database. Use the sync endpoint to update them.

3. **Real-time Monitoring**: Use WebSocket for real-time log streaming during deployments. Much better UX than polling.

4. **Nginx Configuration**: The generated nginx config includes SSL setup. Run the certbot command on your server to obtain certificates.

5. **Project Type Detection**: The system auto-detects React, Vue, Django, Flask, Node.js, etc. and generates optimized pipelines for each.

6. **SSH Keys**: Add your deployment SSH private key to Bitbucket repository variables as `SSH_PRIVATE_KEY` for deployments to work.

## Error Codes

- `200` - Success
- `201` - Created
- `400` - Bad request (validation error)
- `401` - Unauthorized (not authenticated)
- `404` - Not found
- `409` - Conflict (active pipeline already exists)
- `500` - Internal server error
