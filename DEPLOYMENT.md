# Deployment Guide

## Bitbucket Repository
Repository URL: https://bitbucket.org/curaceldev/devops-tool

## Application Configuration
The application has been configured to run on **port 5080**.

### Access URLs
- Frontend: http://localhost:5080
- Backend API: http://localhost:5080/api

## Bitbucket Pipeline
The pipeline is configured in `bitbucket-pipelines.yml` and will automatically:
1. Build Docker images for frontend and backend
2. Start all services (PostgreSQL, Redis, Backend, Frontend)
3. Run health checks
4. Verify the application is accessible on port 5080

### Pipeline Triggers
- **Default**: Runs on any branch push
- **Main branch**: Full build, test, and deploy
- **Pull requests**: Test build only

## Local Development
To run the application locally on port 5080:

```bash
docker-compose up -d
```

Access the application at http://localhost:5080

## Environment Variables
Make sure to configure the following in your Bitbucket repository settings or `.env` file:
- `BITBUCKET_CLIENT_ID`
- `BITBUCKET_CLIENT_SECRET`
- `GITHUB_CLIENT_ID`
- `GITHUB_CLIENT_SECRET`
- `GEMINI_API_KEY`
- `SECRET_KEY`

## Next Steps
1. Configure environment variables in Bitbucket repository settings
2. Enable Bitbucket Pipelines in your repository
3. Push changes to trigger the pipeline
4. Monitor the pipeline execution in Bitbucket
