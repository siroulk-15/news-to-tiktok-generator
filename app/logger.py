"""Logging configuration."""

import logging
import sys
from pathlib import Path

from app.config import settings


def setup_logger(name: str = None) -> logging.Logger:
    """Configure and return a logger."""
    
    logger = logging.getLogger(name or __name__)
    logger.setLevel(settings.log_level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.log_level)
    
    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    
    # Add handler if not already present
    if not logger.handlers:
        logger.addHandler(console_handler)
    
    return logger


# Root logger
root_logger = setup_logger("ntg")
