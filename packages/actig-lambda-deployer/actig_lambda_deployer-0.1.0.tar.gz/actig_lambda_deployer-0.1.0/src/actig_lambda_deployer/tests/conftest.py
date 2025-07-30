"""
Pytest configuration and fixtures for ACTIG Lambda Deployer tests
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock
# Moto v5+ uses mock_aws for all services
from moto import mock_aws

# Use relative imports for the module structure
from ..aws_clients import AWSClientManager
from ..config import Config


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_lambda_code():
    """Sample Lambda function code for testing"""
    return '''
import json
import boto3
import os
from datetime import datetime

def lambda_handler(event, context):
    """Sample Lambda handler function"""
    print(f"Received event: {json.dumps(event)}")
    
    s3_client = boto3.client('s3')
    
    try:
        # Process the event
        body = {
            'message': 'Hello from Lambda!',
            'timestamp': datetime.now().isoformat(),
            'event_data': event
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(body)
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
'''


@pytest.fixture
def sample_requirements():
    """Sample requirements.txt content"""
    return '''
boto3>=1.26.0
requests>=2.28.0
python-dateutil>=2.8.0
'''


@pytest.fixture
def sample_lambda_project(temp_dir, sample_lambda_code, sample_requirements):
    """Create a complete sample Lambda project in temp directory"""
    # Create main Lambda file
    lambda_file = temp_dir / "lambda_function.py"
    lambda_file.write_text(sample_lambda_code)
    
    # Create requirements file
    req_file = temp_dir / "requirements.txt"
    req_file.write_text(sample_requirements)
    
    # Create a helper module
    utils_file = temp_dir / "utils.py"
    utils_file.write_text('''
def format_response(status_code, body):
    """Helper function to format Lambda response"""
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(body) if isinstance(body, dict) else body
    }
''')
    
    return temp_dir


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    config = Mock(spec=Config)
    config.aws_profile = 'test-profile'
    config.aws_region = 'us-east-1'
    config.bedrock_model_id = 'anthropic.claude-3-5-sonnet-20240620-v1:0'
    config.bedrock_max_tokens = 4096
    config.lambda_default_memory = 512
    config.lambda_default_timeout = 60
    config.log_level = 'INFO'
    return config


@pytest.fixture
def mock_client_manager():
    """Mock AWS client manager for testing"""
    manager = Mock(spec=AWSClientManager)
    manager.profile_name = 'test-profile'
    manager.region_name = 'us-east-1'
    manager.get_account_id.return_value = '123456789012'
    
    # Mock clients
    manager.get_client.return_value = Mock()
    
    return manager


@pytest.fixture
def mock_bedrock_client():
    """Mock Bedrock client with sample responses"""
    client = Mock()
    
    # Mock successful response
    mock_response = {
        'body': Mock(),
        'ResponseMetadata': {'HTTPStatusCode': 200}
    }
    
    sample_analysis = {
        'content': [{
            'text': json.dumps({
                'handler_function': 'lambda_function.lambda_handler',
                'runtime_version': 'python3.12', 
                'estimated_memory': 512,
                'estimated_timeout': 30,
                'base_image_recommendation': 'public.ecr.aws/lambda/python:3.12',
                'security_recommendations': ['Use environment variables'],
                'optimization_suggestions': ['Minimize cold start'],
                'required_packages': ['boto3', 'requests']
            })
        }]
    }
    
    mock_response['body'].read.return_value = json.dumps(sample_analysis).encode()
    client.invoke_model.return_value = mock_response
    
    return client


@pytest.fixture
def aws_mocks():
    """Setup mocked AWS services"""
    with mock_aws():
        yield


@pytest.fixture
def real_client_manager():
    """Real AWS client manager for integration tests"""
    # Only use this if AWS credentials are available
    pytest.skip("Integration test - requires AWS credentials")
    return AWSClientManager('default', 'us-east-1')


# Test markers
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires AWS credentials)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


# Fixtures for specific test scenarios
@pytest.fixture
def deployment_config():
    """Sample deployment configuration"""
    return {
        'function_name': 'test-lambda-function',
        'repository_name': 'test-lambda-repo',
        'aws_region': 'us-east-1',
        'aws_profile': 'test-profile',
        'memory_size': 512,
        'timeout': 60,
        'log_level': 'INFO'
    }