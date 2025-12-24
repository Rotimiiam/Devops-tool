import yaml


class PipelineGenerator:
    """Service for generating pipeline configurations"""
    
    def generate_deployment_pipeline(self, repo_name, deployment_server=None):
        """Generate a basic deployment pipeline configuration"""
        
        # Create a simple deployment pipeline
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
        
        # Add deployment step if server is specified
        if deployment_server:
            deployment_step = {
                'step': {
                    'name': 'Deploy to Server',
                    'deployment': 'production',
                    'script': [
                        f'echo "Deploying to {deployment_server}"',
                        '# Add deployment commands here',
                        '# Example: scp -r * user@server:/path/to/deploy',
                        'echo "Deployment completed successfully"'
                    ]
                }
            }
            pipeline['pipelines']['default'].append(deployment_step)
        
        return yaml.dump(pipeline, default_flow_style=False, sort_keys=False)
    
    def validate_pipeline_yaml(self, pipeline_config):
        """Validate that the pipeline configuration is valid YAML"""
        try:
            yaml.safe_load(pipeline_config)
            return True
        except yaml.YAMLError:
            return False
