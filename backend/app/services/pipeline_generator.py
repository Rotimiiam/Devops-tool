import yaml
import os


class PipelineGenerator:
    """Service for generating pipeline configurations"""
    
    def __init__(self):
        self.project_types = {
            'react': self._generate_react_pipeline,
            'vue': self._generate_vue_pipeline,
            'angular': self._generate_angular_pipeline,
            'django': self._generate_django_pipeline,
            'flask': self._generate_flask_pipeline,
            'fastapi': self._generate_fastapi_pipeline,
            'nodejs': self._generate_nodejs_pipeline,
            'express': self._generate_express_pipeline,
            'nextjs': self._generate_nextjs_pipeline,
            'docker': self._generate_docker_pipeline,
            'fullstack': self._generate_fullstack_pipeline,
        }
    
    def generate_deployment_pipeline(self, repo_name, deployment_server=None, project_type=None, 
                                     detected_frameworks=None, detected_languages=None,
                                     subdomain=None, port=None, server_ip=None, 
                                     environment_variables=None):
        """Generate a deployment pipeline configuration based on project type"""
        
        # Auto-detect project type if not specified
        if not project_type and detected_frameworks:
            project_type = self._detect_project_type(detected_frameworks, detected_languages)
        
        # Use specific generator if available, otherwise use generic
        generator_func = self.project_types.get(project_type.lower() if project_type else None)
        
        if generator_func:
            pipeline_config = generator_func(
                repo_name=repo_name,
                deployment_server=deployment_server,
                subdomain=subdomain,
                port=port,
                server_ip=server_ip,
                environment_variables=environment_variables or {}
            )
        else:
            pipeline_config = self._generate_generic_pipeline(
                repo_name=repo_name,
                deployment_server=deployment_server,
                subdomain=subdomain,
                port=port,
                server_ip=server_ip,
                environment_variables=environment_variables or {}
            )
        
        return yaml.dump(pipeline_config, default_flow_style=False, sort_keys=False)
    
    def _detect_project_type(self, frameworks, languages):
        """Detect project type from frameworks and languages"""
        framework_names = [f.lower() for f in frameworks.keys()]
        
        # Check for specific frameworks
        if 'react' in framework_names:
            return 'react'
        elif 'vue' in framework_names:
            return 'vue'
        elif 'angular' in framework_names:
            return 'angular'
        elif 'next.js' in framework_names:
            return 'nextjs'
        elif 'django' in framework_names:
            return 'django'
        elif 'flask' in framework_names:
            return 'flask'
        elif 'fastapi' in framework_names:
            return 'fastapi'
        elif 'express' in framework_names:
            return 'nodejs'
        elif 'docker' in framework_names:
            return 'docker'
        
        # Check for language-based detection
        if languages:
            if 'JavaScript' in languages or 'TypeScript' in languages:
                return 'nodejs'
            elif 'Python' in languages:
                return 'flask'
        
        return None
    
    def _generate_generic_pipeline(self, repo_name, deployment_server, subdomain, port, server_ip, environment_variables):
        """Generate a basic deployment pipeline configuration"""
        pipeline = {
            'image': 'atlassian/default-image:3',
            'pipelines': {
                'default': [
                    {
                        'step': {
                            'name': 'Build and Test',
                            'script': [
                                'echo "Building application..."',
                                '# Add your build commands here',
                                'echo "Build completed successfully"'
                            ]
                        }
                    }
                ]
            }
        }
        
        if deployment_server and server_ip:
            pipeline['pipelines']['default'].append(
                self._generate_deployment_step(
                    deployment_server, subdomain, port, server_ip, environment_variables
                )
            )
        
        return pipeline
    
    def _generate_react_pipeline(self, repo_name, deployment_server, subdomain, port, server_ip, environment_variables):
        """Generate React deployment pipeline with build optimization"""
        pipeline = {
            'image': 'node:18',
            'definitions': {
                'caches': {
                    'npm': '$HOME/.npm'
                }
            },
            'pipelines': {
                'default': [
                    {
                        'step': {
                            'name': 'Build React Application',
                            'caches': ['node', 'npm'],
                            'script': [
                                'echo "Installing dependencies..."',
                                'npm ci',
                                'echo "Running tests..."',
                                'npm test -- --watchAll=false --coverage',
                                'echo "Building production bundle..."',
                                'npm run build',
                                'echo "Build artifacts created in ./build"'
                            ],
                            'artifacts': ['build/**']
                        }
                    }
                ]
            }
        }
        
        if deployment_server and server_ip:
            deploy_step = {
                'step': {
                    'name': 'Deploy to Server',
                    'deployment': 'production',
                    'script': [
                        f'echo "Deploying to {deployment_server}"',
                        'apt-get update && apt-get install -y rsync openssh-client',
                        '# Setup SSH key',
                        'mkdir -p ~/.ssh',
                        'echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa',
                        'chmod 600 ~/.ssh/id_rsa',
                        'ssh-keyscan -H ' + server_ip + ' >> ~/.ssh/known_hosts',
                        '# Deploy build files',
                        f'rsync -avz --delete build/ root@{server_ip}:/var/www/{subdomain or repo_name}/',
                        '# Restart nginx if needed',
                        f'ssh root@{server_ip} "systemctl reload nginx"',
                        'echo "Deployment completed successfully"'
                    ]
                }
            }
            pipeline['pipelines']['default'].append(deploy_step)
        
        return pipeline
    
    def _generate_vue_pipeline(self, repo_name, deployment_server, subdomain, port, server_ip, environment_variables):
        """Generate Vue.js deployment pipeline"""
        pipeline = {
            'image': 'node:18',
            'definitions': {
                'caches': {
                    'npm': '$HOME/.npm'
                }
            },
            'pipelines': {
                'default': [
                    {
                        'step': {
                            'name': 'Build Vue Application',
                            'caches': ['node', 'npm'],
                            'script': [
                                'echo "Installing dependencies..."',
                                'npm ci',
                                'echo "Running linter..."',
                                'npm run lint || true',
                                'echo "Building production bundle..."',
                                'npm run build',
                                'echo "Build artifacts created in ./dist"'
                            ],
                            'artifacts': ['dist/**']
                        }
                    }
                ]
            }
        }
        
        if deployment_server and server_ip:
            deploy_step = {
                'step': {
                    'name': 'Deploy to Server',
                    'deployment': 'production',
                    'script': [
                        f'echo "Deploying to {deployment_server}"',
                        'apt-get update && apt-get install -y rsync openssh-client',
                        'mkdir -p ~/.ssh',
                        'echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa',
                        'chmod 600 ~/.ssh/id_rsa',
                        'ssh-keyscan -H ' + server_ip + ' >> ~/.ssh/known_hosts',
                        f'rsync -avz --delete dist/ root@{server_ip}:/var/www/{subdomain or repo_name}/',
                        f'ssh root@{server_ip} "systemctl reload nginx"',
                        'echo "Deployment completed successfully"'
                    ]
                }
            }
            pipeline['pipelines']['default'].append(deploy_step)
        
        return pipeline
    
    def _generate_angular_pipeline(self, repo_name, deployment_server, subdomain, port, server_ip, environment_variables):
        """Generate Angular deployment pipeline"""
        pipeline = {
            'image': 'node:18',
            'pipelines': {
                'default': [
                    {
                        'step': {
                            'name': 'Build Angular Application',
                            'caches': ['node'],
                            'script': [
                                'npm ci',
                                'npm run test -- --watch=false --browsers=ChromeHeadless',
                                'npm run build -- --configuration production',
                                'echo "Build artifacts created"'
                            ],
                            'artifacts': ['dist/**']
                        }
                    }
                ]
            }
        }
        
        if deployment_server and server_ip:
            deploy_step = {
                'step': {
                    'name': 'Deploy to Server',
                    'deployment': 'production',
                    'script': [
                        'apt-get update && apt-get install -y rsync openssh-client',
                        'mkdir -p ~/.ssh',
                        'echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa',
                        'chmod 600 ~/.ssh/id_rsa',
                        'ssh-keyscan -H ' + server_ip + ' >> ~/.ssh/known_hosts',
                        f'rsync -avz --delete dist/ root@{server_ip}:/var/www/{subdomain or repo_name}/',
                        f'ssh root@{server_ip} "systemctl reload nginx"'
                    ]
                }
            }
            pipeline['pipelines']['default'].append(deploy_step)
        
        return pipeline
    
    def _generate_django_pipeline(self, repo_name, deployment_server, subdomain, port, server_ip, environment_variables):
        """Generate Django deployment pipeline with WSGI setup"""
        pipeline = {
            'image': 'python:3.11',
            'pipelines': {
                'default': [
                    {
                        'step': {
                            'name': 'Test Django Application',
                            'caches': ['pip'],
                            'script': [
                                'pip install -r requirements.txt',
                                'python manage.py check',
                                'python manage.py test || true',
                                'echo "Tests completed"'
                            ]
                        }
                    }
                ]
            }
        }
        
        if deployment_server and server_ip:
            deploy_step = {
                'step': {
                    'name': 'Deploy Django Application',
                    'deployment': 'production',
                    'script': [
                        'apt-get update && apt-get install -y rsync openssh-client',
                        'mkdir -p ~/.ssh',
                        'echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa',
                        'chmod 600 ~/.ssh/id_rsa',
                        'ssh-keyscan -H ' + server_ip + ' >> ~/.ssh/known_hosts',
                        f'rsync -avz --exclude=".git" --exclude="*.pyc" --exclude="__pycache__" . root@{server_ip}:/var/www/{repo_name}/',
                        f'ssh root@{server_ip} "cd /var/www/{repo_name} && pip install -r requirements.txt"',
                        f'ssh root@{server_ip} "cd /var/www/{repo_name} && python manage.py migrate"',
                        f'ssh root@{server_ip} "cd /var/www/{repo_name} && python manage.py collectstatic --noinput"',
                        f'ssh root@{server_ip} "systemctl restart gunicorn-{repo_name}"',
                        'echo "Django deployment completed"'
                    ]
                }
            }
            pipeline['pipelines']['default'].append(deploy_step)
        
        return pipeline
    
    def _generate_flask_pipeline(self, repo_name, deployment_server, subdomain, port, server_ip, environment_variables):
        """Generate Flask deployment pipeline with WSGI setup"""
        pipeline = {
            'image': 'python:3.11',
            'pipelines': {
                'default': [
                    {
                        'step': {
                            'name': 'Test Flask Application',
                            'caches': ['pip'],
                            'script': [
                                'pip install -r requirements.txt',
                                'python -m pytest tests/ || true',
                                'echo "Tests completed"'
                            ]
                        }
                    }
                ]
            }
        }
        
        if deployment_server and server_ip:
            deploy_step = {
                'step': {
                    'name': 'Deploy Flask Application',
                    'deployment': 'production',
                    'script': [
                        'apt-get update && apt-get install -y rsync openssh-client',
                        'mkdir -p ~/.ssh',
                        'echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa',
                        'chmod 600 ~/.ssh/id_rsa',
                        'ssh-keyscan -H ' + server_ip + ' >> ~/.ssh/known_hosts',
                        f'rsync -avz --exclude=".git" --exclude="*.pyc" --exclude="__pycache__" . root@{server_ip}:/var/www/{repo_name}/',
                        f'ssh root@{server_ip} "cd /var/www/{repo_name} && pip install -r requirements.txt"',
                        f'ssh root@{server_ip} "systemctl restart gunicorn-{repo_name}"',
                        'echo "Flask deployment completed"'
                    ]
                }
            }
            pipeline['pipelines']['default'].append(deploy_step)
        
        return pipeline
    
    def _generate_fastapi_pipeline(self, repo_name, deployment_server, subdomain, port, server_ip, environment_variables):
        """Generate FastAPI deployment pipeline"""
        return self._generate_flask_pipeline(repo_name, deployment_server, subdomain, port, server_ip, environment_variables)
    
    def _generate_nodejs_pipeline(self, repo_name, deployment_server, subdomain, port, server_ip, environment_variables):
        """Generate Node.js deployment pipeline with PM2"""
        pipeline = {
            'image': 'node:18',
            'pipelines': {
                'default': [
                    {
                        'step': {
                            'name': 'Test Node.js Application',
                            'caches': ['node'],
                            'script': [
                                'npm ci',
                                'npm test || true',
                                'echo "Tests completed"'
                            ]
                        }
                    }
                ]
            }
        }
        
        if deployment_server and server_ip:
            deploy_step = {
                'step': {
                    'name': 'Deploy Node.js Application',
                    'deployment': 'production',
                    'script': [
                        'apt-get update && apt-get install -y rsync openssh-client',
                        'mkdir -p ~/.ssh',
                        'echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa',
                        'chmod 600 ~/.ssh/id_rsa',
                        'ssh-keyscan -H ' + server_ip + ' >> ~/.ssh/known_hosts',
                        f'rsync -avz --exclude="node_modules" --exclude=".git" . root@{server_ip}:/var/www/{repo_name}/',
                        f'ssh root@{server_ip} "cd /var/www/{repo_name} && npm ci --production"',
                        f'ssh root@{server_ip} "pm2 restart {repo_name} || pm2 start app.js --name {repo_name}"',
                        'echo "Node.js deployment completed"'
                    ]
                }
            }
            pipeline['pipelines']['default'].append(deploy_step)
        
        return pipeline
    
    def _generate_express_pipeline(self, repo_name, deployment_server, subdomain, port, server_ip, environment_variables):
        """Generate Express.js deployment pipeline"""
        return self._generate_nodejs_pipeline(repo_name, deployment_server, subdomain, port, server_ip, environment_variables)
    
    def _generate_nextjs_pipeline(self, repo_name, deployment_server, subdomain, port, server_ip, environment_variables):
        """Generate Next.js deployment pipeline"""
        pipeline = {
            'image': 'node:18',
            'pipelines': {
                'default': [
                    {
                        'step': {
                            'name': 'Build Next.js Application',
                            'caches': ['node'],
                            'script': [
                                'npm ci',
                                'npm run build',
                                'echo "Next.js build completed"'
                            ]
                        }
                    }
                ]
            }
        }
        
        if deployment_server and server_ip:
            deploy_step = {
                'step': {
                    'name': 'Deploy Next.js Application',
                    'deployment': 'production',
                    'script': [
                        'apt-get update && apt-get install -y rsync openssh-client',
                        'mkdir -p ~/.ssh',
                        'echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa',
                        'chmod 600 ~/.ssh/id_rsa',
                        'ssh-keyscan -H ' + server_ip + ' >> ~/.ssh/known_hosts',
                        f'rsync -avz --exclude="node_modules" --exclude=".git" . root@{server_ip}:/var/www/{repo_name}/',
                        f'ssh root@{server_ip} "cd /var/www/{repo_name} && npm ci --production"',
                        f'ssh root@{server_ip} "pm2 restart {repo_name} || pm2 start npm --name {repo_name} -- start"',
                        'echo "Next.js deployment completed"'
                    ]
                }
            }
            pipeline['pipelines']['default'].append(deploy_step)
        
        return pipeline
    
    def _generate_docker_pipeline(self, repo_name, deployment_server, subdomain, port, server_ip, environment_variables):
        """Generate Docker multi-stage build pipeline"""
        pipeline = {
            'image': 'atlassian/default-image:3',
            'options': {
                'docker': True
            },
            'pipelines': {
                'default': [
                    {
                        'step': {
                            'name': 'Build and Push Docker Image',
                            'services': ['docker'],
                            'script': [
                                'export IMAGE_NAME=$BITBUCKET_REPO_SLUG',
                                'export IMAGE_TAG=${BITBUCKET_COMMIT::8}',
                                'echo "Building Docker image..."',
                                'docker build -t $IMAGE_NAME:$IMAGE_TAG .',
                                'docker tag $IMAGE_NAME:$IMAGE_TAG $IMAGE_NAME:latest',
                                'echo "Docker image built successfully"'
                            ]
                        }
                    }
                ]
            }
        }
        
        if deployment_server and server_ip:
            deploy_step = {
                'step': {
                    'name': 'Deploy Docker Container',
                    'deployment': 'production',
                    'script': [
                        'apt-get update && apt-get install -y openssh-client',
                        'mkdir -p ~/.ssh',
                        'echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa',
                        'chmod 600 ~/.ssh/id_rsa',
                        'ssh-keyscan -H ' + server_ip + ' >> ~/.ssh/known_hosts',
                        f'docker save {repo_name}:latest | ssh root@{server_ip} "docker load"',
                        f'ssh root@{server_ip} "docker stop {repo_name} || true"',
                        f'ssh root@{server_ip} "docker rm {repo_name} || true"',
                        f'ssh root@{server_ip} "docker run -d --name {repo_name} -p {port or 8080}:{port or 8080} {repo_name}:latest"',
                        'echo "Docker deployment completed"'
                    ]
                }
            }
            pipeline['pipelines']['default'].append(deploy_step)
        
        return pipeline
    
    def _generate_fullstack_pipeline(self, repo_name, deployment_server, subdomain, port, server_ip, environment_variables):
        """Generate full-stack deployment pipeline"""
        pipeline = {
            'image': 'atlassian/default-image:3',
            'pipelines': {
                'default': [
                    {
                        'step': {
                            'name': 'Build Frontend',
                            'image': 'node:18',
                            'caches': ['node'],
                            'script': [
                                'cd frontend || cd client',
                                'npm ci',
                                'npm run build',
                                'cd ..'
                            ],
                            'artifacts': ['frontend/build/**', 'frontend/dist/**', 'client/build/**', 'client/dist/**']
                        }
                    },
                    {
                        'step': {
                            'name': 'Test Backend',
                            'image': 'python:3.11',
                            'caches': ['pip'],
                            'script': [
                                'cd backend || cd server',
                                'pip install -r requirements.txt',
                                'python -m pytest tests/ || true',
                                'cd ..'
                            ]
                        }
                    }
                ]
            }
        }
        
        if deployment_server and server_ip:
            deploy_step = {
                'step': {
                    'name': 'Deploy Full Stack Application',
                    'deployment': 'production',
                    'script': [
                        'apt-get update && apt-get install -y rsync openssh-client',
                        'mkdir -p ~/.ssh',
                        'echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa',
                        'chmod 600 ~/.ssh/id_rsa',
                        'ssh-keyscan -H ' + server_ip + ' >> ~/.ssh/known_hosts',
                        f'rsync -avz --exclude="node_modules" --exclude=".git" . root@{server_ip}:/var/www/{repo_name}/',
                        f'ssh root@{server_ip} "cd /var/www/{repo_name}/backend && pip install -r requirements.txt"',
                        f'ssh root@{server_ip} "systemctl restart gunicorn-{repo_name}"',
                        f'ssh root@{server_ip} "systemctl reload nginx"',
                        'echo "Full stack deployment completed"'
                    ]
                }
            }
            pipeline['pipelines']['default'].append(deploy_step)
        
        return pipeline
    
    def _generate_deployment_step(self, deployment_server, subdomain, port, server_ip, environment_variables):
        """Generate generic deployment step"""
        return {
            'step': {
                'name': 'Deploy to Server',
                'deployment': 'production',
                'script': [
                    f'echo "Deploying to {deployment_server}"',
                    '# Add deployment commands here',
                    f'# Target: {server_ip}',
                    f'# Subdomain: {subdomain}',
                    f'# Port: {port}',
                    'echo "Deployment completed successfully"'
                ]
            }
        }
    
    def generate_nginx_config(self, subdomain, domain, port, server_ip, ssl_enabled=True):
        """Generate nginx reverse proxy configuration with SSL support"""
        server_name = f"{subdomain}.{domain}" if subdomain else domain
        
        if ssl_enabled:
            config = f"""server {{
    listen 80;
    server_name {server_name};
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {server_name};
    
    # SSL certificates managed by certbot
    ssl_certificate /etc/letsencrypt/live/{server_name}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{server_name}/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_session_timeout 10m;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Logging
    access_log /var/log/nginx/{server_name}_access.log;
    error_log /var/log/nginx/{server_name}_error.log;
    
    # Proxy settings
    location / {{
        proxy_pass http://127.0.0.1:{port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }}
}}
"""
        else:
            config = f"""server {{
    listen 80;
    server_name {server_name};
    
    # Logging
    access_log /var/log/nginx/{server_name}_access.log;
    error_log /var/log/nginx/{server_name}_error.log;
    
    # Proxy settings
    location / {{
        proxy_pass http://127.0.0.1:{port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }}
}}
"""
        
        return config
    
    def generate_certbot_command(self, subdomain, domain, email):
        """Generate certbot command for SSL certificate setup"""
        server_name = f"{subdomain}.{domain}" if subdomain else domain
        return f"certbot --nginx -d {server_name} --non-interactive --agree-tos -m {email}"
    
    def validate_pipeline_yaml(self, pipeline_config):
        """Validate that the pipeline configuration is valid YAML"""
        try:
            yaml.safe_load(pipeline_config)
            return True
        except yaml.YAMLError:
            return False
