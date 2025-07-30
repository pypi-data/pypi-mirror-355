#!/usr/bin/env python3
"""
Logging utilities for consistent logging across CLI scripts.
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console


class LoggingUtils:
    """Utilities for setting up consistent logging."""
    
    @staticmethod
    def setup_logging(
        name: str,
        level: Optional[str] = None,
        log_file: Optional[Path] = None,
        console: Optional[Console] = None
    ) -> logging.Logger:
        """
        Set up logging with Rich handler.
        
        Args:
            name: Logger name
            level: Log level (defaults to LOG_LEVEL env var or INFO)
            log_file: Optional file to log to
            console: Rich console to use (creates new if not provided)
            
        Returns:
            Configured logger
        """
        import os
        
        # Determine log level
        if level is None:
            level = os.environ.get("LOG_LEVEL", "INFO")
        
        # Convert to uppercase and validate
        level = level.upper()
        if level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            level = "INFO"
        
        # Create console if not provided
        if console is None:
            console = Console()
        
        # Configure handlers
        handlers = []
        
        # Rich console handler
        handlers.append(RichHandler(
            console=console,
            rich_tracebacks=True,
            show_time=True,
            show_path=False
        ))
        
        # File handler if requested
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            )
            handlers.append(file_handler)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, level),
            format="%(message)s",
            datefmt="[%X]",
            handlers=handlers
        )
        
        # Get logger
        logger = logging.getLogger(name)
        
        # Set level explicitly
        logger.setLevel(getattr(logging, level))
        
        return logger
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """
        Get a logger with the given name.
        
        Args:
            name: Logger name
            
        Returns:
            Logger instance
        """
        return logging.getLogger(name)
    
    @staticmethod
    def set_log_level(level: str) -> None:
        """
        Set log level for all loggers.
        
        Args:
            level: Log level to set
        """
        level = level.upper()
        if level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            logging.getLogger().setLevel(getattr(logging, level))
            
            # Update all existing loggers
            for logger_name in logging.Logger.manager.loggerDict:
                logging.getLogger(logger_name).setLevel(getattr(logging, level))
    
    @staticmethod
    def enable_debug_logging() -> None:
        """Enable debug logging for all loggers."""
        LoggingUtils.set_log_level("DEBUG")
    
    @staticmethod
    def disable_verbose_libraries() -> None:
        """Disable verbose logging from common libraries."""
        # Quiet down noisy libraries
        for lib in ["urllib3", "botocore", "boto3", "requests"]:
            logging.getLogger(lib).setLevel(logging.WARNING)
    
    @staticmethod
    def format_log_message(
        level: str,
        message: str,
        context: Optional[dict] = None
    ) -> str:
        """
        Format a log message with optional context.
        
        Args:
            level: Log level
            message: Log message
            context: Optional context dictionary
            
        Returns:
            Formatted message
        """
        if context:
            context_str = " ".join(f"{k}={v}" for k, v in context.items())
            return f"[{level}] {message} | {context_str}"
        else:
            return f"[{level}] {message}"