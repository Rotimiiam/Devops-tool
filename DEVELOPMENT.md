# Development Guide

## Project Structure

```
Devops-tool/
├── backend/                    # Python Flask backend
│   ├── app/
│   │   ├── __init__.py        # Flask app factory
│   │   ├── config.py          # Configuration management
│   │   ├── main.py            # Application entry point
│   │   ├── models.py          # Database models
│   │   ├── routes/            # API routes
│   │   │   ├── auth.py        # OAuth authentication
│   │   │   ├── repositories.py # Repository management
│   │   │   ├── pipelines.py   # Pipeline operations
│   │   │   ├── domains.py     # Domain management
│   │   │   └── settings.py    # User settings
│   │   ├── services/          # Business logic
│   │   │   ├── github_service.py
│   │   │   ├── bitbucket_service.py
│   │   │   ├── gemini_service.py
│   │   │   ├── pipeline_generator.py
│   │   │   └── pipeline_runner.py
│   │   └── utils/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # React frontend
│   ├── public/
│   ├── src/
│   │   ├── pages/             # Page components
│   │   ├── services/          # API client
│   │   ├── App.js
│   │   └── index.js
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
├── .env.example
└── README.md
```

## Setting Up OAuth Applications

### Bitbucket OAuth

1. Go to your Bitbucket workspace settings
2. Navigate to OAuth consumers
3. Create a new OAuth consumer:
   - Name: DevOps Tool
   - Callback URL: `http://localhost:5000/api/auth/bitbucket/callback`
   - Permissions: `repository`, `repository:write`, `account`
4. Copy the Key and Secret to your `.env` file

### GitHub OAuth

1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Create a new OAuth App:
   - Application name: DevOps Tool
   - Homepage URL: `http://localhost:3000`
   - Authorization callback URL: `http://localhost:5000/api/auth/github/callback`
3. Copy the Client ID and Secret to your `.env` file

## API Endpoints

### Authentication
- `GET /api/auth/bitbucket/login` - Initiate Bitbucket OAuth
- `GET /api/auth/bitbucket/callback` - Bitbucket OAuth callback
- `GET /api/auth/github/login` - Initiate GitHub OAuth
- `GET /api/auth/github/callback` - GitHub OAuth callback
- `GET /api/auth/status` - Check authentication status
- `POST /api/auth/logout` - Logout

### Repositories
- `GET /api/repositories/github` - List GitHub repositories
- `GET /api/repositories/bitbucket` - List Bitbucket repositories
- `GET /api/repositories/` - List all managed repositories
- `GET /api/repositories/:id` - Get repository details
- `POST /api/repositories/migrate` - Migrate GitHub repo to Bitbucket
- `DELETE /api/repositories/:id` - Delete repository record

### Pipelines
- `POST /api/pipelines/generate` - Generate pipeline configuration
- `POST /api/pipelines/test` - Test pipeline in self-hosted runner
- `POST /api/pipelines/iterate` - Use Gemini to fix failed pipeline
- `POST /api/pipelines/create-pr` - Create PR with working pipeline
- `GET /api/pipelines/repository/:repo_id` - List pipelines for repository
- `GET /api/pipelines/:id` - Get pipeline details

### Domains
- `GET /api/domains/` - List domains
- `GET /api/domains/:id` - Get domain details
- `POST /api/domains/` - Create domain
- `PUT /api/domains/:id` - Update domain
- `DELETE /api/domains/:id` - Delete domain

### Settings
- `GET /api/settings/` - Get user settings
- `POST /api/settings/gemini-api-key` - Update Gemini API key
- `DELETE /api/settings/gemini-api-key` - Remove Gemini API key

## Database Schema

### Users
- OAuth tokens for Bitbucket and GitHub
- Gemini API key
- Connection metadata

### Repositories
- Source repository information
- Bitbucket repository details
- Migration status

### Pipelines
- Configuration (YAML)
- Test results
- Version history
- PR information

### Domains
- Root domains and subdomains
- Parent-child relationships
- Active/inactive status

## Development Workflow

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

The backend will run on `http://localhost:5000`

### Frontend Development

```bash
cd frontend
npm install
npm start
```

The frontend will run on `http://localhost:3000`

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Docker Development

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up -d --build
```

## Environment Variables

See `.env.example` for all available configuration options.

Required variables:
- `BITBUCKET_CLIENT_ID` and `BITBUCKET_CLIENT_SECRET`
- `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET`
- `SECRET_KEY` (for session management)

Optional variables:
- `GEMINI_API_KEY` (can be configured via UI)
- `DATABASE_URL` (defaults to PostgreSQL in Docker)
- `ROOT_DOMAIN` (for domain management)

## Troubleshooting

### OAuth Callback Issues
- Ensure callback URLs match exactly in OAuth app settings
- Check that FRONTEND_URL is correctly set in .env

### Docker Socket Issues
- The backend needs access to Docker socket for pipeline runner
- Ensure `/var/run/docker.sock` is mounted in docker-compose.yml

### Database Migrations
```bash
# Access backend container
docker-compose exec backend bash

# Run migrations
flask db upgrade
```

### API Connection Issues
- Check that backend is running on port 5000
- Verify CORS settings allow frontend origin
- Check browser console for errors

## Production Deployment

1. Update `.env` with production values
2. Set `FLASK_ENV=production`
3. Use proper SECRET_KEY (not the default)
4. Set up proper domain and SSL certificates
5. Update OAuth callback URLs to production domain
6. Consider using a proper database backup strategy
7. Set up monitoring and logging

## Security Considerations

- Never commit `.env` file to version control
- Use strong SECRET_KEY in production
- Keep OAuth credentials secure
- Regularly rotate API keys
- Use HTTPS in production
- Implement rate limiting for APIs
- Validate and sanitize all user inputs
- Keep dependencies updated

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues and questions, please open an issue on the repository.
