"""
Centralized logging utility for Arbor AI Studio.

This module provides a custom logger that:
- Saves logs to files in the logs/ directory
- Rotates log files automatically (10MB max size, keeps 5 backups)
- Filters logs to save only important ones (INFO and above)
- Provides different log levels for different components
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


class LoggerSetup:
    """Centralized logger configuration."""

    _initialized = False
    _loggers = {}

    @staticmethod
    def initialize(log_level: str = "INFO", enable_console: bool = True):
        """
        Initialize the logging system.

        Args:
            log_level: Default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            enable_console: Whether to enable console output
        """
        if LoggerSetup._initialized:
            return

        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # Convert string level to logging constant
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)

        # Clear existing handlers
        root_logger.handlers = []

        # Create formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # File handler for all logs (INFO and above)
        file_handler = RotatingFileHandler(
            logs_dir / "app.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # File handler for error logs only
        error_handler = RotatingFileHandler(
            logs_dir / "errors.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)

        # Console handler (optional, for development)
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(numeric_level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        # Reduce noise from third-party libraries
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

        LoggerSetup._initialized = True

    @staticmethod
    def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
        """
        Get or create a logger instance.

        Args:
            name: Logger name (typically __name__ of the module)
            level: Optional specific log level for this logger

        Returns:
            Configured logger instance
        """
        # Initialize if not already done
        if not LoggerSetup._initialized:
            LoggerSetup.initialize()

        # Return cached logger if exists
        if name in LoggerSetup._loggers:
            logger = LoggerSetup._loggers[name]
            if level:
                logger.setLevel(getattr(logging, level.upper(), logging.INFO))
            return logger

        # Create new logger
        logger = logging.getLogger(name)
        if level:
            logger.setLevel(getattr(logging, level.upper(), logging.INFO))

        LoggerSetup._loggers[name] = logger
        return logger


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Convenience function to get a logger instance.

    Usage:
        from src.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Application started")
        logger.error("Something went wrong", exc_info=True)

    Args:
        name: Logger name (use __name__ for automatic module naming)
        level: Optional log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    return LoggerSetup.get_logger(name, level)


def setup_logging(log_level: str = "INFO", enable_console: bool = True):
    """
    Initialize the logging system.

    This should be called once at application startup.

    Args:
        log_level: Default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_console: Whether to enable console output (useful for development)
    """
    LoggerSetup.initialize(log_level, enable_console)
