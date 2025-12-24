import google.generativeai as genai


class GeminiService:
    """Service for interacting with Gemini API"""
    
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def fix_pipeline(self, current_config, error_output, error_message):
        """Use Gemini to analyze and fix a failed pipeline configuration"""
        
        prompt = f"""You are a Bitbucket Pipelines expert. A pipeline configuration has failed and needs to be fixed.

Current Pipeline Configuration:
```yaml
{current_config}
```

Error Output:
```
{error_output}
```

Error Message:
```
{error_message}
```

Please analyze the error and provide a corrected version of the bitbucket-pipelines.yml file that should work.
Only provide the YAML configuration, nothing else. Do not include markdown code blocks or explanations.
"""
        
        response = self.model.generate_content(prompt)
        fixed_config = response.text.strip()
        
        # Remove markdown code blocks if present
        if fixed_config.startswith('```'):
            lines = fixed_config.split('\n')
            # Remove first line (```yaml or ```)
            lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            fixed_config = '\n'.join(lines)
        
        return fixed_config
    
    def generate_pipeline(self, repo_info, deployment_server=None):
        """Generate a pipeline configuration based on repository information"""
        
        prompt = f"""Generate a Bitbucket Pipelines configuration for deploying an application.

Repository Information:
- Name: {repo_info.get('name')}
- Language: {repo_info.get('language', 'Unknown')}
- Description: {repo_info.get('description', 'N/A')}

Requirements:
1. The pipeline should be simple and deploy the application
2. Deployment server: {deployment_server or 'to be specified'}
3. Include basic build steps appropriate for the language
4. Include deployment steps using SSH or similar

Provide only the YAML configuration for bitbucket-pipelines.yml, nothing else.
Do not include markdown code blocks or explanations.
"""
        
        response = self.model.generate_content(prompt)
        config = response.text.strip()
        
        # Remove markdown code blocks if present
        if config.startswith('```'):
            lines = config.split('\n')
            lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            config = '\n'.join(lines)
        
        return config
