import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
from .utils.exceptions import ValidationError


class Config:
    """Configuration management with YAML file support"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_data = self._load_default_config()
        
        # Load from file if provided
        if config_file:
            self._load_config_file(config_file)
        
        # Override with environment variables
        self._load_environment_variables()
        
        # Set dynamic properties
        self.aws_profile = self.config_data.get('aws', {}).get('default_profile', 'default')
        self.aws_region = self.config_data.get('aws', {}).get('default_region', 'us-east-1')
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration values"""
        return {
            'aws': {
                'default_region': 'us-east-1',
                'default_profile': 'default',
            },
            'bedrock': {
                'model_id': 'anthropic.claude-3-5-sonnet-20240620-v1:0',
                'max_tokens': 4096,
                'temperature': 0.1,
            },
            'lambda': {
                'default_memory': 512,
                'default_timeout': 60,
                'default_runtime': 'python3.12',
            },
            'ecr': {
                'scan_on_push': True,
                'tag_mutability': 'MUTABLE',
            },
            'codebuild': {
                'compute_type': 'BUILD_GENERAL1_SMALL',
                'image': 'aws/codebuild/standard:5.0',
                'timeout_minutes': 60,
            },
            'logging': {
                'level': 'INFO',
                'format': 'json',
                'retention_days': 14,
            }
        }
    
    def _load_config_file(self, config_file: str):
        """Load configuration from YAML file"""
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise ValidationError(f"Configuration file not found: {config_file}")
        
        try:
            with open(config_path, 'r') as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    self._merge_config(self.config_data, file_config)
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise ValidationError(f"Failed to load configuration file: {e}")
    
    def _load_environment_variables(self):
        """Load configuration from environment variables"""
        env_mappings = {
            'AWS_PROFILE': ['aws', 'default_profile'],
            'AWS_DEFAULT_REGION': ['aws', 'default_region'],
            'BEDROCK_MODEL_ID': ['bedrock', 'model_id'],
            'LAMBDA_DEFAULT_MEMORY': ['lambda', 'default_memory'],
            'LAMBDA_DEFAULT_TIMEOUT': ['lambda', 'default_timeout'],
            'LOG_LEVEL': ['logging', 'level'],
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                # Convert numeric values
                if env_var in ['LAMBDA_DEFAULT_MEMORY', 'LAMBDA_DEFAULT_TIMEOUT']:
                    try:
                        value = int(value)
                    except ValueError:
                        continue
                
                # Set nested configuration value
                current = self.config_data
                for key in config_path[:-1]:
                    current = current.setdefault(key, {})
                current[config_path[-1]] = value
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]):
        """Recursively merge configuration dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation (e.g., 'aws.default_region')"""
        keys = key_path.split('.')
        current = self.config_data
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value):
        """Set configuration value using dot notation"""
        keys = key_path.split('.')
        current = self.config_data
        
        for key in keys[:-1]:
            current = current.setdefault(key, {})
        current[keys[-1]] = value
    
    @property
    def bedrock_model_id(self) -> str:
        """Get Bedrock model ID"""
        return self.get('bedrock.model_id', 'anthropic.claude-3-5-sonnet-20240620-v1:0')
    
    @property
    def bedrock_max_tokens(self) -> int:
        """Get Bedrock max tokens"""
        return self.get('bedrock.max_tokens', 4096)
    
    @property
    def lambda_default_memory(self) -> int:
        """Get Lambda default memory size"""
        return self.get('lambda.default_memory', 512)
    
    @property
    def lambda_default_timeout(self) -> int:
        """Get Lambda default timeout"""
        return self.get('lambda.default_timeout', 60)
    
    @property
    def codebuild_compute_type(self) -> str:
        """Get CodeBuild compute type"""
        return self.get('codebuild.compute_type', 'BUILD_GENERAL1_SMALL')
    
    @property
    def codebuild_image(self) -> str:
        """Get CodeBuild image"""
        return self.get('codebuild.image', 'aws/codebuild/standard:5.0')
    
    @property
    def log_level(self) -> str:
        """Get logging level"""
        return self.get('logging.level', 'INFO')
    
    def validate(self):
        """Validate configuration values"""
        required_keys = [
            'aws.default_region',
            'bedrock.model_id',
        ]
        
        for key in required_keys:
            if self.get(key) is None:
                raise ValidationError(f"Required configuration key missing: {key}")
        
        # Validate memory size
        memory = self.lambda_default_memory
        if not (128 <= memory <= 10240):
            raise ValidationError(f"Lambda memory size must be between 128 and 10240 MB, got: {memory}")
        
        # Validate timeout
        timeout = self.lambda_default_timeout
        if not (1 <= timeout <= 900):
            raise ValidationError(f"Lambda timeout must be between 1 and 900 seconds, got: {timeout}")
        
        # Validate log level
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level.upper() not in valid_levels:
            raise ValidationError(f"Invalid log level: {self.log_level}. Must be one of: {valid_levels}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary"""
        return self.config_data.copy()
    
    def save(self, file_path: str):
        """Save configuration to YAML file"""
        config_path = Path(file_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'w') as f:
                yaml.dump(self.config_data, f, default_flow_style=False, sort_keys=True)
        except Exception as e:
            raise ValidationError(f"Failed to save configuration file: {e}")