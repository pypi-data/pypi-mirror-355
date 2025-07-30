"""
Logger utility module for consistent logging across the application.
"""

import logging
import sys
from typing import Optional


def get_logger(name: str, level: Optional[str] = None, format_string: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name (str): Logger name (usually __name__)
        level (str, optional): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string (str, optional): Custom format string for log messages
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if logger doesn't have handlers (avoid duplicate configuration)
    if not logger.handlers:
        # Set default level
        log_level = level or 'INFO'
        logger.setLevel(getattr(logging, log_level.upper()))
        
        # Set default format
        default_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(format_string or default_format)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Prevent propagation to root logger to avoid duplicate messages
        logger.propagate = False
    
    return logger


def configure_file_logging(logger: logging.Logger, filename: str, level: Optional[str] = None):
    """
    Add file logging to an existing logger.
    
    Args:
        logger (logging.Logger): Logger instance to configure
        filename (str): Path to log file
        level (str, optional): Logging level for file handler
    """
    # Create file handler
    file_handler = logging.FileHandler(filename)
    
    # Set level for file handler
    if level:
        file_handler.setLevel(getattr(logging, level.upper()))
    
    # Use the same formatter as existing handlers
    if logger.handlers:
        formatter = logger.handlers[0].formatter
    else:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def disable_logging():
    """Disable all logging by setting root logger to CRITICAL level."""
    logging.getLogger().setLevel(logging.CRITICAL)


def enable_logging(level: str = 'INFO'):
    """
    Enable logging by setting root logger level.
    
    Args:
        level (str): Logging level to set
    """
    logging.getLogger().setLevel(getattr(logging, level.upper()))
