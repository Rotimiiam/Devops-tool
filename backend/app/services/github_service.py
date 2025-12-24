from github import Github
import requests


class GitHubService:
    """Service for interacting with GitHub API"""
    
    def __init__(self, access_token):
        self.github = Github(access_token)
        self.access_token = access_token
    
    def list_repositories(self):
        """List user's repositories"""
        user = self.github.get_user()
        repos = []
        
        for repo in user.get_repos():
            repos.append({
                'id': repo.id,
                'name': repo.name,
                'full_name': repo.full_name,
                'description': repo.description,
                'private': repo.private,
                'html_url': repo.html_url,
                'clone_url': repo.clone_url,
                'default_branch': repo.default_branch,
                'language': repo.language
            })
        
        return repos
    
    def get_repository(self, repo_name):
        """Get repository details"""
        user = self.github.get_user()
        repo = user.get_repo(repo_name)
        
        return {
            'id': repo.id,
            'name': repo.name,
            'full_name': repo.full_name,
            'description': repo.description,
            'private': repo.private,
            'html_url': repo.html_url,
            'clone_url': repo.clone_url,
            'default_branch': repo.default_branch,
            'language': repo.language
        }
    
    def get_repository_content(self, repo_name, path=''):
        """Get repository file structure"""
        user = self.github.get_user()
        repo = user.get_repo(repo_name)
        
        try:
            contents = repo.get_contents(path)
            return [
                {
                    'name': content.name,
                    'path': content.path,
                    'type': content.type
                }
                for content in contents
            ]
        except Exception:
            return []
