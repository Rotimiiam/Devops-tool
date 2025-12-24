# DevOps Tool - Automated Bitbucket Pipeline Manager

A self-hosted web application that automates Bitbucket pipeline creation and testing for your repositories.

## Features

- **OAuth Integration**: Connect your Bitbucket and GitHub accounts
- **Repository Management**: Select and manage repositories from connected accounts
- **GitHub to Bitbucket Migration**: Automatically recreate GitHub repos in Bitbucket
- **AI-Powered Pipeline Generation**: Use Gemini 3 Pro to generate and iterate on pipeline configurations
- **Self-Hosted Pipeline Runner**: Test pipelines internally before deployment
- **Automated Pull Requests**: Create PRs with working pipeline configurations
- **Domain Management**: Configure root domains and subdomains for your tools

## Prerequisites

- Docker and Docker Compose
- Bitbucket OAuth credentials (Key and Secret)
- GitHub OAuth credentials (Client ID and Secret)
- Gemini 3 Pro API key

## Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd Devops-tool
```

2. Copy the example environment file and configure:
```bash
cp .env.example .env
# Edit .env with your OAuth credentials and API keys
```

3. Start the application:
```bash
docker-compose up -d
```

4. Access the web interface at `http://localhost:3000`

## Configuration

### Environment Variables

- `BITBUCKET_CLIENT_ID`: Your Bitbucket OAuth client ID
- `BITBUCKET_CLIENT_SECRET`: Your Bitbucket OAuth client secret
- `GITHUB_CLIENT_ID`: Your GitHub OAuth client ID
- `GITHUB_CLIENT_SECRET`: Your GitHub OAuth client secret
- `GEMINI_API_KEY`: Your Gemini 3 Pro API key (can be configured via UI)
- `SECRET_KEY`: Application secret key for session management
- `DATABASE_URL`: Database connection string
- `ROOT_DOMAIN`: Root domain for the application

## Architecture

- **Backend**: Python/Flask REST API
- **Frontend**: React-based web interface
- **Database**: PostgreSQL for persistent storage
- **Pipeline Runner**: Docker-based Bitbucket pipeline runner

## Usage

1. **Connect Accounts**: Navigate to Settings and connect your Bitbucket and GitHub accounts via OAuth
2. **Configure API Key**: Add your Gemini 3 Pro API key in Settings
3. **Select Repository**: Choose a repository from your connected accounts
4. **Generate Pipeline**: The system will automatically generate a pipeline configuration
5. **Test & Iterate**: The pipeline is tested in the self-hosted runner and refined using AI
6. **Deploy**: Once successful, a PR is automatically created with the working configuration

## Development

To run in development mode:

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m app.main

# Frontend
cd frontend
npm install
npm start
```

## License

See LICENSE file for details.
