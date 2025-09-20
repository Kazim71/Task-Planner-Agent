"""
Logging configuration for the Task Planner Agent.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_file: str = None) -> logging.Logger:
    """
    Set up comprehensive logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        
    Returns:
        logging.Logger: Configured logger
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Default log file
    if log_file is None:
        log_file = log_dir / f"task_planner_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Error file handler (only errors and above)
    error_file = log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)
    
    # API request handler (for tracking API calls)
    api_file = log_dir / f"api_requests_{datetime.now().strftime('%Y%m%d')}.log"
    api_handler = logging.handlers.RotatingFileHandler(
        api_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    api_handler.setLevel(logging.INFO)
    api_handler.setFormatter(detailed_formatter)
    
    # Create API logger
    api_logger = logging.getLogger('api_requests')
    api_logger.setLevel(logging.INFO)
    api_logger.addHandler(api_handler)
    api_logger.propagate = False  # Don't propagate to root logger
    
    # Database operations logger
    db_file = log_dir / f"database_{datetime.now().strftime('%Y%m%d')}.log"
    db_handler = logging.handlers.RotatingFileHandler(
        db_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    db_handler.setLevel(logging.INFO)
    db_handler.setFormatter(detailed_formatter)
    
    # Create database logger
    db_logger = logging.getLogger('database')
    db_logger.setLevel(logging.INFO)
    db_logger.addHandler(db_handler)
    db_logger.propagate = False  # Don't propagate to root logger
    
    # External API logger
    external_api_file = log_dir / f"external_apis_{datetime.now().strftime('%Y%m%d')}.log"
    external_api_handler = logging.handlers.RotatingFileHandler(
        external_api_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    external_api_handler.setLevel(logging.INFO)
    external_api_handler.setFormatter(detailed_formatter)
    
    # Create external API logger
    external_api_logger = logging.getLogger('external_apis')
    external_api_logger.setLevel(logging.INFO)
    external_api_logger.addHandler(external_api_handler)
    external_api_logger.propagate = False  # Don't propagate to root logger
    
    # Log startup message
    logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)


def log_api_request(logger: logging.Logger, method: str, endpoint: str, status_code: int, 
                   response_time: float, user_agent: str = None, ip_address: str = None):
    """
    Log API request details.
    
    Args:
        logger: Logger instance
        method: HTTP method
        endpoint: API endpoint
        status_code: HTTP status code
        response_time: Response time in seconds
        user_agent: User agent string
        ip_address: Client IP address
    """
    api_logger = logging.getLogger('api_requests')
    api_logger.info(
        f"API Request - {method} {endpoint} | "
        f"Status: {status_code} | "
        f"Response Time: {response_time:.3f}s | "
        f"IP: {ip_address or 'unknown'} | "
        f"User-Agent: {user_agent or 'unknown'}"
    )


def log_database_operation(logger: logging.Logger, operation: str, table: str, 
                          record_id: str = None, success: bool = True, 
                          error: str = None, execution_time: float = None):
    """
    Log database operation details.
    
    Args:
        logger: Logger instance
        operation: Database operation (INSERT, UPDATE, DELETE, SELECT)
        table: Table name
        record_id: Record ID if applicable
        success: Whether operation was successful
        error: Error message if operation failed
        execution_time: Execution time in seconds
    """
    db_logger = logging.getLogger('database')
    status = "SUCCESS" if success else "FAILED"
    time_str = f" | Time: {execution_time:.3f}s" if execution_time else ""
    error_str = f" | Error: {error}" if error else ""
    
    db_logger.info(
        f"DB {operation} - Table: {table} | "
        f"Record ID: {record_id or 'N/A'} | "
        f"Status: {status}{time_str}{error_str}"
    )


def log_external_api_call(logger: logging.Logger, service: str, endpoint: str, 
                         method: str, status_code: int = None, response_time: float = None,
                         error: str = None, request_data: dict = None):
    """
    Log external API call details.
    
    Args:
        logger: Logger instance
        service: External service name (Gemini, Tavily, OpenWeatherMap)
        endpoint: API endpoint
        method: HTTP method
        status_code: HTTP status code
        response_time: Response time in seconds
        error: Error message if call failed
        request_data: Request data (sanitized)
    """
    external_api_logger = logging.getLogger('external_apis')
    status = f"Status: {status_code}" if status_code else "Status: Unknown"
    time_str = f" | Time: {response_time:.3f}s" if response_time else ""
    error_str = f" | Error: {error}" if error else ""
    data_str = f" | Data: {request_data}" if request_data else ""
    
    external_api_logger.info(
        f"External API - {service} | "
        f"{method} {endpoint} | "
        f"{status}{time_str}{error_str}{data_str}"
    )


def log_security_event(logger: logging.Logger, event_type: str, details: str, 
                      severity: str = "INFO", ip_address: str = None, 
                      user_agent: str = None):
    """
    Log security-related events.
    
    Args:
        logger: Logger instance
        event_type: Type of security event
        details: Event details
        severity: Severity level (INFO, WARNING, ERROR, CRITICAL)
        ip_address: Client IP address
        user_agent: User agent string
    """
    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.INFO)
    
    # Add file handler for security events
    if not security_logger.handlers:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        security_file = log_dir / f"security_{datetime.now().strftime('%Y%m%d')}.log"
        security_handler = logging.handlers.RotatingFileHandler(
            security_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=7  # Keep more security logs
        )
        security_handler.setLevel(logging.INFO)
        security_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        security_logger.addHandler(security_handler)
        security_logger.propagate = False
    
    log_level = getattr(logging, severity.upper(), logging.INFO)
    security_logger.log(
        log_level,
        f"SECURITY - {event_type} | "
        f"Details: {details} | "
        f"IP: {ip_address or 'unknown'} | "
        f"User-Agent: {user_agent or 'unknown'}"
    )


def sanitize_log_data(data: dict) -> dict:
    """
    Sanitize sensitive data before logging.
    
    Args:
        data: Dictionary containing potentially sensitive data
        
    Returns:
        dict: Sanitized dictionary
    """
    sensitive_keys = [
        'password', 'api_key', 'token', 'secret', 'auth', 'credential',
        'key', 'pass', 'pwd', 'private', 'sensitive'
    ]
    
    sanitized = {}
    for key, value in data.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_log_data(value)
        else:
            sanitized[key] = value
    
    return sanitized
