import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Setup logging configuration"""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_file = os.getenv("LOG_FILE", "./logs/app.log")
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, log_level))
    root_logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, log_level))
    root_logger.addHandler(console_handler)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module"""
    return logging.getLogger(name)

# Initialize logging when module is imported
setup_logging()
