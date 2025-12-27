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

4. Access the web interface:
   - **Frontend**: http://localhost:8088
   - **Backend API**: http://localhost:5088
   - **Coolify UI**: http://localhost:9000

## Configuration

### Required Environment Variables

All configuration is managed through environment variables. See `.env.example` for a complete list with descriptions.

#### Essential Variables (Required)

- **OAuth Credentials**:
  - `BITBUCKET_CLIENT_ID`: Your Bitbucket OAuth client ID
  - `BITBUCKET_CLIENT_SECRET`: Your Bitbucket OAuth client secret
  - `GITHUB_CLIENT_ID`: Your GitHub OAuth client ID
  - `GITHUB_CLIENT_SECRET`: Your GitHub OAuth client secret

- **API Keys**:
  - `GEMINI_API_KEY`: Your Gemini 3 Pro API key (can be configured via UI)

- **Security**:
  - `SECRET_KEY`: Application secret key for session management (change in production!)

#### Database Configuration

- `POSTGRES_USER`: PostgreSQL username (default: `devops`)
- `POSTGRES_PASSWORD`: PostgreSQL password (default: `devops`)
- `POSTGRES_DB`: PostgreSQL database name (default: `devops_tool`)
- `DATABASE_URL`: Full PostgreSQL connection string

#### Domain Configuration

- `ROOT_DOMAIN`: Root domain for the application (e.g., `crl.to`)
- `FRONTEND_URL`: Full URL where the frontend is accessible
- `REACT_APP_API_URL`: Backend API URL for frontend calls

#### Coolify Configuration (Optional)

- `COOLIFY_BASE_URL`: Internal Coolify service URL (default: `http://coolify`)
- `COOLIFY_API_TOKEN`: API token from Coolify dashboard
- `COOLIFY_AUTO_CLEANUP_HOURS`: Hours before auto-cleanup of test deployments (default: `24`)
- `COOLIFY_URL`: External URL where Coolify UI is accessible
- `COOLIFY_APP_KEY`: Coolify application key (generate with: `openssl rand -base64 32`)
- `COOLIFY_DB_PASSWORD`: PostgreSQL password for Coolify's database

#### Redis Configuration

- `REDIS_URL`: Redis connection URL for Celery tasks (default: `redis://redis:6379/0`)

#### Flask Configuration

- `FLASK_ENV`: Set to `production` for production deployment

### Port Configuration

The application exposes the following ports:

- **Backend API**: `5088` (internal port 5000)
- **Frontend**: `8088` (internal port 80)
- **Coolify UI**: `9000-9004` (internal port 80, additional ports for deployments)
- **PostgreSQL**: `5432` (internal only)
- **Redis**: `6379` (internal only)

### Environment Setup

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and update the following required variables:
   - `SECRET_KEY`: Generate with `openssl rand -base64 32`
   - `BITBUCKET_CLIENT_ID` and `BITBUCKET_CLIENT_SECRET`
   - `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET`
   - `GEMINI_API_KEY`
   - Update callback URLs to match your domain

3. For Coolify integration, also configure:
   - `COOLIFY_API_TOKEN`: Generate from Coolify dashboard
   - `COOLIFY_APP_KEY`: Generate with `openssl rand -base64 32`

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

## Production Deployment

### Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- Docker Engine 20.10+ and Docker Compose 2.0+
- Domain name with DNS configured
- SSL certificate (recommended)

### Deployment Steps

#### 1. Server Setup

```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker (if not already installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose-plugin -y

# Add your user to docker group (optional)
sudo usermod -aG docker $USER
```

#### 2. Application Deployment

```bash
# Clone the repository
git clone <repository-url>
cd Devops-tool

# Configure environment
cp .env.example .env
nano .env  # Edit with your configuration

# Generate secure keys
export SECRET_KEY=$(openssl rand -base64 32)
export COOLIFY_APP_KEY=$(openssl rand -base64 32)
echo "SECRET_KEY=$SECRET_KEY" >> .env
echo "COOLIFY_APP_KEY=base64:$COOLIFY_APP_KEY" >> .env

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

#### 3. Verify Deployment

```bash
# Check health endpoints
curl http://localhost:5088/health     # Backend health
curl http://localhost:8088            # Frontend
curl http://localhost:9000            # Coolify UI

# Check service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs coolify
```

#### 4. Database Migrations

The application automatically creates database tables on startup. To manually run migrations:

```bash
# Enter backend container
docker-compose exec backend bash

# Run migrations (if using flask-migrate)
flask db upgrade

# Exit container
exit
```

### SSL Certificate Setup

#### Option 1: Using Let's Encrypt with Nginx

1. Install Certbot:
```bash
sudo apt-get install certbot python3-certbot-nginx -y
```

2. Obtain SSL certificate:
```bash
sudo certbot --nginx -d launchpad.crl.to
```

3. Update nginx configuration (`nginx-proxy.conf`) with SSL:
```nginx
server {
    listen 80;
    server_name launchpad.crl.to;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name launchpad.crl.to;
    
    ssl_certificate /etc/letsencrypt/live/launchpad.crl.to/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/launchpad.crl.to/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    
    # ... rest of your configuration
}
```

4. Set up auto-renewal:
```bash
sudo certbot renew --dry-run
```

#### Option 2: Using Existing SSL Certificate

If you have an existing SSL certificate, copy it to the server:

```bash
# Copy certificate files
sudo mkdir -p /etc/ssl/certs/launchpad
sudo cp your-cert.crt /etc/ssl/certs/launchpad/
sudo cp your-cert.key /etc/ssl/certs/launchpad/
sudo chmod 600 /etc/ssl/certs/launchpad/your-cert.key
```

Update nginx configuration to use your certificate paths.

### Nginx Proxy Setup

1. Install Nginx (if not using as a container):
```bash
sudo apt-get install nginx -y
```

2. Copy the proxy configuration:
```bash
sudo cp nginx-proxy.conf /etc/nginx/sites-available/launchpad.crl.to
sudo ln -s /etc/nginx/sites-available/launchpad.crl.to /etc/nginx/sites-enabled/
```

3. Test and reload Nginx:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

4. Enable Nginx on boot:
```bash
sudo systemctl enable nginx
```

### Firewall Configuration

```bash
# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow SSH (if not already allowed)
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable
```

### Docker Compose Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart a specific service
docker-compose restart backend

# View logs
docker-compose logs -f [service-name]

# Rebuild and restart after code changes
docker-compose up -d --build

# Remove all containers and volumes (CAUTION: deletes data)
docker-compose down -v

# Scale a service (if needed)
docker-compose up -d --scale backend=2
```

