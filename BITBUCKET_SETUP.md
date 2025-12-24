# Bitbucket Pipeline Setup Guide

## Required Repository Variables

Configure these in your Bitbucket repository:
**Repository Settings > Pipelines > Repository variables**

### 1. EC2_HOST
- **Value**: Your EC2 instance public IP or hostname
- **Example**: `ec2-54-123-45-67.compute-1.amazonaws.com` or `54.123.45.67`
- **Secured**: No (unless you want to hide it)

### 2. EC2_USER
- **Value**: SSH username for your EC2 instance
- **Common values**:
  - Ubuntu AMI: `ubuntu`
  - Amazon Linux: `ec2-user`
  - Debian: `admin`
- **Secured**: No

### 3. SSH_KEY
- **Value**: Your private SSH key (base64 encoded)
- **Secured**: Yes (check the "Secured" checkbox)

## How to Get Your SSH Key

### If you already have an SSH key pair:

```bash
# Encode your private key to base64
cat ~/.ssh/id_rsa | base64 -w 0

# Copy the output and paste it as the SSH_KEY variable value
```

### If you need to create a new SSH key:

```bash
# Generate a new SSH key pair
ssh-keygen -t rsa -b 4096 -f ~/.ssh/bitbucket_deploy_key -N ""

# Add the public key to your EC2 instance
ssh-copy-id -i ~/.ssh/bitbucket_deploy_key.pub $EC2_USER@$EC2_HOST

# Or manually add it:
cat ~/.ssh/bitbucket_deploy_key.pub
# Copy the output and add it to ~/.ssh/authorized_keys on your EC2

# Encode the private key for Bitbucket
cat ~/.ssh/bitbucket_deploy_key | base64 -w 0
```

## EC2 Security Group Configuration

Ensure your EC2 security group allows:

| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| SSH | TCP | 22 | Bitbucket IPs or 0.0.0.0/0 | SSH access for deployment |
| HTTP | TCP | 80 | 0.0.0.0/0 | Web traffic |
| Custom TCP | TCP | 5080 | 127.0.0.1/32 | Application (localhost only) |

### Bitbucket IP Ranges (for SSH restriction)
If you want to restrict SSH to Bitbucket only, add these IPs:
- `104.192.136.0/21`
- `185.166.140.0/22`
- `18.205.93.0/25`
- `18.234.32.128/25`

[Full list here](https://support.atlassian.com/bitbucket-cloud/docs/what-are-the-bitbucket-cloud-ip-addresses-i-should-use-to-configure-my-corporate-firewall/)

## Testing the Pipeline

### 1. Enable Pipelines
- Go to Repository Settings > Pipelines > Settings
- Enable Pipelines

### 2. Verify Variables
- Go to Repository Settings > Pipelines > Repository variables
- Ensure all three variables are set:
  - EC2_HOST
  - EC2_USER
  - SSH_KEY (should show as secured)

### 3. Test SSH Connection Manually

```bash
# Test from your local machine
ssh $EC2_USER@$EC2_HOST

# If successful, the pipeline should work too
```

### 4. Trigger the Pipeline

```bash
# Push to main branch
git push bitbucket main

# Or manually trigger from Bitbucket UI:
# Repository > Pipelines > Run pipeline > Select branch: main
```

## Pipeline Workflow

When you push to the `main` branch:

1. **Setup SSH**: Pipeline decodes SSH_KEY and configures SSH
2. **Connect to EC2**: SSH into your EC2 instance
3. **Clone/Pull Code**: Gets latest code from Bitbucket
4. **Build**: Runs `docker-compose build`
5. **Deploy**: Runs `docker-compose up -d`
6. **Health Check**: Verifies services are running

## Troubleshooting

### "Permission denied (publickey)"
- Verify SSH_KEY is correctly base64 encoded
- Ensure public key is in EC2's `~/.ssh/authorized_keys`
- Check EC2_USER is correct for your AMI

### "Host key verification failed"
- The pipeline includes `ssh-keyscan` to handle this automatically
- If issues persist, manually SSH once to add to known_hosts

### "docker: command not found"
- Docker not installed on EC2
- Follow NGINX_SETUP.md to install Docker

### "Permission denied" for Docker
- User not in docker group
- Run: `sudo usermod -aG docker $EC2_USER`
- Log out and back in

### Pipeline succeeds but app not accessible
- Check nginx is running: `sudo systemctl status nginx`
- Check docker containers: `docker-compose ps`
- Check logs: `docker-compose logs`
- Verify Security Group allows port 80

## Manual Deployment (Fallback)

If pipeline fails, you can deploy manually:

```bash
# SSH into EC2
ssh $EC2_USER@$EC2_HOST

# Navigate to project directory
cd /home/$USER/devops-tool

# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f
```

## Next Steps

1. Set up the three repository variables in Bitbucket
2. Ensure EC2 security group is configured
3. Install Docker and Nginx on EC2 (see NGINX_SETUP.md)
4. Push to main branch to trigger deployment
5. Access your app at http://launchpad.crl.to
