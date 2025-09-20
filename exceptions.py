"""
Custom exceptions and error handling utilities for the Task Planner Agent.
"""

from typing import Dict, Any, Optional
from enum import Enum
import traceback
import logging

# Configure logging
logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Standardized error codes for the application."""
    
    # Validation errors (400-499)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    INVALID_DATE_FORMAT = "INVALID_DATE_FORMAT"
    GOAL_TOO_LONG = "GOAL_TOO_LONG"
    GOAL_TOO_SHORT = "GOAL_TOO_SHORT"
    
    # Authentication/Authorization errors (401-403)
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_API_KEY = "INVALID_API_KEY"
    MISSING_API_KEY = "MISSING_API_KEY"
    
    # Resource errors (404-409)
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    PLAN_NOT_FOUND = "PLAN_NOT_FOUND"
    CONFLICT = "CONFLICT"
    
    # External service errors (500-599)
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    GEMINI_API_ERROR = "GEMINI_API_ERROR"
    TAVILY_API_ERROR = "TAVILY_API_ERROR"
    WEATHER_API_ERROR = "WEATHER_API_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    
    # Internal server errors (500-599)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    UNEXPECTED_ERROR = "UNEXPECTED_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    
    # Rate limiting (429)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Service unavailable (503)
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    DATABASE_UNAVAILABLE = "DATABASE_UNAVAILABLE"
    AI_SERVICE_UNAVAILABLE = "AI_SERVICE_UNAVAILABLE"


class TaskPlannerException(Exception):
    """Base exception class for Task Planner Agent."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.original_error = original_error
        
        # Log the error
        self._log_error()
        
        super().__init__(self.message)
    
    def _log_error(self):
        """Log the error with appropriate level based on status code."""
        log_message = f"[{self.error_code.value}] {self.message}"
        
        if self.details:
            log_message += f" | Details: {self.details}"
        
        if self.original_error:
            log_message += f" | Original: {str(self.original_error)}"
        
        if self.status_code >= 500:
            logger.error(log_message)
            if self.original_error:
                logger.error(f"Original error traceback: {traceback.format_exc()}")
        elif self.status_code >= 400:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": {
                "code": self.error_code.value,
                "message": self.message,
                "status_code": self.status_code,
                "details": self.details,
                "timestamp": self._get_timestamp()
            }
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()


class ValidationError(TaskPlannerException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=400,
            details=details
        )


class AuthenticationError(TaskPlannerException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str, service: Optional[str] = None):
        details = {}
        if service:
            details["service"] = service
        
        super().__init__(
            message=message,
            error_code=ErrorCode.UNAUTHORIZED,
            status_code=401,
            details=details
        )


class ResourceNotFoundError(TaskPlannerException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        
        super().__init__(
            message=message,
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            status_code=404,
            details=details
        )


class ExternalServiceError(TaskPlannerException):
    """Raised when an external service fails."""
    
    def __init__(self, message: str, service: str, original_error: Optional[Exception] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            status_code=502,
            details={"service": service},
            original_error=original_error
        )


class DatabaseError(TaskPlannerException):
    """Raised when database operations fail."""
    
    def __init__(self, message: str, operation: Optional[str] = None, original_error: Optional[Exception] = None):
        details = {}
        if operation:
            details["operation"] = operation
        
        super().__init__(
            message=message,
            error_code=ErrorCode.DATABASE_ERROR,
            status_code=500,
            details=details,
            original_error=original_error
        )


class ConfigurationError(TaskPlannerException):
    """Raised when there's a configuration issue."""
    
    def __init__(self, message: str, setting: Optional[str] = None):
        details = {}
        if setting:
            details["setting"] = setting
        
        super().__init__(
            message=message,
            error_code=ErrorCode.CONFIGURATION_ERROR,
            status_code=500,
            details=details
        )


class RateLimitError(TaskPlannerException):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, message: str, service: Optional[str] = None, retry_after: Optional[int] = None):
        details = {}
        if service:
            details["service"] = service
        if retry_after:
            details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=429,
            details=details
        )


def handle_exception(exception: Exception) -> TaskPlannerException:
    """
    Convert any exception to a TaskPlannerException.
    
    Args:
        exception: The original exception
        
    Returns:
        TaskPlannerException: A properly formatted TaskPlannerException
    """
    if isinstance(exception, TaskPlannerException):
        return exception
    
    # Convert common exceptions to TaskPlannerException
    if isinstance(exception, ValueError):
        return ValidationError(
            message=str(exception),
            original_error=exception
        )
    elif isinstance(exception, KeyError):
        return ValidationError(
            message=f"Missing required field: {str(exception)}",
            field=str(exception),
            original_error=exception
        )
    elif isinstance(exception, ConnectionError):
        return ExternalServiceError(
            message="Connection failed",
            service="external_api",
            original_error=exception
        )
    elif isinstance(exception, TimeoutError):
        return ExternalServiceError(
            message="Request timeout",
            service="external_api",
            original_error=exception
        )
    else:
        return TaskPlannerException(
            message=f"Unexpected error: {str(exception)}",
            error_code=ErrorCode.UNEXPECTED_ERROR,
            status_code=500,
            original_error=exception
        )


def create_error_response(exception: TaskPlannerException) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        exception: The TaskPlannerException
        
    Returns:
        Dict: Standardized error response
    """
    return {
        "success": False,
        "error": exception.to_dict()["error"],
        "message": exception.message,
        "timestamp": exception._get_timestamp()
    }
