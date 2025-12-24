import docker
import tempfile
import os
import yaml
import shutil
import subprocess


class PipelineRunner:
    """Service for running Bitbucket pipelines in a self-hosted environment"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
    
    def run_pipeline(self, pipeline_config, repository_url=None):
        """
        Run a Bitbucket pipeline configuration in a Docker container
        
        Args:
            pipeline_config: YAML string of the pipeline configuration
            repository_url: Optional URL to clone repository
        
        Returns:
            dict with success status, output, and error message
        """
        try:
            # Parse pipeline configuration
            config = yaml.safe_load(pipeline_config)
            
            # Get the image to use
            image = config.get('image', 'atlassian/default-image:3')
            
            # Get the default pipeline steps
            pipelines = config.get('pipelines', {})
            default_pipeline = pipelines.get('default', [])
            
            if not default_pipeline:
                return {
                    'success': False,
                    'output': '',
                    'error': 'No default pipeline defined'
                }
            
            # Create a temporary directory for the workspace
            with tempfile.TemporaryDirectory() as tmpdir:
                # Clone repository if URL provided
                if repository_url:
                    try:
                        subprocess.run(
                            ['git', 'clone', repository_url, tmpdir],
                            check=True,
                            capture_output=True,
                            timeout=300
                        )
                    except subprocess.CalledProcessError as e:
                        return {
                            'success': False,
                            'output': e.stdout.decode() if e.stdout else '',
                            'error': f'Failed to clone repository: {e.stderr.decode()}'
                        }
                
                # Execute each step
                all_output = []
                
                for step_def in default_pipeline:
                    step = step_def.get('step', {})
                    step_name = step.get('name', 'Unnamed step')
                    scripts = step.get('script', [])
                    
                    all_output.append(f"\n=== Running step: {step_name} ===\n")
                    
                    # Combine all script commands
                    script_content = '\n'.join(scripts)
                    
                    # Create a script file
                    script_path = os.path.join(tmpdir, 'step_script.sh')
                    with open(script_path, 'w') as f:
                        f.write('#!/bin/bash\n')
                        f.write('set -e\n')  # Exit on error
                        f.write(script_content)
                    
                    os.chmod(script_path, 0o755)
                    
                    try:
                        # Pull the image if not present
                        try:
                            self.docker_client.images.pull(image)
                        except Exception:
                            pass  # Image might already exist
                        
                        # Run the container
                        container = self.docker_client.containers.run(
                            image,
                            command='/bin/bash /workspace/step_script.sh',
                            volumes={tmpdir: {'bind': '/workspace', 'mode': 'rw'}},
                            working_dir='/workspace',
                            detach=True,
                            remove=False
                        )
                        
                        # Wait for container to complete
                        result = container.wait(timeout=300)
                        
                        # Get logs
                        logs = container.logs().decode('utf-8')
                        all_output.append(logs)
                        
                        # Check exit code
                        exit_code = result.get('StatusCode', 1)
                        
                        # Remove container
                        container.remove()
                        
                        if exit_code != 0:
                            return {
                                'success': False,
                                'output': '\n'.join(all_output),
                                'error': f'Step "{step_name}" failed with exit code {exit_code}'
                            }
                        
                    except docker.errors.ContainerError as e:
                        return {
                            'success': False,
                            'output': '\n'.join(all_output),
                            'error': f'Container error in step "{step_name}": {str(e)}'
                        }
                    except docker.errors.ImageNotFound:
                        return {
                            'success': False,
                            'output': '\n'.join(all_output),
                            'error': f'Docker image not found: {image}'
                        }
                    except Exception as e:
                        return {
                            'success': False,
                            'output': '\n'.join(all_output),
                            'error': f'Error running step "{step_name}": {str(e)}'
                        }
                
                # All steps completed successfully
                return {
                    'success': True,
                    'output': '\n'.join(all_output),
                    'error': None
                }
        
        except yaml.YAMLError as e:
            return {
                'success': False,
                'output': '',
                'error': f'Invalid YAML configuration: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'Unexpected error: {str(e)}'
            }
