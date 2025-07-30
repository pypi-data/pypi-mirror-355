import re
import os
from pathlib import Path
from typing import Union, List, Optional, Dict, Any
from .exceptions import ValidationError


def validate_aws_region(region: str) -> bool:
    """Validate AWS region format"""
    # AWS region pattern: us-east-1, eu-west-2, ap-southeast-1, etc.
    pattern = r'^[a-z]{2}-[a-z]+-[0-9]$'
    return bool(re.match(pattern, region))


def validate_function_name(name: str) -> bool:
    """Validate Lambda function name according to AWS rules"""
    # Function name must be 1-64 characters, alphanumeric, hyphens, underscores
    if not name or len(name) > 64:
        return False
    
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, name))


def validate_repository_name(name: str) -> bool:
    """Validate ECR repository name according to AWS rules"""
    # Repository name must be 2-256 characters, lowercase, alphanumeric, hyphens, underscores, periods, slashes
    if not name or len(name) < 2 or len(name) > 256:
        return False
    
    pattern = r'^[a-z0-9._/-]+$'
    return bool(re.match(pattern, name))


def validate_memory_size(memory: int) -> bool:
    """Validate Lambda memory size"""
    # Lambda memory must be between 128 MB and 10,240 MB in 1 MB increments
    return 128 <= memory <= 10240


def validate_timeout(timeout: int) -> bool:
    """Validate Lambda timeout"""
    # Lambda timeout must be between 1 and 900 seconds
    return 1 <= timeout <= 900


def validate_source_path(path: Union[str, Path]) -> Path:
    """Validate and return source path"""
    source_path = Path(path)
    
    if not source_path.exists():
        raise ValidationError(f"Source path does not exist: {path}")
    
    if not source_path.is_dir():
        raise ValidationError(f"Source path must be a directory: {path}")
    
    # Check for at least one Python file
    python_files = list(source_path.rglob('*.py'))
    if not python_files:
        raise ValidationError(f"No Python files found in source path: {path}")
    
    return source_path


def validate_aws_profile(profile: str) -> bool:
    """Validate AWS profile exists in credentials"""
    import boto3
    from botocore.exceptions import ProfileNotFound
    
    try:
        session = boto3.Session(profile_name=profile)
        # Try to get credentials to verify profile exists
        session.get_credentials()
        return True
    except ProfileNotFound:
        return False
    except Exception:
        # If credentials are not available, profile might still exist
        return True


def validate_bedrock_model_id(model_id: str) -> bool:
    """Validate Bedrock model ID format"""
    # Common Bedrock model ID patterns
    valid_patterns = [
        r'^anthropic\.claude-.*',  # Claude models
        r'^amazon\.titan-.*',      # Titan models
        r'^ai21\.j2-.*',          # AI21 models
        r'^cohere\.command-.*',   # Cohere models
    ]
    
    return any(re.match(pattern, model_id) for pattern in valid_patterns)


def validate_environment_variables(required_vars: List[str]) -> Dict[str, str]:
    """Validate and return required environment variables"""
    missing_vars = []
    env_vars = {}
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            env_vars[var] = value
    
    if missing_vars:
        raise ValidationError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return env_vars


def validate_file_exists(file_path: Union[str, Path], description: str = "File") -> Path:
    """Validate that a file exists"""
    path = Path(file_path)
    
    if not path.exists():
        raise ValidationError(f"{description} does not exist: {file_path}")
    
    if not path.is_file():
        raise ValidationError(f"{description} is not a file: {file_path}")
    
    return path


def validate_directory_exists(dir_path: Union[str, Path], description: str = "Directory") -> Path:
    """Validate that a directory exists"""
    path = Path(dir_path)
    
    if not path.exists():
        raise ValidationError(f"{description} does not exist: {dir_path}")
    
    if not path.is_dir():
        raise ValidationError(f"{description} is not a directory: {dir_path}")
    
    return path


def validate_log_level(level: str) -> str:
    """Validate logging level"""
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    level_upper = level.upper()
    
    if level_upper not in valid_levels:
        raise ValidationError(f"Invalid log level: {level}. Must be one of: {', '.join(valid_levels)}")
    
    return level_upper


