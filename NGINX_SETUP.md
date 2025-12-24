# Nginx Setup for launchpad.crl.to

This guide will help you configure Nginx to route traffic from launchpad.crl.to to your application running on port 5080.

## Prerequisites

1. EC2 instance with Nginx installed
2. DNS A record pointing launchpad.crl.to to your EC2 IP
3. Application running on port 5080
4. SSH access configured in Bitbucket

## Bitbucket Repository Variables

Configure these variables in your Bitbucket repository settings (Repository Settings > Pipelines > Repository variables):

1. **EC2_HOST**: Your EC2 instance IP or hostname (e.g., `ec2-xx-xx-xx-xx.compute.amazonaws.com`)
2. **EC2_USER**: SSH user for EC2 (usually `ubuntu` or `ec2-user`)

The pipeline uses Bitbucket's built-in SSH key management (Repository Settings > SSH keys).

## Installation Steps

### 1. Install Nginx on EC2

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx

# Amazon Linux
sudo yum install nginx
```

### 2. Deploy Nginx Configuration

```bash
# Copy the configuration file to your EC2
scp nginx-proxy.conf $EC2_USER@$EC2_HOST:/tmp/

# SSH into EC2
ssh $EC2_USER@$EC2_HOST

# Move config to nginx directory
sudo mv /tmp/nginx-proxy.conf /etc/nginx/sites-available/launchpad.crl.to

# Create symbolic link to enable the site
sudo ln -s /etc/nginx/sites-available/launchpad.crl.to /etc/nginx/sites-enabled/

# Remove default site if needed
sudo rm /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 3. Install Docker and Docker Compose on EC2

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version

# Log out and back in for group changes to take effect
```

### 4. Update OAuth Callback URLs

Update your OAuth application settings:

**Bitbucket:**
- Callback URL: `https://launchpad.crl.to/api/auth/bitbucket/callback`

**GitHub:**
- Callback URL: `https://launchpad.crl.to/api/auth/github/callback`

### 5. Configure Environment Variables on EC2

SSH into your EC2 instance and create the `.env` file:

```bash
ssh $EC2_USER@$EC2_HOST
cd /home/$USER/devops-tool

# Create .env file
nano .env
```

Add your environment variables:

```bash
# Domain Configuration
ROOT_DOMAIN=crl.to
FRONTEND_URL=http://launchpad.crl.to

# OAuth Callbacks
BITBUCKET_CLIENT_ID=your-bitbucket-client-id
BITBUCKET_CLIENT_SECRET=your-bitbucket-client-secret
BITBUCKET_CALLBACK_URL=http://launchpad.crl.to/api/auth/bitbucket/callback

GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GITHUB_CALLBACK_URL=http://launchpad.crl.to/api/auth/github/callback

# API Keys
GEMINI_API_KEY=your-gemini-api-key
SECRET_KEY=your-secret-key-change-in-production

# API URL for frontend
REACT_APP_API_URL=http://launchpad.crl.to/api

# Database
POSTGRES_USER=devops
POSTGRES_PASSWORD=your-secure-password
POSTGRES_DB=devops_tool

# Flask
FLASK_ENV=production
```

### 6. Deploy via Bitbucket Pipeline

Push to the main branch to trigger automatic deployment:

```bash
git push bitbucket main
```

The pipeline will:
1. Connect to your EC2 via SSH
2. Clone/pull the latest code
3. Build Docker images
4. Start all services on port 5080
5. Run health checks

## Verification

1. Check Nginx status:
```bash
sudo systemctl status nginx
```

2. Test the application:
```bash
curl http://launchpad.crl.to
```

3. Check Nginx logs:
```bash
sudo tail -f /var/log/nginx/launchpad.crl.to.access.log
sudo tail -f /var/log/nginx/launchpad.crl.to.error.log
```

4. Check application logs on EC2:
```bash
ssh $EC2_USER@$EC2_HOST
cd /home/$USER/devops-tool
docker-compose logs -f
```

## Firewall Configuration

Ensure ports 80 and 5080 are open in EC2 Security Group:

**EC2 Security Group Inbound Rules:**
- Port 80 (HTTP) - Source: 0.0.0.0/0
- Port 22 (SSH) - Source: Your IP or Bitbucket IPs
- Port 5080 - Source: localhost only (not needed if using nginx proxy)

**On the server (if using UFW):**
```bash
# UFW (Ubuntu)
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

## Troubleshooting

### Pipeline Fails to Connect
- Verify SSH_KEY is base64 encoded correctly
- Check EC2_HOST and EC2_USER variables in Bitbucket
- Ensure SSH key is added to EC2 `~/.ssh/authorized_keys`

### Connection Refused
Check if the application is running on port 5080:
```bash
ssh $EC2_USER@$EC2_HOST
curl http://localhost:5080
docker-compose ps
```

### 502 Bad Gateway
Check application logs:
```bash
ssh $EC2_USER@$EC2_HOST
cd /home/$USER/devops-tool
docker-compose logs backend
docker-compose logs frontend
```

### Docker Permission Issues
Add user to docker group:
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

## Security Recommendations

1. Restrict SSH access to Bitbucket IPs only
2. Use strong passwords for database
3. Keep SECRET_KEY secure and random
4. Regular security updates: `sudo apt update && sudo apt upgrade`
5. Monitor logs for suspicious activity
6. Consider adding SSL/TLS later with Let's Encrypt

## Access URLs

- **Production**: http://launchpad.crl.to
- **API**: http://launchpad.crl.to/api
- **Local Development**: http://localhost:5080

## Adding SSL Later (Optional)

If you want to add SSL later:

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d launchpad.crl.to

# Certbot will automatically update your nginx config
```
