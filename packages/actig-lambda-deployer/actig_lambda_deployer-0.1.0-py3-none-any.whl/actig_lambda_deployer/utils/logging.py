import logging
import sys
from pathlib import Path
from typing import Optional
try:
    from pythonjsonlogger.json import JsonFormatter as jsonlogger_JsonFormatter
    jsonlogger = type('jsonlogger', (), {'JsonFormatter': jsonlogger_JsonFormatter})
except ImportError:
    # Fall back to old import for backwards compatibility
    from pythonjsonlogger import jsonlogger
from functools import wraps


def setup_logging(level: str = 'INFO', log_file: Optional[str] = None) -> logging.Logger:
    """Setup structured logging for the application"""
    
    # Create logger
    logger = logging.getLogger('actig_lambda_deployer')
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers to avoid duplicates
    logger.handlers = []
    
    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s %(funcName)s %(lineno)d'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        file_formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(funcName)s %(lineno)d'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """Get logger instance for a specific module"""
    logger_name = f'actig_lambda_deployer.{name}' if name else 'actig_lambda_deployer'
    return logging.getLogger(logger_name)


def log_function_call(logger: Optional[logging.Logger] = None):
    """Decorator for logging function calls with execution time"""
    if logger is None:
        logger = get_logger()
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            func_name = f"{func.__module__}.{func.__qualname__}"
            logger.info(f"Starting function: {func_name}")
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(
                    f"Completed function: {func_name}",
                    extra={
                        'execution_time_seconds': round(execution_time, 3),
                        'function_name': func_name,
                        'status': 'success'
                    }
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Failed function: {func_name} - {str(e)}",
                    extra={
                        'execution_time_seconds': round(execution_time, 3),
                        'function_name': func_name,
                        'status': 'error',
                        'error_type': type(e).__name__,
                        'error_message': str(e)
                    },
                    exc_info=True
                )
                raise
        return wrapper
    return decorator


def log_aws_api_call(service: str, operation: str, logger: Optional[logging.Logger] = None):
    """Decorator for logging AWS API calls"""
    if logger is None:
        logger = get_logger()
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            logger.info(
                f"AWS API call started: {service}.{operation}",
                extra={
                    'aws_service': service,
                    'aws_operation': operation,
                    'status': 'started'
                }
            )
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(
                    f"AWS API call completed: {service}.{operation}",
                    extra={
                        'aws_service': service,
                        'aws_operation': operation,
                        'execution_time_seconds': round(execution_time, 3),
                        'status': 'success'
                    }
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"AWS API call failed: {service}.{operation} - {str(e)}",
                    extra={
                        'aws_service': service,
                        'aws_operation': operation,
                        'execution_time_seconds': round(execution_time, 3),
                        'status': 'error',
                        'error_type': type(e).__name__,
                        'error_message': str(e)
                    },
                    exc_info=True
                )
                raise
        return wrapper
    return decorator


class ContextualLogger:
    """Logger with additional context for tracking deployment operations"""
    
    def __init__(self, logger: logging.Logger, context: dict = None):
        self.logger = logger
        self.context = context or {}
    
    def _log_with_context(self, level: int, message: str, extra: dict = None):
        """Log message with additional context"""
        combined_extra = self.context.copy()
        if extra:
            combined_extra.update(extra)
        
        self.logger.log(level, message, extra=combined_extra)
    
    def debug(self, message: str, extra: dict = None):
        self._log_with_context(logging.DEBUG, message, extra)
    
    def info(self, message: str, extra: dict = None):
        self._log_with_context(logging.INFO, message, extra)
    
    def warning(self, message: str, extra: dict = None):
        self._log_with_context(logging.WARNING, message, extra)
    
    def error(self, message: str, extra: dict = None, exc_info: bool = False):
        self.logger.error(message, extra={**(self.context or {}), **(extra or {})}, exc_info=exc_info)
    
    def exception(self, message: str, extra: dict = None):
        self.error(message, extra, exc_info=True)
    
    def add_context(self, key: str, value):
        """Add context to this logger instance"""
        self.context[key] = value
    
    def remove_context(self, key: str):
        """Remove context from this logger instance"""
        self.context.pop(key, None)
    
    def with_context(self, **kwargs):
        """Create a new logger instance with additional context"""
        new_context = self.context.copy()
        new_context.update(kwargs)
        return ContextualLogger(self.logger, new_context)


def get_deployment_logger(function_name: str = None, deployment_id: str = None) -> ContextualLogger:
    """Get a logger with deployment-specific context"""
    logger = get_logger('deployment')
    context = {}
    
    if function_name:
        context['function_name'] = function_name
    if deployment_id:
        context['deployment_id'] = deployment_id
    
    return ContextualLogger(logger, context)


# Configure boto3 logging to reduce noise
logging.getLogger('boto3').setLevel(logging.WARNING)
logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('git').setLevel(logging.WARNING)