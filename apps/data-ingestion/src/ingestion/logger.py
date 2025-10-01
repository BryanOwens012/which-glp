"""
Logging configuration for Reddit ingestion pipeline

Provides a centralized logging setup with:
- Console output (INFO level) with colored formatting
- File output (DEBUG level) with detailed information
- Rotating file handler to prevent log files from growing too large
- Structured log format with timestamps, levels, and module names
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logger(
    name: str = "ingestion",
    log_file: str = "ingestion.log",
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Configure and return a logger with console and file handlers

    Args:
        name: Logger name (default: "ingestion")
        log_file: Path to log file (default: "ingestion.log")
        console_level: Console logging level (default: INFO)
        file_level: File logging level (default: DEBUG)
        max_bytes: Max size per log file before rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Capture everything, handlers will filter

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )

    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler (INFO and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)

    # File handler with rotation (DEBUG and above)
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(file_formatter)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "ingestion") -> logging.Logger:
    """
    Get an existing logger by name

    Args:
        name: Logger name (default: "ingestion")

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
