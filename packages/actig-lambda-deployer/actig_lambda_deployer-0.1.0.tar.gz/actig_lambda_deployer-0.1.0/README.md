# ACTIG Lambda Deployer

An intelligent AWS Lambda container deployment CLI that automates code analysis and deployment using AWS Bedrock Claude for AI-powered artifact generation.

## Features

✨ **AI-Powered Analysis**: Uses AWS Bedrock Claude to analyze Lambda code and generate optimized deployment artifacts  
🐳 **Container Deployments**: Automated Docker container builds and ECR repository management  
🚀 **Complete CI/CD Pipeline**: Integrates CodeCommit, CodeBuild, and CloudFormation for end-to-end automation  
📦 **Artifact Generation**: Automatically generates Dockerfile, buildspec.yml, and CloudFormation templates  
🔧 **Team Standards**: Follows your team's build patterns and requirements  

## Installation

```bash
pip install actig-lambda-deployer
```

## Prerequisites

- AWS CLI configured with appropriate permissions
- AWS Bedrock access with Claude models enabled
- Git configured for CodeCommit (if using CodeCommit)
- Docker (for local testing)

## Quick Start

### 1. Prepare Your Lambda Function

Your Lambda function directory should contain:
- Python source files (`.py`)
- `requirements.txt` file (required)

Example structure:
```
my-lambda/
├── lambda_function.py
└── requirements.txt
```

### 2. Deploy Your Function

```bash
actig-lambda-deployer deploy ./my-lambda --function-name my-function
```

The tool will:
1. Analyze your code using AI
2. Generate optimized deployment artifacts
3. Create CI/CD pipeline infrastructure  
4. Build and deploy your container image
5. Deploy your Lambda function

### 3. Check Deployment Status

```bash
actig-lambda-deployer status my-function
```

## Configuration

### AWS Credentials

Configure AWS credentials using any standard method:

```bash
# Using AWS CLI
aws configure

# Using environment variables
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_DEFAULT_REGION=us-east-1

# Using AWS profiles
actig-lambda-deployer deploy ./my-lambda --function-name my-func --profile production
```

### Bedrock Access

Ensure you have access to these Bedrock models:
- `anthropic.claude-3-5-sonnet-20240620-v1:0`

Enable model access in the AWS Bedrock console.

## Usage Examples

### Basic Deployment
```bash
actig-lambda-deployer deploy ./src --function-name api-handler
```

### Custom ECR Repository
```bash
actig-lambda-deployer deploy ./src --function-name api-handler --repository-name my-custom-repo
```

### Dry Run (Preview Changes)
```bash
actig-lambda-deployer deploy ./src --function-name api-handler --dry-run
```

### Different AWS Region
```bash
actig-lambda-deployer deploy ./src --function-name api-handler --region us-west-2
```

### Debug Mode
```bash
actig-lambda-deployer deploy ./src --function-name api-handler --log-level DEBUG
```

## CLI Reference

### Commands

- `deploy` - Analyze and deploy Lambda function
- `status` - Check deployment status
- `--help` - Show help information

### Global Options

- `--profile` - AWS profile to use (default: default)
- `--region` - AWS region (default: us-east-1)  
- `--log-level` - Logging level (DEBUG, INFO, WARNING, ERROR)

### Deploy Options

- `--function-name` - Lambda function name (required)
- `--repository-name` - ECR repository name (optional)
- `--dry-run` - Preview changes without deployment

## Requirements File

Your `requirements.txt` must be present in the Lambda source directory. Example:

```
boto3>=1.26.0
requests>=2.31.0
pydantic>=1.10.0
```

## Generated Artifacts

The tool automatically generates:

1. **Dockerfile** - Optimized for Lambda container runtime
2. **buildspec.yml** - CodeBuild configuration for CI/CD
3. **CloudFormation template** - Infrastructure as code

These are created in your source directory and can be customized as needed.

## AWS Resources Created

The deployment creates:

- ECR repository for container images
- CodeCommit repository for source code (optional)
- CodeBuild project for CI/CD pipeline
- IAM roles with minimal required permissions
- CloudFormation stack for Lambda function
- CloudWatch log groups

## Troubleshooting

### Common Issues

**"requirements.txt not found"**
```bash
# Ensure requirements.txt exists in your source directory
ls ./my-lambda/requirements.txt
```

**"AWS credentials not configured"**
```bash
# Configure AWS credentials
aws configure
# Or set environment variables
export AWS_PROFILE=your-profile
```

**"Bedrock access denied"**
- Enable model access in AWS Bedrock console
- Ensure your IAM user/role has Bedrock permissions

**"Build failed with Docker errors"**
- Check your requirements.txt for invalid packages
- Ensure all dependencies are compatible with Lambda runtime

### Debug Mode

For detailed logging:
```bash
actig-lambda-deployer deploy ./src --function-name my-func --log-level DEBUG
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- GitHub Issues: [Report bugs or request features](https://github.com/gao-dennis/actig-lambda-deployer/issues)
- Documentation: [Full documentation](https://github.com/gao-dennis/actig-lambda-deployer)
