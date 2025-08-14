"""Logging configuration for the Weather application."""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from rich.logging import RichHandler
from rich.console import Console

from .config import config


class WeatherLogger:
    """Custom logger for weather application."""
    
    def __init__(self, name: str, log_dir: Optional[str] = None):
        self.name = name
        self.log_dir = Path(log_dir or "logs")
        self.log_dir.mkdir(exist_ok=True)
        self._logger = None
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger with multiple handlers."""
        self._logger = logging.getLogger(self.name)
        self._logger.setLevel(getattr(logging, config.log_level.upper()))
        
        # Prevent adding handlers multiple times
        if self._logger.handlers:
            return
        
        # Create formatters
        file_formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_formatter = logging.Formatter(
            fmt='%(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler with Rich
        console_handler = RichHandler(
            console=Console(),
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
            markup=True
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        
        # File handler for general logs (rotating)
        general_log_file = self.log_dir / "weather.log"
        file_handler = RotatingFileHandler(
            general_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        
        # Error log file (rotating)
        error_log_file = self.log_dir / "weather_errors.log"
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setFormatter(file_formatter)
        error_handler.setLevel(logging.ERROR)
        
        # Daily log file
        daily_log_file = self.log_dir / "weather_daily.log"
        daily_handler = TimedRotatingFileHandler(
            daily_log_file,
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        daily_handler.setFormatter(file_formatter)
        daily_handler.setLevel(logging.DEBUG)
        
        # Add handlers to logger
        self._logger.addHandler(console_handler)
        self._logger.addHandler(file_handler)
        self._logger.addHandler(error_handler)
        self._logger.addHandler(daily_handler)
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance."""
        return self._logger
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._logger.critical(message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception message with traceback."""
        self._logger.exception(message, **kwargs)


# Global logger instances
main_logger = WeatherLogger("weather.main")
api_logger = WeatherLogger("weather.api")
db_logger = WeatherLogger("weather.database")
scheduler_logger = WeatherLogger("weather.scheduler")
notification_logger = WeatherLogger("weather.notifications")


def get_logger(name: str) -> WeatherLogger:
    """Get a logger instance for a specific module."""
    return WeatherLogger(f"weather.{name}")


# Convenience functions for global logging
def log_info(message: str, **kwargs):
    """Log info message to main logger."""
    main_logger.info(message, **kwargs)


def log_error(message: str, **kwargs):
    """Log error message to main logger."""
    main_logger.error(message, **kwargs)


def log_debug(message: str, **kwargs):
    """Log debug message to main logger."""
    main_logger.debug(message, **kwargs)


def log_warning(message: str, **kwargs):
    """Log warning message to main logger."""
    main_logger.warning(message, **kwargs)