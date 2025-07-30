import json
from typing import Dict, Any
from .utils.exceptions import ArtifactGenerationError

class ArtifactGenerator:
    """Generates deployment artifacts using AI"""
    
    def __init__(self, client_manager):
        self.client_manager = client_manager
        self.bedrock_client = client_manager.get_client('bedrock-runtime')
    
    def generate_artifacts(self, analysis_result: Dict[str, Any]) -> Dict[str, str]:
        """Generate deployment artifacts (excludes requirements.txt - user provided)"""
        try:
            artifacts = {}
            
            # Generate Dockerfile
            artifacts['Dockerfile'] = self._generate_dockerfile(analysis_result)
            
            # Generate buildspec.yml
            artifacts['buildspec.yml'] = self._generate_buildspec(analysis_result)
            
            # Generate CloudFormation template
            artifacts['cloudformation.yaml'] = self._generate_cloudformation(analysis_result)
            
            return artifacts
            
        except Exception as e:
            raise ArtifactGenerationError(f"Artifact generation failed: {e}")
    
    def _generate_dockerfile(self, analysis: Dict[str, Any]) -> str:
        """Generate optimized Dockerfile using Claude"""
        
        ai_analysis = analysis.get('ai_analysis', {})
        base_image = ai_analysis.get('base_image_recommendation', 'public.ecr.aws/lambda/python:3.12')
        
        prompt = f"""
<task>
Generate a production-ready Dockerfile for an AWS Lambda function container image following the team's standard pattern.
</task>

<requirements>
- Use {base_image} as base image
- Follow the team's working Dockerfile pattern
- Copy requirements.txt to LAMBDA_TASK_ROOT (user provides this file)
- Comment out build tools by default (only include if packages require compilation)
- Upgrade pip before installing dependencies
- Install packages from requirements.txt
- Copy Python files to LAMBDA_TASK_ROOT
- Set CMD to lambda handler
</requirements>

<context>
Base image: {base_image}
Handler: {ai_analysis.get('handler_function', 'lambda_function.lambda_handler')}
</context>

<team_standard_dockerfile>
FROM public.ecr.aws/lambda/python:3.12

# Copy over requirements.txt
COPY requirements.txt ${{LAMBDA_TASK_ROOT}}

# Install necessary build tools (use dnf for Amazon Linux 2023)
# Only include if packages require compilation - most packages don't need this
# RUN dnf install -y git gcc gcc-c++ python3-devel

# Upgrade pip before installing dependencies
RUN pip install --upgrade pip

# Install the packages
RUN pip install -r requirements.txt

# Copy the function code
COPY *.py ${{LAMBDA_TASK_ROOT}}

# Bind the lambda handler
CMD [ "lambda_function.lambda_handler" ]
</team_standard_dockerfile>

<output_format>
Return only the Dockerfile content following the team standard pattern exactly, adjusting only the base image and handler as needed.
</output_format>
"""
        
        return self._invoke_claude(prompt)
    
    
    def _generate_buildspec(self, analysis: Dict[str, Any]) -> str:
        """Generate CodeBuild buildspec.yml"""
        
        prompt = """
<task>
Generate a buildspec.yml file for AWS CodeBuild following the team's standard pattern.
</task>

<requirements>
- Use version: 0.2 format
- Follow the team's working buildspec.yml pattern
- Use environment variables: $AWS_DEFAULT_REGION, $AWS_ACCOUNT_ID, $IMAGE_REPO_NAME, $IMAGE_TAG
- Handle ECR authentication: aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
- Build Docker image: docker build -t $IMAGE_REPO_NAME:$IMAGE_TAG .
- Tag and push image: docker tag $IMAGE_REPO_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG
- Include ECR login in pre_build phase using environment variables
- Build and tag Docker image in build phase using environment variables
- Push image in post_build phase using environment variables
</requirements>

<team_standard_pattern>
The team uses this pattern:
- pre_build: ECR login with region and account ID
- build: docker build and docker tag commands
- post_build: docker push command
- Uses date logging and descriptive echo statements
</team_standard_pattern>

<current_variables>
Use these environment variables:
- $AWS_DEFAULT_REGION for region
- $AWS_ACCOUNT_ID for account ID  
- $IMAGE_REPO_NAME for repository name
- $IMAGE_TAG for image tag
</current_variables>

<output_format>
Return only the buildspec.yml content in YAML format without any runtime sections.
</output_format>
"""
        
        return self._invoke_claude(prompt)
    
    def _generate_cloudformation(self, analysis: Dict[str, Any]) -> str:
        """Generate CloudFormation template"""
        
        ai_analysis = analysis.get('ai_analysis', {})
        memory_size = ai_analysis.get('estimated_memory', 512)
        timeout = ai_analysis.get('estimated_timeout', 60)
        
        prompt = f"""
<task>
Generate an AWS CloudFormation template for deploying a Lambda function with container image.
</task>

<requirements>
- Lambda function with PackageType: Image
- Do NOT include ECR repository (it's created separately)
- IAM execution role with proper permissions
- Do NOT include CloudWatch log group (Lambda creates it automatically)
- Parameters: FunctionName and ImageUri
- Outputs for function ARN
- Keep template simple and focused on Lambda function only
</requirements>

<specifications>
Memory Size: {memory_size} MB
Timeout: {timeout} seconds
Handler: {ai_analysis.get('handler_function', 'lambda_function.lambda_handler')}
</specifications>

<example_structure>
Parameters:
  FunctionName:
    Type: String
  ImageUri:
    Type: String

Resources:
  LambdaExecutionRole:
    Type: AWS::IAM::Role
    # IAM role for Lambda execution
    
  LambdaFunction:
    Type: AWS::Lambda::Function
    Properties:
      PackageType: Image
      Code:
        ImageUri: !Ref ImageUri
      # Other Lambda properties

Outputs:
  FunctionArn:
    Value: !GetAtt LambdaFunction.Arn
</example_structure>

<output_format>
Return only the CloudFormation template in YAML format.
</output_format>
"""
        
        return self._invoke_claude(prompt)
    
    def _invoke_claude(self, prompt: str) -> str:
        """Invoke Claude model with error handling"""
        try:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": prompt}]
                    }
                ]
            }
            
            response = self.bedrock_client.invoke_model(
                modelId='anthropic.claude-3-5-sonnet-20240620-v1:0',
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text'].strip()
            
        except Exception as e:
            raise ArtifactGenerationError(f"Claude invocation failed: {e}")