def validate_deployment_configuration(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate complete deployment configuration"""
    validated_config = {}
    
    # Required fields
    required_fields = ['function_name', 'source_path']
    for field in required_fields:
        if field not in config:
            raise ValidationError(f"Missing required configuration field: {field}")
    
    # Validate function name
    if not validate_function_name(config['function_name']):
        raise ValidationError(f"Invalid function name: {config['function_name']}")
    validated_config['function_name'] = config['function_name']
    
    # Validate source path
    validated_config['source_path'] = validate_source_path(config['source_path'])
    
    # Optional fields with validation
    if 'repository_name' in config:
        if not validate_repository_name(config['repository_name']):
            raise ValidationError(f"Invalid repository name: {config['repository_name']}")
        validated_config['repository_name'] = config['repository_name']
    
    if 'aws_region' in config:
        if not validate_aws_region(config['aws_region']):
            raise ValidationError(f"Invalid AWS region: {config['aws_region']}")
        validated_config['aws_region'] = config['aws_region']
    
    if 'aws_profile' in config:
        validated_config['aws_profile'] = config['aws_profile']
    
    if 'memory_size' in config:
        try:
            memory = int(config['memory_size'])
            if not validate_memory_size(memory):
                raise ValidationError(f"Invalid memory size: {memory}. Must be between 128 and 10240 MB")
            validated_config['memory_size'] = memory
        except (ValueError, TypeError):
            raise ValidationError(f"Memory size must be an integer: {config['memory_size']}")
    
    if 'timeout' in config:
        try:
            timeout = int(config['timeout'])
            if not validate_timeout(timeout):
                raise ValidationError(f"Invalid timeout: {timeout}. Must be between 1 and 900 seconds")
            validated_config['timeout'] = timeout
        except (ValueError, TypeError):
            raise ValidationError(f"Timeout must be an integer: {config['timeout']}")
    
    if 'log_level' in config:
        validated_config['log_level'] = validate_log_level(config['log_level'])
    
    return validated_config


def validate_handler_function(handler: str) -> bool:
    """Validate Lambda handler function format"""
    # Handler format: module.function or file.function
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*$'
    return bool(re.match(pattern, handler))


def validate_python_requirements(requirements_content: str) -> List[str]:
    """Validate requirements.txt content and return package list"""
    valid_packages = []
    invalid_lines = []
    
    lines = requirements_content.strip().split('\n')
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue
        
        # Basic package name validation
        # Supports: package, package==version, package>=version, etc.
        package_pattern = r'^[a-zA-Z][a-zA-Z0-9_-]*(\[.*\])?(==|>=|<=|>|<|~=|!=)?\S*$'
        
        if re.match(package_pattern, line):
            valid_packages.append(line)
        else:
            invalid_lines.append(f"Line {line_num}: {line}")
    
    if invalid_lines:
        raise ValidationError(f"Invalid requirements.txt entries:\n" + "\n".join(invalid_lines))
    
    return valid_packages


def validate_dockerfile_content(dockerfile_content: str) -> bool:
    """Validate basic Dockerfile structure"""
    lines = dockerfile_content.strip().split('\n')
    
    # Check for required FROM instruction
    has_from = any(line.strip().upper().startswith('FROM') for line in lines)
    if not has_from:
        raise ValidationError("Dockerfile must contain a FROM instruction")
    
    # Check for basic Lambda requirements
    has_cmd_or_entrypoint = any(
        line.strip().upper().startswith(('CMD', 'ENTRYPOINT')) 
        for line in lines
    )
    
    if not has_cmd_or_entrypoint:
        raise ValidationError("Dockerfile must contain a CMD or ENTRYPOINT instruction")
    
    return True


class ValidationContext:
    """Context manager for validation operations"""
    
    def __init__(self, operation: str):
        self.operation = operation
        self.errors = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.errors:
            error_msg = f"Validation failed for {self.operation}:\n" + "\n".join(self.errors)
            raise ValidationError(error_msg)
    
    def add_error(self, error: str):
        """Add validation error to context"""
        self.errors.append(error)
    
    def validate(self, condition: bool, error_msg: str):
        """Add error if condition is False"""
        if not condition:
            self.add_error(error_msg)
    
    def validate_field(self, value: Any, validator_func, field_name: str):
        """Validate a field using a validator function"""
        try:
            if not validator_func(value):
                self.add_error(f"Invalid {field_name}: {value}")
        except Exception as e:
            self.add_error(f"Validation error for {field_name}: {e}")


def safe_validate(validator_func, value, default=None):
    """Safely run a validator function and return result or default"""
    try:
        return validator_func(value)
    except Exception:
        return default