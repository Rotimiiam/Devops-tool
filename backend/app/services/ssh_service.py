import os
import tempfile
import subprocess
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ed25519
from cryptography.hazmat.backends import default_backend
import hashlib
import base64
import paramiko


class SSHService:
    """Service for SSH key management and deployment"""
    
    @staticmethod
    def generate_ssh_key_pair(key_type='rsa', key_size=4096, comment=''):
        """
        Generate SSH key pair
        
        Args:
            key_type: Type of key to generate ('rsa' or 'ed25519')
            key_size: Size of key (only for RSA, default 4096)
            comment: Comment to add to the public key
            
        Returns:
            dict with 'public_key', 'private_key', and 'fingerprint'
        """
        if key_type == 'ed25519':
            # Generate ED25519 key
            private_key_obj = ed25519.Ed25519PrivateKey.generate()
            public_key_obj = private_key_obj.public_key()
            
            # Serialize private key
            private_key_pem = private_key_obj.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.OpenSSH,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')
            
            # Serialize public key
            public_key_openssh = public_key_obj.public_bytes(
                encoding=serialization.Encoding.OpenSSH,
                format=serialization.PublicFormat.OpenSSH
            ).decode('utf-8')
            
        elif key_type == 'rsa':
            # Generate RSA key
            private_key_obj = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size,
                backend=default_backend()
            )
            public_key_obj = private_key_obj.public_key()
            
            # Serialize private key
            private_key_pem = private_key_obj.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.OpenSSH,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')
            
            # Serialize public key
            public_key_openssh = public_key_obj.public_bytes(
                encoding=serialization.Encoding.OpenSSH,
                format=serialization.PublicFormat.OpenSSH
            ).decode('utf-8')
        else:
            raise ValueError(f"Unsupported key type: {key_type}")
        
        # Add comment if provided
        if comment:
            public_key_with_comment = f"{public_key_openssh} {comment}"
        else:
            public_key_with_comment = public_key_openssh
        
        # Calculate fingerprint (MD5)
        fingerprint = SSHService.calculate_fingerprint(public_key_openssh)
        
        return {
            'public_key': public_key_with_comment,
            'private_key': private_key_pem,
            'fingerprint': fingerprint,
            'key_type': key_type
        }
    
    @staticmethod
    def calculate_fingerprint(public_key_str):
        """
        Calculate SSH key fingerprint (MD5 format)
        
        Args:
            public_key_str: OpenSSH format public key string
            
        Returns:
            Fingerprint string in format 'MD5:xx:xx:xx:...'
        """
        try:
            # Parse the public key
            parts = public_key_str.strip().split()
            if len(parts) < 2:
                raise ValueError("Invalid public key format")
            
            key_data = base64.b64decode(parts[1])
            
            # Calculate MD5 hash
            md5_hash = hashlib.md5(key_data).hexdigest()
            
            # Format as colon-separated pairs
            fingerprint = ':'.join(md5_hash[i:i+2] for i in range(0, len(md5_hash), 2))
            
            return f"MD5:{fingerprint}"
        except Exception as e:
            # Fallback to a simple hash if parsing fails
            return f"MD5:{hashlib.md5(public_key_str.encode()).hexdigest()}"
    
    @staticmethod
    def deploy_key_to_server(server_host, server_port, username, password, public_key, auth_method='password'):
        """
        Deploy SSH public key to a remote server's authorized_keys
        
        Args:
            server_host: Server hostname or IP
            server_port: SSH port (default 22)
            username: SSH username
            password: SSH password (if auth_method is 'password')
            public_key: Public key to deploy
            auth_method: 'password' or 'key'
            
        Returns:
            dict with success status and message
        """
        try:
            # Create SSH client
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect to server
            client.connect(
                hostname=server_host,
                port=server_port,
                username=username,
                password=password if auth_method == 'password' else None,
                timeout=10
            )
            
            # Prepare the command to add the key
            # Ensure .ssh directory exists
            stdin, stdout, stderr = client.exec_command('mkdir -p ~/.ssh && chmod 700 ~/.ssh')
            stdout.channel.recv_exit_status()  # Wait for command to complete
            
            # Add key to authorized_keys
            escaped_key = public_key.replace("'", "'\"'\"'")
            command = f"echo '{escaped_key}' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
            stdin, stdout, stderr = client.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()
            
            client.close()
            
            if exit_status == 0:
                return {
                    'success': True,
                    'message': f'SSH key successfully deployed to {username}@{server_host}:{server_port}'
                }
            else:
                error_msg = stderr.read().decode('utf-8')
                return {
                    'success': False,
                    'message': f'Failed to deploy SSH key: {error_msg}'
                }
                
        except paramiko.AuthenticationException:
            return {
                'success': False,
                'message': 'Authentication failed. Please check username and password.'
            }
        except paramiko.SSHException as e:
            return {
                'success': False,
                'message': f'SSH connection error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Deployment error: {str(e)}'
            }
    
    @staticmethod
    def test_ssh_connection(server_host, server_port, username, private_key_str):
        """
        Test SSH connection using a private key
        
        Args:
            server_host: Server hostname or IP
            server_port: SSH port
            username: SSH username
            private_key_str: Private key string (PEM format)
            
        Returns:
            dict with success status and message
        """
        try:
            # Create SSH client
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Load private key from string
            from io import StringIO
            private_key_file = StringIO(private_key_str)
            
            try:
                private_key = paramiko.RSAKey.from_private_key(private_key_file)
            except:
                private_key_file = StringIO(private_key_str)
                private_key = paramiko.Ed25519Key.from_private_key(private_key_file)
            
            # Connect using the private key
            client.connect(
                hostname=server_host,
                port=server_port,
                username=username,
                pkey=private_key,
                timeout=10
            )
            
            # Test with a simple command
            stdin, stdout, stderr = client.exec_command('echo "SSH connection successful"')
            output = stdout.read().decode('utf-8').strip()
            
            client.close()
            
            return {
                'success': True,
                'message': f'SSH connection successful: {output}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Connection test failed: {str(e)}'
            }
    
    @staticmethod
    def remove_key_from_server(server_host, server_port, username, password, public_key_fingerprint):
        """
        Remove SSH public key from server's authorized_keys
        
        Args:
            server_host: Server hostname or IP
            server_port: SSH port
            username: SSH username
            password: SSH password
            public_key_fingerprint: Fingerprint of the key to remove
            
        Returns:
            dict with success status and message
        """
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            client.connect(
                hostname=server_host,
                port=server_port,
                username=username,
                password=password,
                timeout=10
            )
            
            # Read current authorized_keys
            stdin, stdout, stderr = client.exec_command('cat ~/.ssh/authorized_keys')
            current_keys = stdout.read().decode('utf-8')
            
            # Filter out the key to remove (basic implementation)
            # In production, you'd want more sophisticated matching
            new_keys = '\n'.join([
                line for line in current_keys.split('\n')
                if line.strip() and public_key_fingerprint not in line
            ])
            
            # Write back the filtered keys
            command = f"echo '{new_keys}' > ~/.ssh/authorized_keys"
            stdin, stdout, stderr = client.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()
            
            client.close()
            
            if exit_status == 0:
                return {
                    'success': True,
                    'message': 'SSH key successfully removed from server'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to remove SSH key from server'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error removing key: {str(e)}'
            }
