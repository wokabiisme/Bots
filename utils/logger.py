"""Logging configuration and utilities."""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional


def setup_logger(
    name: str = "trading_bot",
    level: str = "INFO",
    log_dir: str = "logs",
    file_rotation: str = "500 MB",
    retention: str = "30 days"
) -> None:
    """Setup logging configuration.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        file_rotation: When to rotate log file (size or time)
        retention: How long to keep log files
    """
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Remove default handler
    logger.remove()
    
    # Console handler
    logger.add(
        sys.stdout,
        format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True
    )
    
    # File handler - all logs
    logger.add(
        log_path / f"{name}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=level,
        rotation=file_rotation,
        retention=retention,
        compression="zip"
    )
    
    # File handler - errors only
    logger.add(
        log_path / f"{name}_errors.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation=file_rotation,
        retention=retention,
        compression="zip"
    )


class StructuredLogger:
    """Structured logging wrapper."""
    
    def __init__(self, name: str):
        """Initialize logger.
        
        Args:
            name: Logger name
        """
        self.logger = logger.bind(name=name)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with structured data."""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message with structured data."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with structured data."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message with structured data."""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message with structured data."""
        self.logger.critical(message, **kwargs)
    
    def log_trade(self, trade_data: dict) -> None:
        """Log trade execution.
        
        Args:
            trade_data: Trade information dictionary
        """
        self.logger.info("Trade executed", **trade_data)
    
    def log_error(self, error: Exception, context: Optional[dict] = None) -> None:
        """Log exception with context.
        
        Args:
            error: Exception object
            context: Additional context dictionary
        """
        context = context or {}
        self.logger.exception(f"Exception occurred: {str(error)}", **context)
