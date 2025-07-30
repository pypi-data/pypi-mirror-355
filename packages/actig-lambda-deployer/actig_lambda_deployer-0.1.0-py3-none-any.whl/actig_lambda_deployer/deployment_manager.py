# Updated deployment_manager.py with CodeCommit integration

import json
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
from git import Repo
from .utils.exceptions import DeploymentError

class DeploymentManager:
    """Manages end-to-end deployment process"""
    
    def __init__(self, client_manager, config):
        self.client_manager = client_manager
        self.config = config
        self.codecommit = client_manager.get_client('codecommit')
        self.codebuild = client_manager.get_client('codebuild')
        self.ecr = client_manager.get_client('ecr')
        self.cloudformation = client_manager.get_client('cloudformation')
        self.lambda_client = client_manager.get_client('lambda')
    
    def deploy(self, function_name: str, repository_name: str, 
               source_path: Path, artifacts: Dict[str, str]) -> Dict[str, Any]:
        """Execute complete deployment workflow"""
        
        deployment_result = {}
        
        try:
            # Step 1: Create ECR repository
            repo_uri = self._create_ecr_repository(repository_name)
            deployment_result['repository_uri'] = repo_uri
            
            # Step 2: Write artifacts to source directory
            self._write_artifacts(source_path, artifacts)
            
            # Step 3: Create CodeCommit repository and push code
            codecommit_url = self._setup_codecommit_repository(
                f"{function_name}-source", 
                source_path
            )
            deployment_result['codecommit_url'] = codecommit_url
            
            # Step 4: Create/update CodeBuild project
            build_project = self._create_codebuild_project(
                function_name, 
                repository_name, 
                codecommit_url
            )
            deployment_result['build_project'] = build_project
            
            # Step 5: Trigger build
            build_result = self._trigger_build(build_project)
            deployment_result['build_id'] = build_result['build']['id']
            
            # Step 6: Wait for build completion
            image_uri = self._wait_for_build(build_result['build']['id'], repo_uri)
            deployment_result['image_uri'] = image_uri
            
            # Step 7: Deploy CloudFormation stack
            stack_result = self._deploy_cloudformation_stack(
                function_name, image_uri, artifacts['cloudformation.yaml']
            )
            deployment_result['stack_name'] = stack_result['StackId']
            
            # Step 8: Get function ARN
            function_arn = self._get_function_arn(function_name)
            deployment_result['function_arn'] = function_arn
            
            return deployment_result
            
        except Exception as e:
            # Cleanup on failure
            self._cleanup_on_failure(deployment_result)
            raise DeploymentError(f"Deployment failed: {e}")
    
    def _create_codecommit_repository(self, repo_name: str) -> str:
        """Create CodeCommit repository if it doesn't exist"""
        try:
            response = self.codecommit.create_repository(
                repositoryName=repo_name,
                repositoryDescription=f"Lambda deployment repository: {repo_name}",
                tags={
                    'Purpose': 'lambda-deployment',
                    'ManagedBy': 'lambda-deployer-cli'
                }
            )
            
            # Set repository triggers for CodeBuild
            self._setup_codecommit_triggers(repo_name)
            
            # Return git-remote-codecommit URL instead of HTTPS
            return f"codecommit::{self.client_manager.region_name}://{repo_name}"
            
        except self.codecommit.exceptions.RepositoryNameExistsException:
            # Repository already exists, return git-remote-codecommit URL
            return f"codecommit::{self.client_manager.region_name}://{repo_name}"
    
    def _setup_codecommit_repository(self, repo_name: str, source_path: Path) -> str:
        """Setup CodeCommit repository and push code"""
        
        # Create or get repository
        clone_url = self._create_codecommit_repository(repo_name)
        
        # Clone repository to temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_repo_path = Path(temp_dir) / repo_name
            region = self.client_manager.region_name
            
            # Configure git credentials for CodeCommit
            self._configure_git_credentials()
            
            try:
                # Try to clone the repository first
                try:
                    repo = Repo.clone_from(clone_url, temp_repo_path, allow_unsafe_protocols=True)
                except Exception:
                    # Repository is empty or doesn't exist, initialize new repository
                    repo = Repo.init(temp_repo_path)
                    repo.create_remote('origin', clone_url)
                
                # Copy source files to repository
                for item in source_path.iterdir():
                    if item.name == '.git':
                        continue
                    
                    dest = temp_repo_path / item.name
                    if item.is_dir():
                        shutil.copytree(item, dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, dest)
                
                # Add and commit files
                repo.index.add('*')
                repo.index.commit(f'Deploy {repo_name} - {time.strftime("%Y%m%d-%H%M%S")}')
                
                # Push to CodeCommit
                origin = repo.remote('origin')
                try:
                    # Try to push to main branch first
                    origin.push('HEAD:main', allow_unsafe_protocols=True)
                except Exception:
                    # If that fails, try pushing as the default branch
                    origin.push('HEAD', allow_unsafe_protocols=True)
                
            except Exception as e:
                raise DeploymentError(f"Failed to push to CodeCommit: {e}")
        
        return clone_url
    
    def _configure_git_credentials(self):
        """Configure git credentials for CodeCommit using git-remote-codecommit"""
        import subprocess
        
        try:
            # Check if git-remote-codecommit is installed
            result = subprocess.run([
                'pip', 'show', 'git-remote-codecommit'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                raise DeploymentError(
                    "git-remote-codecommit is not installed. Please install it with: pip install git-remote-codecommit"
                )
                
            # Test AWS credentials
            result = subprocess.run([
                'aws', 'sts', 'get-caller-identity'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise DeploymentError(f"AWS credentials not configured properly: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise DeploymentError("AWS credential check timed out")
        except subprocess.CalledProcessError as e:
            raise DeploymentError(f"Failed to verify git-remote-codecommit setup: {e}")
    
    def _is_repository_empty(self, repo_name: str) -> bool:
        """Check if CodeCommit repository is empty"""
        try:
            self.codecommit.get_branch(
                repositoryName=repo_name,
                branchName='main'
            )
            return False
        except self.codecommit.exceptions.BranchDoesNotExistException:
            return True
    
    def _setup_codecommit_triggers(self, repo_name: str):
        """Setup repository triggers for automated builds"""
        # This is optional - you can set up triggers to automatically
        # start CodeBuild when code is pushed
        try:
            self.codecommit.put_repository_triggers(
                repositoryName=repo_name,
                triggers=[
                    {
                        'name': 'BuildTrigger',
                        'destinationArn': f'arn:aws:sns:{self.client_manager.region_name}:{self.client_manager.get_account_id()}:codecommit-builds',
                        'branches': ['main'],
                        'events': ['all']
                    }
                ]
            )
        except Exception as e:
            # Triggers are optional, don't fail deployment
            print(f"Warning: Could not set up repository triggers: {e}")
    
    def _create_codebuild_project(self, function_name: str, 
                                  repository_name: str, 
                                  codecommit_url: str) -> str:
        """Create or update CodeBuild project for CodeCommit source"""
        project_name = f"{function_name}-build"
        account_id = self.client_manager.get_account_id()
        region = self.client_manager.region_name
        
        # Extract repository name from git-remote-codecommit URL format
        # codecommit::us-east-1://repo-name -> repo-name
        codecommit_repo_name = codecommit_url.split('://')[-1]
        
        # Convert to HTTPS URL for CodeBuild
        codebuild_source_url = f"https://git-codecommit.{region}.amazonaws.com/v1/repos/{codecommit_repo_name}"
        
        # Create service role for CodeBuild
        service_role_arn = self._create_codebuild_service_role(project_name)
        
        project_config = {
            'name': project_name,
            'description': f'Build project for {function_name} Lambda function',
            'source': {
                'type': 'CODECOMMIT',
                'location': codebuild_source_url,
                'gitCloneDepth': 1,
                'buildspec': 'buildspec.yml',  # Uses the generated buildspec.yml
                'gitSubmodulesConfig': {
                    'fetchSubmodules': False
                }
            },
            'artifacts': {
                'type': 'NO_ARTIFACTS'
            },
            'environment': {
                'type': 'LINUX_CONTAINER',
                'image': 'aws/codebuild/standard:7.0',  # Updated to newer image with Docker support
                'computeType': 'BUILD_GENERAL1_SMALL',
                'privilegedMode': True,  # Required for Docker
                'environmentVariables': [
                    {'name': 'AWS_DEFAULT_REGION', 'value': region},
                    {'name': 'AWS_ACCOUNT_ID', 'value': account_id},
                    {'name': 'IMAGE_REPO_NAME', 'value': repository_name},
                    {'name': 'IMAGE_TAG', 'value': 'latest'}
                ]
            },
            'serviceRole': service_role_arn,
            'timeoutInMinutes': 60,
            'logsConfig': {
                'cloudWatchLogs': {
                    'status': 'ENABLED',
                    'groupName': f'/aws/codebuild/{project_name}'
                }
            }
        }
        
        try:
            response = self.codebuild.create_project(**project_config)
        except self.codebuild.exceptions.ResourceAlreadyExistsException:
            # Update existing project
            response = self.codebuild.update_project(**project_config)
        
        return project_name
    
    def _create_codebuild_service_role(self, project_name: str) -> str:
        """Create IAM role for CodeBuild with CodeCommit permissions"""
        iam = self.client_manager.get_client('iam')
        role_name = f"CodeBuildRole-{project_name}"
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "codebuild.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "arn:aws:logs:*:*:*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "ecr:GetAuthorizationToken",
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:PutImage",
                        "ecr:InitiateLayerUpload",
                        "ecr:UploadLayerPart",
                        "ecr:CompleteLayerUpload"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "codecommit:GitPull",
                        "codecommit:GetBranch",
                        "codecommit:GetCommit",
                        "codecommit:GetRepository"
                    ],
                    "Resource": f"arn:aws:codecommit:{self.client_manager.region_name}:{self.client_manager.get_account_id()}:*"
                }
            ]
        }
        
        try:
            # Create role
            iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description=f"Service role for CodeBuild project {project_name}"
            )
            
            # Attach inline policy
            iam.put_role_policy(
                RoleName=role_name,
                PolicyName='CodeBuildPolicy',
                PolicyDocument=json.dumps(policy_document)
            )
            
            # Wait for role to propagate
            time.sleep(10)
            
        except iam.exceptions.EntityAlreadyExistsException:
            # Role already exists, update policy
            iam.put_role_policy(
                RoleName=role_name,
                PolicyName='CodeBuildPolicy',
                PolicyDocument=json.dumps(policy_document)
            )
        
        return f"arn:aws:iam::{self.client_manager.get_account_id()}:role/{role_name}"
    
    # Note: _upload_source_to_s3 is not needed when using CodeCommit
    # but included here for reference if you want to use S3 as source
    def _upload_source_to_s3(self, source_path: Path, project_name: str) -> str:
        """Upload source code to S3 (alternative to CodeCommit)"""
        s3 = self.client_manager.get_client('s3')
        bucket_name = f"codebuild-sources-{self.client_manager.get_account_id()}-{self.client_manager.region_name}"
        
        # Create bucket if it doesn't exist
        try:
            s3.create_bucket(Bucket=bucket_name)
        except s3.exceptions.BucketAlreadyExists:
            pass
        
        # Create zip of source
        import zipfile
        import io
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in source_path.rglob('*'):
                if file_path.is_file() and '.git' not in str(file_path):
                    zip_file.write(file_path, file_path.relative_to(source_path))
        
        # Upload to S3
        key = f"{project_name}/source-{int(time.time())}.zip"
        zip_buffer.seek(0)
        s3.put_object(Bucket=bucket_name, Key=key, Body=zip_buffer.getvalue())
        
        return f"{bucket_name}/{key}"
    
    def _write_artifacts(self, source_path: Path, artifacts: Dict[str, str]):
        """Write generated artifacts to source directory"""
        # Check if requirements.txt exists in source directory
        requirements_path = source_path / 'requirements.txt'
        if not requirements_path.exists():
            raise DeploymentError(
                f"requirements.txt not found in {source_path}. "
                "Please provide a requirements.txt file in your Lambda source directory."
            )
        
        # Write generated artifacts (excludes requirements.txt)
        for filename, content in artifacts.items():
            file_path = source_path / filename
            with open(file_path, 'w') as f:
                f.write(content)
    
    def _create_ecr_repository(self, repository_name: str) -> str:
        """Create ECR repository if it doesn't exist"""
        try:
            response = self.ecr.create_repository(
                repositoryName=repository_name,
                imageScanningConfiguration={'scanOnPush': True},
                encryptionConfiguration={'encryptionType': 'AES256'}
            )
            repo_uri = response['repository']['repositoryUri']
            
            # Set lifecycle policy
            lifecycle_policy = {
                "rules": [
                    {
                        "rulePriority": 1,
                        "selection": {
                            "tagStatus": "untagged",
                            "countType": "sinceImagePushed",
                            "countUnit": "days",
                            "countNumber": 1
                        },
                        "action": {"type": "expire"}
                    }
                ]
            }
            
            self.ecr.put_lifecycle_policy(
                repositoryName=repository_name,
                lifecyclePolicyText=json.dumps(lifecycle_policy)
            )
            
            return repo_uri
            
        except self.ecr.exceptions.RepositoryAlreadyExistsException:
            response = self.ecr.describe_repositories(repositoryNames=[repository_name])
            return response['repositories'][0]['repositoryUri']
    
    def _trigger_build(self, project_name: str) -> Dict[str, Any]:
        """Start CodeBuild execution"""
        response = self.codebuild.start_build(projectName=project_name)
        return response
    
    def _wait_for_build(self, build_id: str, repo_uri: str) -> str:
        """Wait for build completion and return image URI"""
        max_wait_time = 1800  # 30 minutes
        wait_interval = 30
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            response = self.codebuild.batch_get_builds(ids=[build_id])
            build = response['builds'][0]
            
            phase = build['currentPhase']
            status = build['buildStatus']
            
            if status == 'SUCCEEDED':
                # Build successful, return image URI
                return f"{repo_uri}:latest"
            elif status in ['FAILED', 'FAULT', 'STOPPED', 'TIMED_OUT']:
                raise DeploymentError(f"Build failed with status: {status}")
            
            time.sleep(wait_interval)
            elapsed_time += wait_interval
        
        raise DeploymentError("Build timed out")
    
    def _deploy_cloudformation_stack(self, function_name: str, 
                                     image_uri: str, template: str) -> Dict[str, Any]:
        """Deploy CloudFormation stack"""
        stack_name = f"{function_name}-stack"
        
        parameters = [
            {'ParameterKey': 'FunctionName', 'ParameterValue': function_name},
            {'ParameterKey': 'ImageUri', 'ParameterValue': image_uri}
        ]
        
        # Check if stack exists
        try:
            self.cloudformation.describe_stacks(StackName=stack_name)
            stack_exists = True
        except self.cloudformation.exceptions.ClientError:
            stack_exists = False
        
        if stack_exists:
            # Update existing stack
            try:
                response = self.cloudformation.update_stack(
                    StackName=stack_name,
                    TemplateBody=template,
                    Parameters=parameters,
                    Capabilities=['CAPABILITY_IAM']
                )
                # Wait for update completion
                waiter = self.cloudformation.get_waiter('stack_update_complete')
                waiter.wait(StackName=stack_name)
            except self.cloudformation.exceptions.ClientError as e:
                if 'No updates are to be performed' in str(e):
                    # Stack is already up to date
                    response = {'StackId': stack_name}
                else:
                    raise
        else:
            # Create new stack
            response = self.cloudformation.create_stack(
                StackName=stack_name,
                TemplateBody=template,
                Parameters=parameters,
                Capabilities=['CAPABILITY_IAM']
            )
            # Wait for creation completion
            waiter = self.cloudformation.get_waiter('stack_create_complete')
            waiter.wait(StackName=stack_name)
        
        return response
    
    def _get_function_arn(self, function_name: str) -> str:
        """Get Lambda function ARN"""
        try:
            response = self.lambda_client.get_function(FunctionName=function_name)
            return response['Configuration']['FunctionArn']
        except self.lambda_client.exceptions.ResourceNotFoundException:
            raise DeploymentError(f"Lambda function {function_name} not found")
    
    def _cleanup_on_failure(self, deployment_result: Dict[str, Any]):
        """Cleanup resources on deployment failure"""
        # This is optional but recommended for production
        # You can implement cleanup logic here based on what was created
        pass