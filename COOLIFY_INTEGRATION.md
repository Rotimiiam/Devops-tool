# Coolify Integration Guide

This guide provides comprehensive information about the Coolify integration for test deployment creation, monitoring, and management.

## Overview

The Coolify integration allows you to create test deployments directly from your pipeline configurations. Coolify is a self-hosted Platform-as-a-Service (PaaS) that makes it easy to deploy applications without complex configuration.

## Features

### ✅ Implemented Features

1. **Coolify Service Integration**
   - Full REST API client for Coolify
   - Automatic retry mechanism for failed requests
   - Health check endpoint to verify Coolify availability

2. **Test Deployment Creation**
   - Create test deployments from pipeline configurations
   - Support for Docker images and Dockerfiles
   - Environment variable configuration
   - Port mapping support
   - Auto-start option for immediate deployment

3. **Deployment Monitoring**
   - Real-time status polling (every 10 seconds)
   - Status tracking: pending, building, deploying, running, failed, stopped
   - Deployment URL tracking
   - Health status monitoring

4. **Deployment Logs**
   - Build logs retrieval
   - Runtime logs retrieval
   - Combined logs view
   - Real-time log streaming support

5. **Deployment Management**
   - Start/stop deployments
   - Delete deployments
   - List all deployments with filtering
   - Deployment cleanup

6. **Automatic Cleanup**
   - Background job (Celery task) for automatic cleanup
   - Configurable age threshold (default: 24 hours)
   - Manual cleanup trigger endpoint
   - Graceful shutdown before deletion

7. **Frontend Integration**
   - "Test with Coolify" button in pipeline UI
   - Deployment status display
   - Log viewer
   - Start/stop/delete controls
   - Real-time status updates

8. **Error Handling**
   - Retry mechanism for API failures
   - Graceful degradation when Coolify is unavailable
   - Comprehensive error messages
   - Fallback to cached data

## Architecture

### Backend Components

#### 1. Database Model (`CoolifyDeployment`)
```python
class CoolifyDeployment(db.Model):
    - id: Primary key
    - pipeline_id: Reference to pipeline
    - coolify_deployment_id: Coolify UUID
    - coolify_application_id: Coolify app ID
    - status: Current status
    - application_name: Deployment name
    - docker_image: Docker image (optional)
    - dockerfile_path: Path to Dockerfile (optional)
    - environment_variables: JSON dict
    - port_mappings: JSON list
    - deployment_url: Public URL
    - build_logs: Cached build logs
    - runtime_logs: Cached runtime logs
    - error_message: Error details
    - created_at: Creation timestamp
    - updated_at: Last update timestamp
    - cleaned_at: Cleanup timestamp
```

#### 2. Coolify Integration Service (`coolify_integration.py`)
- `CoolifyIntegrationService`: Main service class
- API methods:
  - `check_health()`: Verify Coolify availability
  - `create_deployment()`: Create new deployment
  - `get_deployment_status()`: Get current status
  - `get_deployment_logs()`: Retrieve logs
  - `start_deployment()`: Trigger deployment
  - `stop_deployment()`: Stop running deployment
  - `delete_deployment()`: Remove deployment
  - `list_deployments()`: List all deployments
  - `poll_deployment_status()`: Poll until terminal state

#### 3. API Routes (`routes/coolify.py`)
- `GET /api/coolify/health`: Check Coolify health
- `POST /api/coolify/deployments`: Create deployment
- `GET /api/coolify/deployments`: List deployments
- `GET /api/coolify/deployments/<id>`: Get deployment status
- `GET /api/coolify/deployments/<id>/logs`: Get logs
- `POST /api/coolify/deployments/<id>/start`: Start deployment
- `POST /api/coolify/deployments/<id>/stop`: Stop deployment
- `DELETE /api/coolify/deployments/<id>`: Delete deployment
- `POST /api/coolify/cleanup/old`: Cleanup old deployments

