"""
Logging configuration for MinIO Adapter.
Provides structured logging with JSON format for production environments.
"""

import logging
import logging.config
import os
import sys
from typing import Dict, Any


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    log_file: str = None
) -> None:
    """
    Setup logging configuration for the MinIO adapter.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type ('json' or 'standard')
        log_file: Optional log file path
    """
    
    # Determine log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure formatters
    formatters = {
        'json': {
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d}',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    }
    
    # Configure handlers
    handlers = {
        'console': {
            'class': 'logging.StreamHandler',
            'level': level,
            'formatter': log_format,
            'stream': sys.stdout
        }
    }
    
    # Add file handler if specified
    if log_file:
        handlers['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': logging.DEBUG,
            'formatter': 'standard',
            'filename': log_file,
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
    
    # Configure loggers
    loggers = {
        'minio_adapter': {
            'level': level,
            'handlers': ['console'] + (['file'] if log_file else []),
            'propagate': False
        },
        'minio': {
            'level': logging.WARNING,
            'handlers': ['console'] + (['file'] if log_file else []),
            'propagate': False
        }
    }
    
    # Build configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': formatters,
        'handlers': handlers,
        'loggers': loggers,
        'root': {
            'level': level,
            'handlers': ['console']
        }
    }
    
    # Apply configuration
    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def configure_from_environment() -> None:
    """
    Configure logging from environment variables.
    
    Environment variables:
    - LOG_LEVEL: Logging level (default: INFO)
    - LOG_FORMAT: Format type (default: json)
    - LOG_FILE: Log file path (optional)
    """
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_format = os.getenv('LOG_FORMAT', 'json')
    log_file = os.getenv('LOG_FILE')
    
    setup_logging(log_level, log_format, log_file)


# Auto-configure logging when module is imported
if not logging.getLogger().handlers:
    configure_from_environment()
