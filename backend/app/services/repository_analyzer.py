import os
import re
import tempfile
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any
import json


class RepositoryAnalyzer:
    """Service for analyzing repository structure, technologies, and configurations"""
    
    # File extension to language mapping
    LANGUAGE_EXTENSIONS = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.jsx': 'JavaScript',
        '.ts': 'TypeScript',
        '.tsx': 'TypeScript',
        '.java': 'Java',
        '.go': 'Go',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.cs': 'C#',
        '.cpp': 'C++',
        '.c': 'C',
        '.h': 'C/C++',
        '.rs': 'Rust',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.r': 'R',
        '.sh': 'Shell',
        '.sql': 'SQL',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.less': 'LESS',
    }
    
    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        'React': [
            {'file': 'package.json', 'content': r'"react":\s*"'},
            {'file': '.jsx', 'content': r'from\s+["\']react["\']'},
            {'file': '.tsx', 'content': r'from\s+["\']react["\']'},
        ],
        'Vue': [
            {'file': 'package.json', 'content': r'"vue":\s*"'},
            {'file': '.vue', 'exists': True},
        ],
        'Angular': [
            {'file': 'package.json', 'content': r'"@angular/core":\s*"'},
            {'file': 'angular.json', 'exists': True},
        ],
        'Django': [
            {'file': 'requirements.txt', 'content': r'[Dd]jango'},
            {'file': 'manage.py', 'content': r'django'},
            {'file': 'settings.py', 'content': r'DJANGO_SETTINGS_MODULE'},
        ],
        'Flask': [
            {'file': 'requirements.txt', 'content': r'[Ff]lask'},
            {'file': '.py', 'content': r'from\s+flask\s+import'},
        ],
        'FastAPI': [
            {'file': 'requirements.txt', 'content': r'fastapi'},
            {'file': '.py', 'content': r'from\s+fastapi\s+import'},
        ],
        'Express': [
            {'file': 'package.json', 'content': r'"express":\s*"'},
            {'file': '.js', 'content': r'require\(["\']express["\']\)'},
        ],
        'Next.js': [
            {'file': 'package.json', 'content': r'"next":\s*"'},
            {'file': 'next.config.js', 'exists': True},
        ],
        'Spring Boot': [
            {'file': 'pom.xml', 'content': r'spring-boot'},
            {'file': 'build.gradle', 'content': r'spring-boot'},
        ],
        'Laravel': [
            {'file': 'composer.json', 'content': r'"laravel/framework"'},
            {'file': 'artisan', 'exists': True},
        ],
        'Ruby on Rails': [
            {'file': 'Gemfile', 'content': r'rails'},
            {'file': 'config.ru', 'exists': True},
        ],
    }
    
    # Build tool detection
    BUILD_TOOLS = {
        'npm': ['package.json'],
        'yarn': ['yarn.lock'],
        'pip': ['requirements.txt', 'setup.py', 'pyproject.toml'],
        'poetry': ['pyproject.toml', 'poetry.lock'],
        'maven': ['pom.xml'],
        'gradle': ['build.gradle', 'build.gradle.kts'],
        'composer': ['composer.json'],
        'bundler': ['Gemfile'],
        'go modules': ['go.mod'],
        'cargo': ['Cargo.toml'],
    }
    
    # Container technology detection
    CONTAINER_PATTERNS = {
        'Docker': ['Dockerfile', 'Dockerfile.*'],
        'docker-compose': ['docker-compose.yml', 'docker-compose.yaml'],
        'Kubernetes': ['*.yaml', '*.yml'],  # Check content for k8s resources
    }
    
    # Environment variable patterns by language
    ENV_VAR_PATTERNS = {
        'JavaScript': [
            r'process\.env\.(\w+)',
            r'process\.env\[[\'"]([\w_]+)[\'"]\]',
        ],
        'TypeScript': [
            r'process\.env\.(\w+)',
            r'process\.env\[[\'"]([\w_]+)[\'"]\]',
        ],
        'Python': [
            r'os\.environ(?:\.get)?\([\'"](\w+)[\'"]\)',
            r'os\.getenv\([\'"](\w+)[\'"]\)',
        ],
        'Java': [
            r'System\.getenv\([\'"](\w+)[\'"]\)',
            r'System\.getProperty\([\'"](\w+)[\'"]\)',
        ],
        'Go': [
            r'os\.Getenv\([\'"](\w+)[\'"]\)',
        ],
        'PHP': [
            r'\$_ENV\[[\'"](\w+)[\'"]\]',
            r'getenv\([\'"](\w+)[\'"]\)',
        ],
        'Ruby': [
            r'ENV\[[\'"](\w+)[\'"]\]',
        ],
        'C#': [
            r'Environment\.GetEnvironmentVariable\([\'"](\w+)[\'"]\)',
        ],
    }
    
    def __init__(self, clone_url: str, access_token: str = None):
        """Initialize the analyzer with repository URL"""
        self.clone_url = clone_url
        self.access_token = access_token
        self.temp_dir = None
        self.repo_path = None
        
    def analyze(self) -> Dict[str, Any]:
        """Perform comprehensive repository analysis"""
        try:
            # Clone repository to temporary directory
            self._clone_repository()
            
            # Perform various analyses
            file_structure = self._scan_file_structure()
            languages = self._detect_languages(file_structure)
            frameworks = self._detect_frameworks()
            build_tools = self._detect_build_tools()
            container_tech = self._detect_container_technologies()
            env_vars = self._extract_environment_variables(languages)
            
            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(
                languages, frameworks, build_tools, container_tech, env_vars
            )
            
            # Prepare analysis results
            analysis_results = {
                'detected_languages': languages,
                'detected_frameworks': {**frameworks, **build_tools, **container_tech},
                'required_env_vars': env_vars,
                'analysis_confidence': overall_confidence,
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'file_count': len(file_structure),
                'total_size': sum(f['size'] for f in file_structure),
            }
            
            return analysis_results
            
        except Exception as e:
            raise Exception(f"Repository analysis failed: {str(e)}")
        finally:
            # Always cleanup temporary directory
            self._cleanup()
    
    def _clone_repository(self):
        """Clone repository to temporary directory"""
        self.temp_dir = tempfile.mkdtemp(prefix='repo_analysis_')
        self.repo_path = os.path.join(self.temp_dir, 'repo')
        
        # Prepare clone URL with authentication if token provided
        clone_url = self.clone_url
        if self.access_token:
            # Insert token into URL (works for GitHub and Bitbucket)
            if 'github.com' in clone_url:
                clone_url = clone_url.replace('https://', f'https://{self.access_token}@')
            elif 'bitbucket.org' in clone_url:
                clone_url = clone_url.replace('https://', f'https://x-token-auth:{self.access_token}@')
        
        # Clone repository
        try:
            subprocess.run(
                ['git', 'clone', '--depth', '1', clone_url, self.repo_path],
                check=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to clone repository: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise Exception("Repository clone timed out after 5 minutes")
    
    def _scan_file_structure(self) -> List[Dict[str, Any]]:
        """Scan and catalog all files in the repository"""
        files = []
        
        for root, dirs, filenames in os.walk(self.repo_path):
            # Skip hidden directories and common ignorable directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'vendor', 'target', 'build', 'dist']]
            
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                    
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, self.repo_path)
                
                try:
                    file_size = os.path.getsize(file_path)
                    file_ext = os.path.splitext(filename)[1].lower()
                    
                    files.append({
                        'name': filename,
                        'path': rel_path,
                        'size': file_size,
                        'extension': file_ext,
                        'type': self._get_file_type(file_ext),
                    })
                except (OSError, IOError):
                    # Skip files that can't be accessed
                    continue
        
        return files
    
    def _get_file_type(self, extension: str) -> str:
        """Determine file type from extension"""
        if extension in self.LANGUAGE_EXTENSIONS:
            return 'source'
        elif extension in ['.json', '.yaml', '.yml', '.xml', '.toml', '.ini', '.env']:
            return 'config'
        elif extension in ['.md', '.txt', '.rst']:
            return 'documentation'
        elif extension in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico']:
            return 'image'
        else:
            return 'other'
    
    def _detect_languages(self, file_structure: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Detect programming languages used in the repository"""
        language_counts = {}
        total_source_files = 0
        
        for file_info in file_structure:
            if file_info['type'] == 'source':
                ext = file_info['extension']
                language = self.LANGUAGE_EXTENSIONS.get(ext, 'Unknown')
                
                if language not in language_counts:
                    language_counts[language] = {'count': 0, 'total_size': 0}
                
                language_counts[language]['count'] += 1
                language_counts[language]['total_size'] += file_info['size']
                total_source_files += 1
        
        # Calculate confidence based on file count percentage
        languages = {}
        for language, stats in language_counts.items():
            count_percentage = (stats['count'] / total_source_files * 100) if total_source_files > 0 else 0
            
            # Confidence increases with more files and significant presence
            if count_percentage >= 50:
                confidence = 95
            elif count_percentage >= 20:
                confidence = 85
            elif count_percentage >= 5:
                confidence = 70
            else:
                confidence = 50
            
            languages[language] = {
                'count': stats['count'],
                'size': stats['total_size'],
                'confidence': round(confidence, 2)
            }
        
        return languages
    
    def _detect_frameworks(self) -> Dict[str, Dict[str, Any]]:
        """Detect frameworks used in the repository"""
        detected_frameworks = {}
        
        for framework, patterns in self.FRAMEWORK_PATTERNS.items():
            confidence = 0
            version = None
            evidence = []
            
            for pattern in patterns:
                if 'exists' in pattern and pattern['exists']:
                    # Check if file with this extension or name exists
                    if self._file_exists_with_pattern(pattern['file']):
                        confidence += 30
                        evidence.append(f"Found {pattern['file']}")
                
                elif 'content' in pattern:
                    # Check file content
                    matches = self._search_file_content(pattern['file'], pattern['content'])
                    if matches:
                        confidence += 40
                        evidence.append(f"Found pattern in {pattern['file']}")
                        
                        # Try to extract version from package.json
                        if pattern['file'] == 'package.json' and framework in ['React', 'Vue', 'Angular', 'Express', 'Next.js']:
                            version = self._extract_version_from_package_json(framework.lower())
                        elif pattern['file'] == 'requirements.txt' and framework in ['Django', 'Flask', 'FastAPI']:
                            version = self._extract_version_from_requirements(framework)
            
            if confidence > 0:
                detected_frameworks[framework] = {
                    'confidence': min(confidence, 100),
                    'version': version,
                    'evidence': evidence
                }
        
        return detected_frameworks
    
    def _detect_build_tools(self) -> Dict[str, Dict[str, Any]]:
        """Detect build tools used in the repository"""
        detected_tools = {}
        
        for tool, indicator_files in self.BUILD_TOOLS.items():
            for indicator in indicator_files:
                if self._file_exists(indicator):
                    detected_tools[tool] = {
                        'confidence': 95,
                        'version': None,
                        'indicator_file': indicator
                    }
                    break
        
        return detected_tools
    
    def _detect_container_technologies(self) -> Dict[str, Dict[str, Any]]:
        """Detect container technologies used"""
        detected_containers = {}
        
        # Check for Docker
        if self._file_exists('Dockerfile') or self._file_exists_with_pattern('Dockerfile.*'):
            detected_containers['Docker'] = {
                'confidence': 100,
                'version': None,
                'files': self._find_dockerfiles()
            }
        
        # Check for docker-compose
        if self._file_exists('docker-compose.yml') or self._file_exists('docker-compose.yaml'):
            detected_containers['docker-compose'] = {
                'confidence': 100,
                'version': None,
                'files': ['docker-compose.yml']
            }
        
        # Check for Kubernetes
        k8s_files = self._find_kubernetes_files()
        if k8s_files:
            detected_containers['Kubernetes'] = {
                'confidence': 85,
                'version': None,
                'files': k8s_files
            }
        
        return detected_containers
    
    def _extract_environment_variables(self, languages: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Extract environment variables from code"""
        env_vars = {}
        
        # Determine which patterns to use based on detected languages
        patterns_to_check = []
        for language in languages.keys():
            if language in self.ENV_VAR_PATTERNS:
                patterns_to_check.extend(self.ENV_VAR_PATTERNS[language])
        
        # Add common .env file parsing
        env_file_vars = self._parse_env_files()
        for var in env_file_vars:
            if var not in env_vars:
                env_vars[var] = {
                    'source_files': ['.env'],
                    'confidence': 90
                }
        
        # Search through source files
        for root, dirs, filenames in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'vendor']]
            
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, self.repo_path)
                
                try:
                    # Only process text files
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    for pattern in patterns_to_check:
                        matches = re.findall(pattern, content)
                        for var_name in matches:
                            if var_name not in env_vars:
                                env_vars[var_name] = {
                                    'source_files': [],
                                    'confidence': 0
                                }
                            
                            if rel_path not in env_vars[var_name]['source_files']:
                                env_vars[var_name]['source_files'].append(rel_path)
                            
                            # Increase confidence based on number of occurrences
                            env_vars[var_name]['confidence'] = min(
                                env_vars[var_name]['confidence'] + 15,
                                100
                            )
                except (UnicodeDecodeError, IOError):
                    continue
        
        return env_vars
    
    def _parse_env_files(self) -> List[str]:
        """Parse .env files to extract variable names"""
        env_vars = []
        env_files = ['.env', '.env.example', '.env.sample', '.env.template']
        
        for env_file in env_files:
            file_path = os.path.join(self.repo_path, env_file)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                var_name = line.split('=')[0].strip()
                                if var_name:
                                    env_vars.append(var_name)
                except (UnicodeDecodeError, IOError):
                    continue
        
        return env_vars
    
    def _calculate_overall_confidence(
        self,
        languages: Dict,
        frameworks: Dict,
        build_tools: Dict,
        container_tech: Dict,
        env_vars: Dict
    ) -> float:
        """Calculate overall analysis confidence score"""
        scores = []
        
        # Languages confidence
        if languages:
            avg_lang_confidence = sum(l['confidence'] for l in languages.values()) / len(languages)
            scores.append(avg_lang_confidence)
        
        # Frameworks confidence
        if frameworks:
            avg_framework_confidence = sum(f['confidence'] for f in frameworks.values()) / len(frameworks)
            scores.append(avg_framework_confidence)
        
        # Build tools are generally very reliable (95% confidence)
        if build_tools:
            scores.append(95)
        
        # Container tech is very reliable
        if container_tech:
            scores.append(95)
        
        # Environment variables have varying confidence
        if env_vars:
            avg_env_confidence = sum(e['confidence'] for e in env_vars.values()) / len(env_vars)
            scores.append(avg_env_confidence)
        
        # Overall confidence is the average of all scores
        if scores:
            return round(sum(scores) / len(scores), 2)
        return 0.0
    
    def _file_exists(self, filename: str) -> bool:
        """Check if file exists in repository root"""
        return os.path.exists(os.path.join(self.repo_path, filename))
    
    def _file_exists_with_pattern(self, pattern: str) -> bool:
        """Check if any file matches the pattern"""
        if pattern.startswith('*.'):
            # Extension pattern
            ext = pattern[1:]
            for root, dirs, files in os.walk(self.repo_path):
                for file in files:
                    if file.endswith(ext):
                        return True
        else:
            # Specific file pattern
            for root, dirs, files in os.walk(self.repo_path):
                for file in files:
                    if file == pattern or file.endswith(pattern):
                        return True
        return False
    
    def _search_file_content(self, file_pattern: str, content_pattern: str) -> List[str]:
        """Search for pattern in files matching the file pattern"""
        matches = []
        
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'vendor']]
            
            for file in files:
                if file_pattern.startswith('*.'):
                    # Extension check
                    if not file.endswith(file_pattern[1:]):
                        continue
                else:
                    # Exact filename check
                    if file != file_pattern:
                        continue
                
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if re.search(content_pattern, content):
                            matches.append(os.path.relpath(file_path, self.repo_path))
                except (UnicodeDecodeError, IOError):
                    continue
        
        return matches
    
    def _extract_version_from_package_json(self, package_name: str) -> str:
        """Extract package version from package.json"""
        package_json_path = os.path.join(self.repo_path, 'package.json')
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    dependencies = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                    
                    for dep_name, version in dependencies.items():
                        if package_name in dep_name.lower():
                            return version.lstrip('^~')
            except (json.JSONDecodeError, IOError):
                pass
        return None
    
    def _extract_version_from_requirements(self, framework: str) -> str:
        """Extract version from requirements.txt"""
        req_path = os.path.join(self.repo_path, 'requirements.txt')
        if os.path.exists(req_path):
            try:
                with open(req_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if framework.lower() in line.lower():
                            # Extract version (e.g., Django==3.2.0 or Django>=3.2.0)
                            match = re.search(r'[=>]=\s*([0-9.]+)', line)
                            if match:
                                return match.group(1)
            except (UnicodeDecodeError, IOError):
                pass
        return None
    
    def _find_dockerfiles(self) -> List[str]:
        """Find all Dockerfile files"""
        dockerfiles = []
        for root, dirs, files in os.walk(self.repo_path):
            for file in files:
                if file == 'Dockerfile' or file.startswith('Dockerfile.'):
                    rel_path = os.path.relpath(os.path.join(root, file), self.repo_path)
                    dockerfiles.append(rel_path)
        return dockerfiles
    
    def _find_kubernetes_files(self) -> List[str]:
        """Find Kubernetes manifest files"""
        k8s_files = []
        k8s_patterns = [r'apiVersion:', r'kind:\s*(Deployment|Service|Pod|Ingress|ConfigMap)']
        
        for root, dirs, files in os.walk(self.repo_path):
            for file in files:
                if file.endswith(('.yaml', '.yml')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            for pattern in k8s_patterns:
                                if re.search(pattern, content):
                                    rel_path = os.path.relpath(file_path, self.repo_path)
                                    k8s_files.append(rel_path)
                                    break
                    except (UnicodeDecodeError, IOError):
                        continue
        
        return k8s_files
    
    def _cleanup(self):
        """Clean up temporary directory"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                # Log but don't raise - cleanup failure shouldn't break the flow
                print(f"Warning: Failed to cleanup temporary directory: {str(e)}")
    
    def generate_ai_recommendations(self, analysis_results: Dict[str, Any], gemini_service) -> str:
        """Generate AI recommendations based on analysis results"""
        if not gemini_service:
            return None
        
        try:
            # Prepare analysis summary for AI
            languages = analysis_results.get('detected_languages', {})
            frameworks = analysis_results.get('detected_frameworks', {})
            env_vars = analysis_results.get('required_env_vars', {})
            
            prompt = f"""You are a DevOps expert. Analyze this repository and provide recommendations.

Repository Analysis:

Detected Languages:
{json.dumps(languages, indent=2)}

Detected Frameworks and Tools:
{json.dumps(frameworks, indent=2)}

Required Environment Variables:
{json.dumps(list(env_vars.keys())[:20], indent=2)}  # Limit to first 20

Based on this analysis, provide:
1. Best practices for this technology stack
2. Recommended deployment strategy (containerization, serverless, traditional hosting)
3. Security considerations for the detected technologies
4. Performance optimization tips
5. Recommended CI/CD pipeline structure

Provide a concise, actionable response (maximum 500 words).
"""
            
            response = gemini_service.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Warning: Failed to generate AI recommendations: {str(e)}")
            return None
