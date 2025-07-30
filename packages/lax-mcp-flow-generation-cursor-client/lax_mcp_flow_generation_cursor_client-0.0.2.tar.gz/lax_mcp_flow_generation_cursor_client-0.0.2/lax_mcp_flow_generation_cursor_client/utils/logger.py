import logging
import sys
from typing import Optional
from lax_mcp_flow_generation_cursor_client.core.settings import settings

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a configured logger instance."""
    
    logger_name = name or __name__
    logger = logging.getLogger(logger_name)
    
    # Avoid adding multiple handlers to the same logger
    if logger.handlers:
        return logger
    
    # Set log level from settings
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    # Prevent propagation to avoid duplicate logs
    logger.propagate = False
    
    return logger 