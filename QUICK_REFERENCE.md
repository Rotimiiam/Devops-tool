# Pipeline Management - Quick Reference Card

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| **GET** | `/api/pipelines` | List all pipelines (paginated) |
| **GET** | `/api/pipelines/{id}` | Get pipeline details + history |
| **PUT** | `/api/pipelines/{id}` | Update pipeline configuration |
| **DELETE** | `/api/pipelines/{id}` | Delete pipeline |
| **POST** | `/api/pipelines/generate` | Create new pipeline |
| **POST** | `/api/pipelines/{id}/regenerate` | Re-analyze & regenerate |
| **POST** | `/api/pipelines/{id}/trigger` | Trigger execution |
| **GET** | `/api/pipelines/{id}/logs` | Get execution logs |
| **POST** | `/api/pipelines/{id}/sync-env` | Sync environment variables |

## Pipeline Status Flow

```
draft → PLANNED → BUILDING → TESTING → DEPLOYING → SUCCESS
                                                  ↓
                                               FAILED
```

## Supported Project Types

- **React** - Build optimization, static serving
- **Vue** - Build optimization with npm/yarn
- **Angular** - AOT compilation
- **Django** - WSGI, migrations, static files
- **Flask/FastAPI** - WSGI/ASGI server setup
- **Node.js/Express** - PM2 management
- **Next.js** - SSR/SSG with PM2
- **Docker** - Multi-stage builds
- **Full-stack** - Coordinated deployment

## Quick Start

### 1. Create Pipeline
```bash
curl -X POST http://localhost:5000/api/pipelines/generate \
  -H "Content-Type: application/json" \
  -d '{"repository_id": 1, "subdomain": "myapp", "port": 8080}' \
  --cookie "session=..."
```

### 2. Trigger Deployment
```bash
curl -X POST http://localhost:5000/api/pipelines/5/trigger \
  -H "Content-Type: application/json" \
  -d '{"branch": "main"}' \
  --cookie "session=..."
```

### 3. Watch Logs (WebSocket)
```javascript
const socket = io('http://localhost:5000');
socket.emit('subscribe_logs', {pipeline_id: 5, execution_id: 42});
socket.on('log_update', (data) => console.log(data));
```

## Key Features

✅ ONE active pipeline per repository (enforced)
✅ Real-time log streaming via WebSocket
✅ Auto-generated nginx configs with SSL
✅ Environment variable sync to Bitbucket
✅ Execution history tracking
✅ Rollback support

## Important Notes

- Authentication required for all endpoints
- Database migrations needed before first run
- SSH keys stored in Bitbucket variables
- Pagination: default 20 items per page

## Documentation

- **Full API Docs**: PIPELINE_API.md
- **Usage Examples**: USAGE_EXAMPLES.md
- **Implementation Details**: IMPLEMENTATION_SUMMARY.md
- **Migration Guide**: backend/migration_guide.py
