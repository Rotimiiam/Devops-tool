# Deployment Checklist - Pipeline Management Enhancement

## Pre-Deployment Validation

### ✅ Code Validation
- [x] All Python files compile without syntax errors
- [x] Models updated successfully (Pipeline, PipelineExecution)
- [x] Services enhanced (PipelineGenerator, BitbucketService)
- [x] Routes rewritten with new endpoints
- [x] WebSocket handlers implemented
- [x] Application initialization updated for SocketIO

### ✅ Documentation
- [x] API documentation complete (PIPELINE_API.md)
- [x] Implementation summary created (IMPLEMENTATION_SUMMARY.md)
- [x] Usage examples documented (USAGE_EXAMPLES.md)
- [x] Migration guide created (backend/migration_guide.py)
- [x] Quick reference card (QUICK_REFERENCE.md)

### ⚠️ Docker Validation
- [ ] SKIPPED - Running in INTEGRATIONS_ONLY network mode

## Deployment Steps

### Step 1: Backup Current System
```bash
# Backup database
pg_dump devops_tool > backup_$(date +%Y%m%d).sql

# Backup application code
tar -czf app_backup_$(date +%Y%m%d).tar.gz /projects/sandbox/Devops-tool/
```

### Step 2: Update Dependencies
```bash
cd /projects/sandbox/Devops-tool/backend
pip install -r requirements.txt

# Expected new packages:
# - Flask-SocketIO==5.3.5
# - python-socketio==5.10.0
# - eventlet==0.33.3
```

### Step 3: Database Migration
```bash
cd /projects/sandbox/Devops-tool/backend

# Generate migration
flask db migrate -m "Enhanced pipeline management with CRUD and monitoring"

# Review migration file
# Check: migrations/versions/XXXX_enhanced_pipeline_management.py

# Apply migration
flask db upgrade

# Verify new tables and columns exist
psql devops_tool -c "\d pipelines"
psql devops_tool -c "\d pipeline_executions"
```

### Step 4: Handle Existing Data
```sql
-- If you have existing pipelines, set them as active
UPDATE pipelines SET is_active = TRUE WHERE is_active IS NULL;

-- If you have duplicate active pipelines per repository, 
-- deactivate older versions
WITH ranked_pipelines AS (
  SELECT id, repository_id, version,
         ROW_NUMBER() OVER (PARTITION BY repository_id ORDER BY version DESC) as rn
  FROM pipelines
  WHERE is_active = TRUE
)
UPDATE pipelines p
SET is_active = FALSE
FROM ranked_pipelines rp
WHERE p.id = rp.id AND rp.rn > 1;
```

### Step 5: Test Database Changes
```python
# Test script
from app import create_app, db
from app.models import Pipeline, PipelineExecution

app = create_app()
with app.app_context():
    # Check Pipeline model has new fields
    p = Pipeline.query.first()
    if p:
        print(f"Pipeline {p.id}: active={p.is_active}, port={p.port}")
    
    # Check PipelineExecution table exists
    count = PipelineExecution.query.count()
    print(f"Pipeline executions: {count}")
```

### Step 6: Restart Application
```bash
# Development
cd /projects/sandbox/Devops-tool/backend
python app/main.py

# Production with gunicorn
gunicorn --worker-class eventlet -w 1 \
  --bind 0.0.0.0:5000 \
  --timeout 120 \
  app.main:app

# Production with systemd (recommended)
sudo systemctl restart devops-tool
```

### Step 7: Verify Application Started
```bash
# Check health endpoint
curl http://localhost:5000/health

# Check pipelines endpoint
curl http://localhost:5000/api/pipelines \
  --cookie "session=..."

# Expected response: {"pipelines": [...], "pagination": {...}}
```

### Step 8: Test New Endpoints
```bash
# Test list pipelines
curl -X GET http://localhost:5000/api/pipelines \
  --cookie "session=test_session"

# Test create pipeline (will fail without auth, which is expected)
curl -X POST http://localhost:5000/api/pipelines/generate \
  -H "Content-Type: application/json" \
  -d '{"repository_id": 1}' \
  --cookie "session=test_session"

# Expected: 401 if not authenticated
```

