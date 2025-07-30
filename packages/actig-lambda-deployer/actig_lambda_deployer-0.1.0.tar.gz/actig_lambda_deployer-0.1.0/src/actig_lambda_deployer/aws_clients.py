import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from functools import lru_cache
from .utils.exceptions import AWSConnectionError

class AWSClientManager:
    """Centralized AWS client management with caching"""
    
    def __init__(self, profile_name='default', region_name='us-east-1'):
        self.profile_name = profile_name
        self.region_name = region_name
        self._session = None
        self._clients = {}
    
    @property
    def session(self):
        """Lazy initialization of boto3 session"""
        if self._session is None:
            try:
                self._session = boto3.Session(
                    profile_name=self.profile_name,
                    region_name=self.region_name
                )
            except NoCredentialsError:
                raise AWSConnectionError(
                    f"AWS credentials not found for profile: {self.profile_name}"
                )
        return self._session
    
    @lru_cache(maxsize=10)
    def get_client(self, service_name):
        """Get cached AWS service client"""
        if service_name not in self._clients:
            try:
                self._clients[service_name] = self.session.client(service_name)
            except ClientError as e:
                raise AWSConnectionError(
                    f"Failed to create {service_name} client: {e}"
                )
        return self._clients[service_name]
    
    def get_account_id(self):
        """Get current AWS account ID"""
        sts = self.get_client('sts')
        return sts.get_caller_identity()['Account']
    
    def verify_permissions(self):
        """Verify required AWS permissions"""
        required_services = ['bedrock-runtime', 'lambda', 'ecr', 'cloudformation']
        
        for service in required_services:
            try:
                client = self.get_client(service)
                # Simple permission check
                if service == 'bedrock-runtime':
                    client.list_foundation_models()
                elif service == 'lambda':
                    client.list_functions(MaxItems=1)
                elif service == 'ecr':
                    client.describe_repositories(maxResults=1)
                elif service == 'cloudformation':
                    client.list_stacks(StackStatusFilter=['CREATE_COMPLETE'])
            except ClientError as e:
                if e.response['Error']['Code'] in ['AccessDenied', 'UnauthorizedOperation']:
                    raise AWSConnectionError(
                        f"Insufficient permissions for {service}: {e}"
                    )