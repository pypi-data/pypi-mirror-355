"""Logging configuration for AI Research Planner."""

import logging
import sys
from pathlib import Path
from typing import Optional


def get_logger(name: str, level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Get configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level
        log_file: Optional log file path
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Set level
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def setup_logging(config_dict: dict) -> None:
    """Setup logging from configuration dictionary."""
    log_config = config_dict.get('logging', {})
    
    level = log_config.get('level', 'INFO')
    log_file = log_config.get('file')
    log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)
