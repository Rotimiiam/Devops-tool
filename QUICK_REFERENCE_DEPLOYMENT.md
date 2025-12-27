# Quick Reference - Deployment Features

## Quick Start

```bash
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Run database migration
python3 backend/migrate_deployment_features.py

# 3. Start the application
python3 backend/app/main.py
```

## API Endpoints Quick Reference

### SSH Key Management
```bash
# Generate SSH key
POST /api/ssh-keys
{"name": "My Key", "key_type": "ed25519"}

# List keys
GET /api/ssh-keys

# Deploy key
POST /api/ssh-keys/{key_id}/deploy
{"servers": [{"host": "192.168.1.100", "port": 22, "username": "deploy", "password": "pass"}]}

# Test connection
POST /api/ssh-keys/{key_id}/test
{"host": "192.168.1.100", "port": 22, "username": "deploy"}

# Delete key
DELETE /api/ssh-keys/{key_id}
```

### Pipeline Operations
```bash
# Trigger pipeline with retry
POST /api/pipelines/{pipeline_id}/trigger
{"branch": "main", "retry": true, "max_retries": 3}

# Get logs with filtering
GET /api/pipelines/{pipeline_id}/logs?status=FAILED&page=1&per_page=20

# Create PR
POST /api/pipelines/{pipeline_id}/create-pr
{"title": "Add CI/CD Pipeline", "include_nginx_config": true}
```

### WebSocket Events
```javascript
// Subscribe to logs
socket.emit('subscribe_logs', {pipeline_id: 123, execution_id: 42});

// Listen for updates
socket.on('pipeline_logs', (data) => console.log(data));
socket.on('pipeline_status', (data) => console.log(data));

// Unsubscribe
socket.emit('unsubscribe_logs', {pipeline_id: 123});
```

## Key Features

| Feature | Endpoint | Method | Description |
|---------|----------|--------|-------------|
| Generate Key | `/api/ssh-keys` | POST | Create RSA/ED25519 key pair |
| Deploy Key | `/api/ssh-keys/{id}/deploy` | POST | Deploy to servers |
| Trigger Pipeline | `/api/pipelines/{id}/trigger` | POST | Trigger with retry |
| Stream Logs | WebSocket | - | Real-time log streaming |
| Create PR | `/api/pipelines/{id}/create-pr` | POST | Enhanced PR creation |
| Filter Logs | `/api/pipelines/{id}/logs` | GET | Paginated log filtering |

## File Structure

```
backend/
├── app/
│   ├── models.py                    # + SSHKey model
│   ├── __init__.py                  # + ssh_keys blueprint
│   ├── routes/
│   │   ├── ssh_keys.py             # NEW: 8 SSH endpoints
│   │   └── pipelines.py            # ENHANCED: 3 endpoints
│   ├── services/
│   │   ├── ssh_service.py          # NEW: SSH operations
│   │   └── bitbucket_service.py    # ENHANCED: PR creation
│   ├── utils/
│   │   └── log_utils.py            # NEW: Log filtering
│   └── websocket_handlers.py       # ENHANCED: 6 events
├── migrate_deployment_features.py  # NEW: Migration script
└── requirements.txt                 # + paramiko

docs/
├── DEPLOYMENT_FEATURES_API.md           # Complete API docs
├── IMPLEMENTATION_DEPLOYMENT_FEATURES.md # Implementation details
└── VALIDATION_REPORT.md                 # Validation results
```

## WebSocket Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `subscribe_logs` | Emit | Subscribe to pipeline logs |
| `pipeline_logs` | Listen | Real-time log updates |
| `pipeline_status` | Listen | Status change notifications |
| `log_error` | Listen | Error notifications |
| `log_timeout` | Listen | Timeout notifications |
| `get_execution_status` | Emit | Get current status |
| `subscribe_pipeline_status` | Emit | Subscribe to status |
| `unsubscribe_logs` | Emit | Unsubscribe from logs |

## Status Codes

| Status | Meaning |
|--------|---------|
| BUILDING | Pipeline is building |
| TESTING | Running tests |
| DEPLOYING | Deploying to servers |
| SUCCESS | Completed successfully |
| FAILED | Pipeline failed |

## Common Filters

### Log Filtering
- `status`: BUILDING, TESTING, DEPLOYING, SUCCESS, FAILED
- `from_date`: ISO format (2024-01-15T00:00:00Z)
- `to_date`: ISO format
- `step_filter`: Partial step name match
- `page`: Page number (default: 1)
- `per_page`: Items per page (max: 50)

### SSH Key Listing
- `active`: Filter by active status (true/false)

## Retry Mechanism

Default configuration:
- **Max Retries**: 3
- **Backoff**: Exponential (2^n seconds)
- **Sequence**: 2s → 4s → 8s

```json
{
  "retry": true,
  "max_retries": 3
}
```

## Security Notes

⚠️ **Private Keys**: Only returned on creation. Store securely!

⚠️ **Production**: Encrypt private keys at rest

⚠️ **SSH Deployment**: Use temporary credentials when possible

⚠️ **Rate Limiting**: Implement for production

## Testing Checklist

- [ ] Generate RSA and ED25519 keys
- [ ] Deploy key to test server
- [ ] Test SSH connection
- [ ] Trigger pipeline with retry
- [ ] Monitor via WebSocket
- [ ] Create PR with custom config
- [ ] Filter logs by status/date
- [ ] Test pagination

## Documentation

📖 **Full API Docs**: `DEPLOYMENT_FEATURES_API.md`

📖 **Implementation**: `IMPLEMENTATION_DEPLOYMENT_FEATURES.md`

📖 **Validation**: `VALIDATION_REPORT.md`

## Support

For detailed examples and troubleshooting, see the comprehensive documentation files.