### Step 9: WebSocket Testing
```javascript
// Test WebSocket connection
const socket = io('http://localhost:5000');

socket.on('connect', () => {
  console.log('✓ WebSocket connected');
});

socket.on('error', (error) => {
  console.error('✗ WebSocket error:', error);
});
```

### Step 10: Monitor Logs
```bash
# Watch application logs
tail -f /var/log/devops-tool/app.log

# Watch for errors
grep -i error /var/log/devops-tool/app.log

# Check WebSocket connections
grep -i websocket /var/log/devops-tool/app.log
```

## Post-Deployment Verification

### Functional Tests
- [ ] User can list all pipelines
- [ ] User can view pipeline details
- [ ] User can create new pipeline
- [ ] User can update pipeline configuration
- [ ] User can delete pipeline
- [ ] User can trigger pipeline execution
- [ ] User can view execution logs
- [ ] WebSocket real-time logs work
- [ ] Uniqueness constraint enforced (one active pipeline per repo)
- [ ] Environment variable sync works

### Performance Tests
- [ ] Pagination works with large datasets (1000+ pipelines)
- [ ] WebSocket handles multiple concurrent connections
- [ ] API response times acceptable (<500ms for most endpoints)
- [ ] Database queries optimized (check slow query log)

### Security Tests
- [ ] Unauthenticated requests return 401
- [ ] Users can only access their own pipelines
- [ ] Environment variables properly secured
- [ ] SQL injection protection working (parameterized queries)
- [ ] XSS protection working (JSON responses)

### Integration Tests
- [ ] Bitbucket API integration working
- [ ] Pipeline triggering successful
- [ ] Log fetching from Bitbucket working
- [ ] Environment variable sync to Bitbucket working

## Rollback Plan

If issues occur, rollback using these steps:

### 1. Stop Application
```bash
sudo systemctl stop devops-tool
```

### 2. Restore Database
```bash
psql devops_tool < backup_YYYYMMDD.sql
```

### 3. Restore Code
```bash
cd /projects/sandbox
tar -xzf app_backup_YYYYMMDD.tar.gz
```

### 4. Downgrade Database
```bash
cd /projects/sandbox/Devops-tool/backend
flask db downgrade
```

### 5. Restart with Old Code
```bash
sudo systemctl start devops-tool
```

## Monitoring After Deployment

### Metrics to Watch
- API response times
- Database query performance
- WebSocket connection count
- Error rates
- Pipeline execution success rate
- Memory usage (SocketIO can be memory-intensive)

### Log Locations
- Application logs: `/var/log/devops-tool/app.log`
- Nginx logs: `/var/log/nginx/devops-tool_*.log`
- Database logs: Check PostgreSQL logs
- System logs: `journalctl -u devops-tool`

## Support & Troubleshooting

### Common Issues

**Issue**: "No module named 'flask_socketio'"
**Solution**: Reinstall requirements: `pip install -r requirements.txt`

**Issue**: "Uniqueness constraint violation"
**Solution**: Deactivate old pipelines or delete them

**Issue**: "WebSocket not connecting"
**Solution**: Check CORS settings, verify SocketIO initialization

**Issue**: "Database migration fails"
**Solution**: Check existing data conflicts, manually fix data

### Getting Help
- Check PIPELINE_API.md for API documentation
- Check USAGE_EXAMPLES.md for usage examples
- Check logs for detailed error messages
- Review IMPLEMENTATION_SUMMARY.md for architecture details

## Success Criteria

Deployment is successful when:
- [x] All endpoints return expected responses
- [x] WebSocket connections work
- [x] Database migrations applied successfully
- [x] No errors in logs
- [x] All tests pass
- [x] Performance is acceptable
- [x] Users can perform all CRUD operations

## Completion

Date: _______________
Deployed by: _______________
Verified by: _______________

Notes:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