#### 4. Background Tasks (`tasks.py`)
- `cleanup_old_coolify_deployments`: Hourly cleanup task
- `poll_deployment_status`: Background status polling

### Frontend Components

#### 1. API Client (`services/api.js`)
```javascript
coolifyAPI.checkHealth()
coolifyAPI.createDeployment(data)
coolifyAPI.listDeployments(params)
coolifyAPI.getDeployment(id)
coolifyAPI.deleteDeployment(id)
coolifyAPI.startDeployment(id)
coolifyAPI.stopDeployment(id)
coolifyAPI.getDeploymentLogs(id, logType)
coolifyAPI.cleanupOld(ageHours)
```

#### 2. Pipeline UI Integration
- "Test with Coolify" button
- Deployment list display
- Status badges with color coding
- Log viewer with expand/collapse
- Action buttons (stop, delete)
- Real-time status polling

## Configuration

### Environment Variables

Add these to your `.env` file or docker-compose environment:

```bash
# Coolify Configuration
COOLIFY_BASE_URL=http://coolify:9000
COOLIFY_API_TOKEN=your-coolify-api-token
COOLIFY_AUTO_CLEANUP_HOURS=24

# Optional: Coolify database password
COOLIFY_DB_PASSWORD=coolify
```

### Docker Compose Services

The integration includes these services:

1. **coolify**: Main Coolify application
2. **coolify-db**: PostgreSQL database for Coolify
3. **coolify-redis**: Redis for Coolify queue management

### Nginx Reverse Proxy

The nginx configuration routes `/coolify` to the Coolify instance:

```nginx
location /coolify {
    rewrite ^/coolify/(.*) /$1 break;
    proxy_pass http://localhost:9000;
    # ... additional proxy settings
}
```

## Usage

### Creating a Test Deployment

1. Navigate to a pipeline in the UI
2. Click "🚀 Test with Coolify" button
3. Deployment will be created and automatically started
4. Status updates every 10 seconds

### Viewing Deployment Status

1. Select a pipeline with deployments
2. View status badges (pending, building, deploying, running, failed, stopped)
3. Click deployment URL to access running application

### Viewing Logs

1. Click "View Logs" button on a deployment
2. See build and runtime logs
3. Logs are cached for offline viewing

### Managing Deployments

**Stop a deployment:**
```
Click "Stop" button → Deployment stops gracefully
```

**Delete a deployment:**
```
Click "Delete" button → Confirm → Deployment removed from Coolify
```

**Manual cleanup:**
```
POST /api/coolify/cleanup/old?age_hours=24
```

### API Usage Examples

#### Create Deployment
```javascript
const deployment = await coolifyAPI.createDeployment({
  pipeline_id: 1,
  application_name: "my-app-test",
  docker_image: "nginx:latest",
  environment_variables: {
    "NODE_ENV": "test",
    "API_KEY": "test-key"
  },
  port_mappings: [
    { container_port: 3000, host_port: 8080 }
  ],
  auto_start: true
});
```

#### Monitor Status
```javascript
const status = await coolifyAPI.getDeployment(deploymentId);
console.log(status.deployment.status); // 'running'
```

#### Get Logs
```javascript
const logs = await coolifyAPI.getDeploymentLogs(deploymentId, 'combined');
console.log(logs.logs.build_logs);
console.log(logs.logs.runtime_logs);
```

## Automatic Cleanup

The system automatically cleans up old deployments:

- **Schedule**: Every hour (configurable)
- **Age Threshold**: 24 hours (configurable via `COOLIFY_AUTO_CLEANUP_HOURS`)
- **Actions**: Stops and deletes deployments older than threshold
- **Database**: Marks as cleaned, preserves records

### Manual Cleanup

Trigger manual cleanup:

```bash
curl -X POST "http://localhost:5000/api/coolify/cleanup/old?age_hours=12"
```

## Status Lifecycle

```
pending → building → deploying → running
                          ↓
                       failed
                          ↓
                       stopped
```

**Terminal States:**
- `running`: Successfully deployed and running
- `failed`: Deployment or build failed
- `stopped`: Manually stopped or cleaned up

