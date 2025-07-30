class DeploymentError(Exception):
    """Base exception for deployment errors"""
    pass

class AWSConnectionError(DeploymentError):
    """AWS connection and authentication errors"""
    pass

class CodeAnalysisError(DeploymentError):
    """Code analysis specific errors"""
    pass

class ArtifactGenerationError(DeploymentError):
    """Artifact generation errors"""
    pass

class ValidationError(DeploymentError):
    """Validation errors"""
    pass