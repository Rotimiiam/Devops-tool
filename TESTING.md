# Testing Guide

This guide helps you test the DevOps Tool application features.

## Prerequisites

Before testing, ensure:
1. Docker and docker-compose are installed
2. `.env` file is configured with OAuth credentials
3. Application is running (`docker-compose up -d`)

## Manual Testing Workflow

### 1. Initial Setup and Authentication

**Test OAuth Integration:**

1. Navigate to `http://localhost:3000`
2. Click "Get Started" button
3. Test Bitbucket OAuth:
   - Click "Connect Bitbucket"
   - Authorize the application
   - Verify redirect back to dashboard
   - Check connection status shows "Bitbucket: ✓ [username]"

4. Test GitHub OAuth:
   - Click "Connect GitHub"
   - Authorize the application
   - Verify redirect back to dashboard
   - Check connection status shows "GitHub: ✓ [username]"

**Expected Results:**
- ✓ OAuth flows complete without errors
- ✓ User is redirected back to dashboard
- ✓ Connection status displays correctly
- ✓ Username is shown for each connected service

### 2. Configure Gemini API Key

**Test Settings Page:**

1. Navigate to Settings page
2. Enter Gemini API key in the form
3. Click "Save API Key"
4. Verify success message appears
5. Refresh page and verify key is marked as configured
6. Test removal:
   - Click "Remove API Key"
   - Confirm removal
   - Verify key is no longer configured

**Expected Results:**
- ✓ API key saves successfully
- ✓ Configuration persists across page reloads
- ✓ Removal works correctly

### 3. Repository Management

**Test GitHub Repository Migration:**

1. Navigate to Repositories page
2. Select a repository from GitHub dropdown
3. Optionally enter deployment server (e.g., `user@server.com:/path`)
4. Click "Migrate to Bitbucket"
5. Wait for migration to complete
6. Verify repository appears in "Your Repositories" list
7. Check status badge shows correct state

**Test Repository Listing:**

1. Verify all migrated repositories are displayed
2. Click "View in Bitbucket" link
3. Verify it opens the correct Bitbucket repository
4. Click "Pipelines" button
5. Verify navigation to pipelines page

**Test Repository Deletion:**

1. Click "Delete" on a repository
2. Confirm deletion
3. Verify repository is removed from list

**Expected Results:**
- ✓ Repository migration completes
- ✓ Repository appears in Bitbucket
- ✓ Repository record is saved in database
- ✓ Links work correctly
- ✓ Deletion removes record

### 4. Pipeline Generation and Testing

**Test Pipeline Generation:**

1. Navigate to a repository's pipeline page
2. Enter deployment server (optional)
3. Click "Generate Pipeline"
4. Verify pipeline configuration is created
5. Check pipeline appears in versions list
6. View pipeline details
7. Verify YAML configuration is displayed

**Test Pipeline Testing:**

1. Select a draft pipeline
2. Click "Test" button
3. Wait for test to complete
4. Verify test results are displayed
5. Check status changes to "success" or "failed"

**Expected Results:**
- ✓ Pipeline generates successfully
- ✓ Configuration is valid YAML
- ✓ Test runner executes pipeline
- ✓ Results are captured and displayed
- ✓ Status updates correctly

### 5. AI-Powered Pipeline Iteration

**Test Pipeline Fixing with Gemini:**

1. Have a failed pipeline (status: "failed")
2. Click "Fix with AI" button
3. Wait for Gemini to analyze and create new version
4. Verify new pipeline version is created
5. View the new configuration
6. Test the new version
7. Repeat until pipeline succeeds

**Expected Results:**
- ✓ Gemini analyzes error output
- ✓ New version is generated
- ✓ Version number increments
- ✓ Configuration is different from original
- ✓ Eventually pipeline should succeed

### 6. Pull Request Creation

**Test PR Creation:**

1. Have a successful pipeline (status: "success")
2. Click "Create PR" button
3. Wait for PR creation
4. Verify success message with PR URL
5. Click PR URL
6. Verify PR is created in Bitbucket
7. Check PR contains pipeline configuration file

**Expected Results:**
- ✓ PR is created in Bitbucket
- ✓ Branch is created with pipeline file
- ✓ PR title and description are appropriate
- ✓ Configuration file is correct

### 7. Domain Management

**Test Root Domain Creation:**

1. Navigate to Domains page
2. Click "Add Domain"
3. Enter domain name (e.g., "example.com")
4. Check "Root Domain"
5. Add description
6. Click "Create Domain"
7. Verify domain appears in list with ROOT badge

**Test Subdomain Creation:**

1. Click "Add Domain" again
2. Enter subdomain name (e.g., "api.example.com")
3. Select parent domain
4. Add description
5. Click "Create Domain"
6. Verify subdomain appears with parent reference

**Test Domain Deletion:**

1. Try to delete root domain with subdomains
2. Verify error message (cannot delete with subdomains)
3. Delete subdomain first
4. Then delete root domain
5. Verify both are removed

**Expected Results:**
- ✓ Only one root domain can be created
- ✓ Subdomains require parent domain
- ✓ Deletion validation works
- ✓ Parent-child relationships maintained

