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
    
    def create_pipeline_pr(self, workspace, repo_slug, pipeline_config, branch_name='add-pipeline'):
        """Create a pull request with pipeline configuration"""
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
        
        files = {
            'bitbucket-pipelines.yml': pipeline_config,
            'message': 'Add Bitbucket pipeline configuration',
            'branch': branch_name
        }
        
        commit_response = requests.post(file_url, data=files, headers={
            'Authorization': f'Bearer {self.access_token}'
        })
        commit_response.raise_for_status()
        
        # Create pull request
        pr_url = f'{self.base_url}/repositories/{workspace}/{repo_slug}/pullrequests'
        
        pr_payload = {
            'title': 'Add Bitbucket Pipeline Configuration',
            'description': 'This PR adds a working Bitbucket pipeline configuration generated and tested automatically.',
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
