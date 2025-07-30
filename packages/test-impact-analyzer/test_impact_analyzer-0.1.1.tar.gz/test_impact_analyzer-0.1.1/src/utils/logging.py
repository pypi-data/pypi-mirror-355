"""Logging configuration for the application."""
import logging
import sys

def setup_logging():
    """Configure logging for the application."""
    
    logger = logging.getLogger('test-impact-analyzer')
    logger.setLevel(logging.INFO)
    
    # Create console handler and set level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()