## API Testing with curl

### Test Health Check
```bash
curl http://localhost:5000/health
```

### Test Auth Status
```bash
curl -X GET http://localhost:5000/api/auth/status \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

### Test Repository List
```bash
curl -X GET http://localhost:5000/api/repositories/ \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

### Test Pipeline Generation
```bash
curl -X POST http://localhost:5000/api/pipelines/generate \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -d '{
    "repository_id": 1,
    "deployment_server": "user@server.com:/path"
  }'
```

## Automated Testing

### Backend Unit Tests

```bash
# Run all backend tests
cd backend
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_pipelines.py
```

### Frontend Tests

```bash
# Run all frontend tests
cd frontend
npm test

# Run with coverage
npm test -- --coverage

# Run specific test
npm test -- Home.test.js
```

### Integration Tests

```bash
# Test full OAuth flow
pytest tests/integration/test_oauth_flow.py

# Test pipeline generation to PR creation
pytest tests/integration/test_pipeline_workflow.py
```

## Common Issues and Solutions

### OAuth Redirect Issues
- **Problem:** OAuth callback fails
- **Solution:** Check callback URLs in OAuth app settings match exactly
- **Verify:** `BITBUCKET_CALLBACK_URL` and `GITHUB_CALLBACK_URL` in .env

### Pipeline Runner Fails
- **Problem:** Pipeline tests fail to run
- **Solution:** Ensure Docker socket is mounted
- **Verify:** Check docker-compose.yml has `/var/run/docker.sock` volume

### Gemini API Errors
- **Problem:** Pipeline iteration fails
- **Solution:** Verify API key is correct and has quota
- **Verify:** Test key at https://makersuite.google.com/

### Database Connection Issues
- **Problem:** Backend fails to start
- **Solution:** Wait for database to be ready
- **Verify:** `docker-compose logs db` shows healthy status

### CORS Errors
- **Problem:** Frontend can't reach backend
- **Solution:** Check FRONTEND_URL in backend .env
- **Verify:** CORS origins allow localhost:3000

## Performance Testing

### Test Pipeline Runner Performance
```bash
# Time pipeline execution
time docker-compose exec backend python -c "
from app.services.pipeline_runner import PipelineRunner
runner = PipelineRunner()
result = runner.run_pipeline('image: atlassian/default-image:3\npipelines:\n  default:\n    - step:\n        script:\n          - echo test')
print(result)
"
```

### Test API Response Times
```bash
# Use Apache Bench
ab -n 100 -c 10 http://localhost:5000/health

# Or use curl with timing
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:5000/api/repositories/
```

## Security Testing

### Test Session Management
1. Login and get session cookie
2. Try accessing protected endpoints without cookie
3. Verify 401 Unauthorized response
4. Logout and verify session is cleared
5. Try accessing with old session cookie

### Test Input Validation
1. Send invalid repository IDs
2. Send malformed YAML in pipeline config
3. Send SQL injection attempts in domain names
4. Verify all return appropriate error messages

### Test OAuth Token Security
1. Verify tokens are encrypted in database
2. Check tokens are not exposed in API responses
3. Verify refresh tokens work correctly
4. Test token expiration handling

## Load Testing

```bash
# Install k6
# Create load test script
cat > load-test.js << 'EOF'
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  vus: 10,
  duration: '30s',
};

export default function() {
  let response = http.get('http://localhost:5000/health');
  check(response, { 'status was 200': (r) => r.status == 200 });
  sleep(1);
}
EOF

# Run load test
k6 run load-test.js
```

## Monitoring During Testing

### Watch Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# With timestamps
docker-compose logs -f -t backend
```

### Monitor Resource Usage
```bash
# Container stats
docker stats

# Specific container
docker stats devops-tool_backend_1
```

### Check Database
```bash
# Connect to database
docker-compose exec db psql -U devops -d devops_tool

# View tables
\dt

# View users
SELECT id, email, bitbucket_username, github_username FROM users;

# View repositories
SELECT id, name, source, status FROM repositories;

# View pipelines
SELECT id, repository_id, version, status FROM pipelines;
```

## Test Checklist

Before marking testing complete, verify:

- [ ] OAuth authentication works for Bitbucket
- [ ] OAuth authentication works for GitHub
- [ ] Gemini API key can be configured
- [ ] GitHub repositories can be listed
- [ ] Bitbucket repositories can be listed
- [ ] Repository migration works
- [ ] Pipeline generation creates valid config
- [ ] Pipeline testing executes successfully
- [ ] Failed pipelines can be fixed with AI
- [ ] Successful pipelines can create PRs
- [ ] Root domains can be created
- [ ] Subdomains can be created with parent
- [ ] Domain deletion validation works
- [ ] All pages are accessible
- [ ] Navigation works correctly
- [ ] Error messages are helpful
- [ ] Success messages appear
- [ ] Loading states show correctly
- [ ] Data persists across page reloads

## Reporting Issues

When reporting issues, include:
1. Steps to reproduce
2. Expected behavior
3. Actual behavior
4. Browser console errors (if frontend)
5. Backend logs (`docker-compose logs backend`)
6. Environment details (OS, Docker version)
7. Screenshots if applicable