### Monitoring and Logs

All services are configured with JSON file logging. Logs are rotated automatically:
- Maximum log file size: 10MB
- Maximum log files kept: 3 per service

View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f coolify

# Last 100 lines
docker-compose logs --tail=100 backend

# Since specific time
docker-compose logs --since 1h backend
```

### Health Checks

All services include health checks:

- **Backend**: HTTP check on `/health` endpoint
- **Frontend**: HTTP check on root endpoint
- **Database**: PostgreSQL `pg_isready` check
- **Redis**: Redis `PING` command
- **Coolify**: HTTP check on `/api/health` endpoint

Check health status:
```bash
docker-compose ps
```

Services showing `(healthy)` status are running correctly.

### Backup and Restore

#### Backup

```bash
# Backup PostgreSQL database
docker-compose exec db pg_dump -U devops devops_tool > backup_$(date +%Y%m%d).sql

# Backup Coolify database
docker-compose exec coolify-db pg_dump -U coolify coolify > coolify_backup_$(date +%Y%m%d).sql

# Backup volumes
docker run --rm -v devops-tool_postgres_data:/data -v $(pwd):/backup ubuntu tar czf /backup/postgres_data_backup.tar.gz /data
```

#### Restore

```bash
# Restore PostgreSQL database
cat backup_20240101.sql | docker-compose exec -T db psql -U devops devops_tool

# Restore Coolify database
cat coolify_backup_20240101.sql | docker-compose exec -T coolify-db psql -U coolify coolify
```

### Troubleshooting

#### Services won't start

```bash
# Check logs
docker-compose logs

# Check disk space
df -h

# Check Docker status
sudo systemctl status docker
```

#### Database connection errors

```bash
# Verify database is healthy
docker-compose ps db

# Check database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

#### Coolify integration issues

```bash
# Verify Coolify is running
docker-compose ps coolify

# Test Coolify health
curl http://localhost:9000/api/health

# Check Coolify logs
docker-compose logs coolify
```

#### Frontend can't reach backend

```bash
# Verify REACT_APP_API_URL in .env
grep REACT_APP_API_URL .env

# Check nginx proxy configuration
cat nginx-proxy.conf

# Test backend directly
curl http://localhost:5088/health
```

### Updating the Application

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up -d --build

# Check status
docker-compose ps
```

### Production Checklist

- [ ] Set strong `SECRET_KEY` in `.env`
- [ ] Set strong `COOLIFY_APP_KEY` in `.env`
- [ ] Configure OAuth credentials
- [ ] Update all callback URLs to production domain
- [ ] Set up SSL certificates
- [ ] Configure firewall rules
- [ ] Set `FLASK_ENV=production`
- [ ] Configure regular database backups
- [ ] Set up monitoring and alerting
- [ ] Test all OAuth flows
- [ ] Test Coolify integration
- [ ] Verify health checks are passing
- [ ] Document your specific deployment configuration

## License

See LICENSE file for details.

## Coolify Integration

This project includes comprehensive Coolify integration for test deployment management. Coolify is a self-hosted PaaS that allows you to deploy and manage applications easily.

### Features

- 🚀 **One-Click Test Deployments**: Create test deployments directly from pipeline UI
- 📊 **Real-Time Monitoring**: Track deployment status with automatic polling every 10 seconds
- 📝 **Log Viewing**: Access build and runtime logs for debugging
- 🔄 **Lifecycle Management**: Start, stop, and delete deployments with ease
- 🧹 **Automatic Cleanup**: Background job automatically removes deployments older than 24 hours
- 🔗 **Reverse Proxy**: Access Coolify UI through `/coolify` path

### Quick Start

1. Configure Coolify credentials in `.env`:
   ```bash
   COOLIFY_BASE_URL=http://coolify
   COOLIFY_API_TOKEN=your-api-token-here
   COOLIFY_AUTO_CLEANUP_HOURS=24
   ```

2. Start services:
   ```bash
   docker-compose up -d
   ```

3. Access Coolify UI:
   - Direct: http://localhost:9000
   - Through proxy: http://launchpad.crl.to/coolify

4. Create test deployment:
   - Navigate to a pipeline
   - Click "🚀 Test with Coolify"
   - Monitor status in real-time

### Documentation

For detailed information, see [COOLIFY_INTEGRATION.md](./COOLIFY_INTEGRATION.md)

### API Endpoints

- `GET /api/coolify/health` - Check Coolify availability
- `POST /api/coolify/deployments` - Create test deployment
- `GET /api/coolify/deployments/<id>` - Get deployment status
- `GET /api/coolify/deployments/<id>/logs` - Retrieve logs
- `DELETE /api/coolify/deployments/<id>` - Delete deployment