## Error Handling

### Retry Mechanism
- Automatic retry for failed API requests
- Maximum 3 retries with exponential backoff
- Configurable retry delay

### Graceful Degradation
- Uses cached data when Coolify unavailable
- Clear error messages in UI
- Continues operation with partial functionality

### Error Messages
- API errors include detailed messages
- Frontend displays user-friendly errors
- Logs capture technical details

## Monitoring and Observability

### Health Check
```bash
curl http://localhost:5000/api/coolify/health
```

Response:
```json
{
  "available": true,
  "status": "healthy",
  "version": "v4.x.x",
  "message": "Coolify service is available"
}
```

### Deployment Metrics
- Creation timestamp
- Update timestamp
- Cleanup timestamp
- Status history (via logs)

## Troubleshooting

### Coolify Not Available
**Symptom**: Health check fails  
**Solution**: 
1. Check Coolify container is running: `docker ps | grep coolify`
2. Verify network connectivity
3. Check COOLIFY_BASE_URL configuration

### Deployment Stuck in Building
**Symptom**: Status remains "building" for extended time  
**Solution**:
1. Check deployment logs for errors
2. Verify Docker image/Dockerfile validity
3. Check resource availability

### Logs Not Appearing
**Symptom**: Logs show "not available"  
**Solution**:
1. Wait for deployment to complete
2. Check Coolify API access
3. Verify deployment ID is correct

### Cleanup Not Running
**Symptom**: Old deployments not being cleaned  
**Solution**:
1. Verify Celery worker is running
2. Check Celery beat scheduler is active
3. Review task logs for errors

## Security Considerations

1. **API Token**: Store COOLIFY_API_TOKEN securely in environment variables
2. **Access Control**: Only authenticated users can create/manage deployments
3. **Resource Limits**: Configure resource limits in Coolify
4. **Network Isolation**: Use Docker networks for service isolation
5. **Log Sanitization**: Sensitive data in logs is not exposed in UI

## Performance

### Optimization Strategies
1. **Log Caching**: Logs cached in database to reduce API calls
2. **Status Polling**: Only active deployments polled
3. **Background Tasks**: Cleanup runs asynchronously
4. **Retry Backoff**: Prevents API flooding on errors

### Resource Usage
- **Database**: ~1KB per deployment record
- **API Calls**: ~6 calls per deployment lifecycle
- **Polling**: 1 call every 10 seconds per active deployment

## Future Enhancements

Potential improvements:
1. WebSocket support for real-time updates
2. Deployment templates
3. Multi-environment support
4. Rollback functionality
5. Performance metrics collection
6. Cost tracking
7. Auto-scaling configuration
8. Blue-green deployment support

## Support

For issues or questions:
1. Check Coolify documentation: https://coolify.io/docs
2. Review application logs
3. Check deployment status and logs
4. Verify configuration settings

## API Reference

See the comprehensive API documentation in the code comments:
- Backend: `/backend/app/routes/coolify.py`
- Frontend: `/frontend/src/services/api.js`
- Service: `/backend/app/services/coolify_integration.py`

## Migration Guide

To enable Coolify integration in existing installations:

1. Update `docker-compose.yml` with Coolify services
2. Add environment variables to configuration
3. Run database migrations: `flask db upgrade`
4. Update nginx configuration
5. Restart services: `docker-compose up -d`
6. Verify health check: `GET /api/coolify/health`

## Testing

Test the integration:

```bash
# Test health check
curl http://localhost:5000/api/coolify/health

# Create test deployment
curl -X POST http://localhost:5000/api/coolify/deployments \
  -H "Content-Type: application/json" \
  -d '{"pipeline_id": 1, "auto_start": true}'

# Check status
curl http://localhost:5000/api/coolify/deployments/1

# Get logs
curl http://localhost:5000/api/coolify/deployments/1/logs

# Delete deployment
curl -X DELETE http://localhost:5000/api/coolify/deployments/1
```
