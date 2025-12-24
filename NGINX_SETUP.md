# Nginx Setup for launchpad.crl.to

This guide will help you configure Nginx to route traffic from launchpad.crl.to to your application running on port 5080.

## Prerequisites

1. Nginx installed on your server
2. SSL certificate for launchpad.crl.to
3. DNS A record pointing launchpad.crl.to to your server IP
4. Application running on port 5080

## Installation Steps

### 1. Install Nginx (if not already installed)

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx

# CentOS/RHEL
sudo yum install nginx
```

### 2. Obtain SSL Certificate

Using Let's Encrypt (recommended):

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d launchpad.crl.to
```

Or manually place your SSL certificates at:
- Certificate: `/etc/ssl/certs/launchpad.crl.to.crt`
- Private Key: `/etc/ssl/private/launchpad.crl.to.key`

### 3. Deploy Nginx Configuration

```bash
# Copy the configuration file
sudo cp nginx-proxy.conf /etc/nginx/sites-available/launchpad.crl.to

# Create symbolic link to enable the site
sudo ln -s /etc/nginx/sites-available/launchpad.crl.to /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### 4. Update OAuth Callback URLs

Update your OAuth application settings:

**Bitbucket:**
- Callback URL: `https://launchpad.crl.to/api/auth/bitbucket/callback`

**GitHub:**
- Callback URL: `https://launchpad.crl.to/api/auth/github/callback`

### 5. Update Environment Variables

Create or update your `.env` file:

```bash
# Domain Configuration
ROOT_DOMAIN=crl.to
FRONTEND_URL=https://launchpad.crl.to

# OAuth Callbacks
BITBUCKET_CALLBACK_URL=https://launchpad.crl.to/api/auth/bitbucket/callback
GITHUB_CALLBACK_URL=https://launchpad.crl.to/api/auth/github/callback

# API URL for frontend
REACT_APP_API_URL=https://launchpad.crl.to/api
```

### 6. Restart Application

```bash
docker-compose down
docker-compose up -d
```

## Verification

1. Check Nginx status:
```bash
sudo systemctl status nginx
```

2. Test the application:
```bash
curl https://launchpad.crl.to
```

3. Check Nginx logs:
```bash
sudo tail -f /var/log/nginx/launchpad.crl.to.access.log
sudo tail -f /var/log/nginx/launchpad.crl.to.error.log
```

## Firewall Configuration

Ensure ports 80 and 443 are open:

```bash
# UFW (Ubuntu)
sudo ufw allow 'Nginx Full'

# Firewalld (CentOS)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## Troubleshooting

### SSL Certificate Issues
If using Let's Encrypt, ensure auto-renewal is enabled:
```bash
sudo certbot renew --dry-run
```

### Connection Refused
Check if the application is running on port 5080:
```bash
curl http://localhost:5080
docker-compose ps
```

### 502 Bad Gateway
Check application logs:
```bash
docker-compose logs backend
docker-compose logs frontend
```

## Security Recommendations

1. Enable HTTP/2 (already configured)
2. Configure rate limiting in Nginx
3. Set up fail2ban for brute force protection
4. Regular security updates
5. Monitor logs for suspicious activity

## Access URLs

- **Production**: https://launchpad.crl.to
- **API**: https://launchpad.crl.to/api
- **Local Development**: http://localhost:5080
