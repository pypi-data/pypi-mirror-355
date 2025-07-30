"""
ACTIG Lambda Deployer

AWS Lambda Container Deployment CLI with AI-powered code analysis using AWS Bedrock Claude.
"""

__version__ = "0.1.0"
__author__ = "ACTIG Team"
__description__ = "AWS Lambda Container Deployment CLI with AI-powered code analysis"

from .cli import cli
from .config import Config
from .aws_clients import AWSClientManager
from .code_analyzer import LambdaCodeAnalyzer
from .artifact_generator import ArtifactGenerator
from .deployment_manager import DeploymentManager

__all__ = [
    "cli",
    "Config",
    "AWSClientManager", 
    "LambdaCodeAnalyzer",
    "ArtifactGenerator",
    "DeploymentManager",
]