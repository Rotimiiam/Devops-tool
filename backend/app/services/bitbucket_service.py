import requests
import base64
import subprocess
import tempfile
import os
import shutil


class BitbucketService:
    """Service for interacting with Bitbucket API"""
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = 'https://api.bitbucket.org/2.0'
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    def list_repositories(self):
        """List user's repositories"""
        url = f'{self.base_url}/repositories'
        params = {'role': 'member'}
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        repos = []
        
        for repo in data.get('values', []):
            repos.append({
                'uuid': repo['uuid'],
                'name': repo['name'],
                'slug': repo['slug'],
                'description': repo.get('description', ''),
                'is_private': repo['is_private'],
                'html_url': repo['links']['html']['href'],
                'workspace': repo['workspace']['slug']
            })
        
        return repos
    
    def get_workspaces(self):
        """Get user's workspaces"""
        url = f'{self.base_url}/workspaces'
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        data = response.json()
        return [
            {
                'slug': ws['slug'],
                'name': ws['name'],
                'uuid': ws['uuid']
            }
            for ws in data.get('values', [])
        ]
    
    def create_repository(self, repo_name, description='', is_private=False, workspace=None):
        """Create a new repository in Bitbucket"""
        if not workspace:
            workspaces = self.get_workspaces()
            if not workspaces:
                raise Exception('No workspace found')
            workspace = workspaces[0]['slug']
        
        url = f'{self.base_url}/repositories/{workspace}/{repo_name}'
        
        payload = {
            'scm': 'git',
            'is_private': is_private,
            'description': description
        }
        
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
    
    def mirror_repository(self, source_url, destination_url):
        """Mirror a repository from source to destination"""
        # This is a simplified version - in production, use background tasks
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                # Clone source repository
                subprocess.run(
                    ['git', 'clone', '--bare', source_url, tmpdir],
                    check=True,
                    capture_output=True
                )
                
                # Push to destination
                subprocess.run(
                    ['git', '--git-dir', tmpdir, 'push', '--mirror', destination_url],
                    check=True,
                    capture_output=True
                )
                
                return True
            except subprocess.CalledProcessError as e:
                raise Exception(f'Failed to mirror repository: {e.stderr.decode()}')
    
    def create_pipeline_pr(self, workspace, repo_slug, pipeline_config, branch_name='add-pipeline', 
                          commit_message=None, pr_title=None, pr_description=None):
        """
        Create a pull request with pipeline configuration
        
        Args:
            workspace: Bitbucket workspace slug
            repo_slug: Repository slug
            pipeline_config: Pipeline YAML configuration
            branch_name: Branch name for the PR
            commit_message: Custom commit message
            pr_title: Custom PR title
            pr_description: Custom PR description
        """
        # First, create a new branch
        branch_url = f'{self.base_url}/repositories/{workspace}/{repo_slug}/refs/branches'
        
        # Get default branch
        repo_url = f'{self.base_url}/repositories/{workspace}/{repo_slug}'
        repo_response = requests.get(repo_url, headers=self.headers)
        repo_response.raise_for_status()
        default_branch = repo_response.json()['mainbranch']['name']
        
        # Create branch
        branch_payload = {
            'name': branch_name,
            'target': {
                'hash': default_branch
            }
        }
        branch_response = requests.post(branch_url, json=branch_payload, headers=self.headers)
        # Branch might already exist, which is okay
        
        # Commit pipeline file
        file_url = f'{self.base_url}/repositories/{workspace}/{repo_slug}/src'
        
        # Use custom commit message or default
        commit_msg = commit_message or 'Add Bitbucket pipeline configuration'
        
        files = {
            'bitbucket-pipelines.yml': pipeline_config,
            'message': commit_msg,
            'branch': branch_name
        }
        
        commit_response = requests.post(file_url, data=files, headers={
            'Authorization': f'Bearer {self.access_token}'
        })
        commit_response.raise_for_status()
        
        # Create pull request
        pr_url = f'{self.base_url}/repositories/{workspace}/{repo_slug}/pullrequests'
        
        # Use custom title and description or defaults
        pr_title_final = pr_title or 'Add Bitbucket Pipeline Configuration'
        pr_description_final = pr_description or 'This PR adds a working Bitbucket pipeline configuration generated and tested automatically.'
        
        pr_payload = {
            'title': pr_title_final,
            'description': pr_description_final,
            'source': {
                'branch': {
                    'name': branch_name
                }
            },
            'destination': {
                'branch': {
                    'name': default_branch
                }
            }
        }
        
        pr_response = requests.post(pr_url, json=pr_payload, headers=self.headers)
        pr_response.raise_for_status()
        
        return pr_response.json()['links']['html']['href']
    
    def trigger_pipeline(self, workspace, repo_slug, branch='main'):
        """Trigger a pipeline run for a repository"""
        url = f'{self.base_url}/repositories/{workspace}/{repo_slug}/pipelines/'
        
        payload = {
            'target': {
                'ref_type': 'branch',
                'type': 'pipeline_ref_target',
                'ref_name': branch
            }
        }
        
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        
        pipeline_data = response.json()
        return {
            'uuid': pipeline_data['uuid'],
            'build_number': pipeline_data['build_number'],
            'state': pipeline_data['state']['name'],
            'created_on': pipeline_data['created_on']
        }
    
    def get_pipeline_runs(self, workspace, repo_slug, limit=10):
        """Get recent pipeline runs for a repository"""
        url = f'{self.base_url}/repositories/{workspace}/{repo_slug}/pipelines/'
        params = {'pagelen': limit, 'sort': '-created_on'}
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        runs = []
        
        for pipeline in data.get('values', []):
            runs.append({
                'uuid': pipeline['uuid'],
                'build_number': pipeline['build_number'],
                'state': pipeline['state']['name'],
                'created_on': pipeline['created_on'],
                'completed_on': pipeline.get('completed_on'),
                'duration_in_seconds': pipeline.get('duration_in_seconds'),
                'trigger': pipeline.get('trigger', {}).get('name', 'unknown')
            })
        
        return runs
    
    def get_pipeline_logs(self, workspace, repo_slug, pipeline_uuid):
        """Get logs for a specific pipeline run"""
        url = f'{self.base_url}/repositories/{workspace}/{repo_slug}/pipelines/{pipeline_uuid}'
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        pipeline_data = response.json()
        
        # Get steps
        steps_url = f'{self.base_url}/repositories/{workspace}/{repo_slug}/pipelines/{pipeline_uuid}/steps/'
        steps_response = requests.get(steps_url, headers=self.headers)
        steps_response.raise_for_status()
        
        steps_data = steps_response.json()
        logs = []
        
        for step in steps_data.get('values', []):
            step_info = {
                'name': step.get('name'),
                'state': step['state']['name'],
                'started_on': step.get('started_on'),
                'completed_on': step.get('completed_on'),
                'duration_in_seconds': step.get('duration_in_seconds'),
                'log': None
            }
            
            # Get step log
            if 'log' in step.get('links', {}):
                log_url = step['links']['log']['href']
                try:
                    log_response = requests.get(log_url, headers=self.headers)
                    log_response.raise_for_status()
                    step_info['log'] = log_response.text
                except:
                    step_info['log'] = 'Log unavailable'
            
            logs.append(step_info)
        
        return {
            'uuid': pipeline_data['uuid'],
            'build_number': pipeline_data['build_number'],
            'state': pipeline_data['state']['name'],
            'created_on': pipeline_data['created_on'],
            'completed_on': pipeline_data.get('completed_on'),
            'duration_in_seconds': pipeline_data.get('duration_in_seconds'),
            'steps': logs
        }
    
    def sync_environment_variables(self, workspace, repo_slug, environment_variables):
        """Sync environment variables to Bitbucket repository variables"""
        url = f'{self.base_url}/repositories/{workspace}/{repo_slug}/pipelines_config/variables/'
        
        # Get existing variables
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        existing_vars = {var['key']: var['uuid'] for var in response.json().get('values', [])}
        
        synced_vars = []
        errors = []
        
        for key, value in environment_variables.items():
            try:
                if key in existing_vars:
                    # Update existing variable
                    var_url = f'{url}{existing_vars[key]}'
                    payload = {'key': key, 'value': value, 'secured': True}
                    update_response = requests.put(var_url, json=payload, headers=self.headers)
                    update_response.raise_for_status()
                    synced_vars.append({'key': key, 'action': 'updated'})
                else:
                    # Create new variable
                    payload = {'key': key, 'value': value, 'secured': True}
                    create_response = requests.post(url, json=payload, headers=self.headers)
                    create_response.raise_for_status()
                    synced_vars.append({'key': key, 'action': 'created'})
            except Exception as e:
                errors.append({'key': key, 'error': str(e)})
        
        return {
            'synced': synced_vars,
            'errors': errors
        }
    
    def get_repository_variables(self, workspace, repo_slug):
        """Get all repository pipeline variables"""
        url = f'{self.base_url}/repositories/{workspace}/{repo_slug}/pipelines_config/variables/'
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        variables = []
        for var in response.json().get('values', []):
            variables.append({
                'key': var['key'],
                'secured': var.get('secured', False),
                'uuid': var['uuid']
            })
        
        return variables
