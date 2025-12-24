# Quick Start Guide

## Prerequisites
- Docker and Docker Compose installed
- Bitbucket OAuth consumer credentials
- GitHub OAuth app credentials
- (Optional) Gemini 3 Pro API key

## Setup Steps

### 1. Configure Environment
```bash
cp .env.example .env
# Edit .env and add your OAuth credentials
```

### 2. Start Application
```bash
docker-compose up -d
```

### 3. Access Application
Open your browser and navigate to:
```
http://localhost:3000
```

### 4. Connect Services
1. Click "Get Started"
2. Click "Connect Bitbucket" and authorize
3. Click "Connect GitHub" and authorize
4. Go to Settings and add Gemini API key (optional, can be added later)

### 5. Use the Application

#### Migrate a Repository
1. Go to "Repositories" page
2. Select a GitHub repository from the dropdown
3. (Optional) Enter deployment server
4. Click "Migrate to Bitbucket"

#### Generate and Test Pipeline
1. Click "Pipelines" on a migrated repository
2. Click "Generate Pipeline"
3. Click "Test" to run the pipeline
4. If it fails, click "Fix with AI" to let Gemini improve it
5. Repeat testing and fixing until successful

#### Create Pull Request
1. Once pipeline is successful, click "Create PR"
2. The PR will be created in Bitbucket with the working configuration
3. Review and merge the PR in Bitbucket

## Common Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up -d --build

# View running containers
docker-compose ps

# Access database
docker-compose exec db psql -U devops -d devops_tool
```

## Troubleshooting

### OAuth Issues
- Verify callback URLs in OAuth app settings match .env configuration
- Check that ports 5000 (backend) and 3000 (frontend) are available

### Docker Issues
- Ensure Docker daemon is running
- Check Docker socket is accessible: `ls -l /var/run/docker.sock`
- Verify no port conflicts with other applications

### Database Issues
- Wait for database to be ready: `docker-compose logs db`
- Reset database: `docker-compose down -v` (WARNING: deletes all data)

## Getting Help

- Check detailed documentation in README.md
- See DEVELOPMENT.md for API documentation
- Review TESTING.md for comprehensive testing guide
- Check logs: `docker-compose logs -f backend`

## Directory Structure
```
Devops-tool/
├── backend/           # Python Flask API
├── frontend/          # React UI
├── docker-compose.yml # Docker orchestration
├── .env.example       # Environment template
├── setup.sh           # Setup script
├── README.md          # Main documentation
├── DEVELOPMENT.md     # Developer guide
└── TESTING.md         # Testing guide
```

## Support
For issues, please check the logs and documentation first.
Common issues and solutions are documented in TESTING.md.
