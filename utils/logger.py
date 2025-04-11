"""
Logger configuration module.

Provides a flexible, type-annotated logging configuration system
that supports multiple outputs and environment-specific settings.
"""

import os
import logging
import logging.config
from typing import Dict, Any, Optional, Union, List
from enum import Enum
from dataclasses import dataclass, field

class LogLevel(Enum):
    """Standard logging levels with proper typing."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

@dataclass
class LogFormat:
    """Predefined log formats for different use cases."""
    STANDARD: str = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    DETAILED: str = '%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s'
    MINIMAL: str = '[%(levelname)s] %(message)s'
    JSON: str = '{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}'

@dataclass
class LoggerConfig:
    """Configuration options for the logger."""
    level: LogLevel = LogLevel.INFO
    format: str = LogFormat.STANDARD
    log_to_console: bool = True
    log_to_file: bool = False
    log_file_path: Optional[str] = None
    max_file_size_mb: int = 10
    backup_count: int = 3
    propagate: bool = True
    additional_handlers: List[Dict[str, Any]] = field(default_factory=list)

class LoggerConfigurator:
    """
    Configures the logging for the application with flexible options.
    
    This class provides a customizable logging configuration with 
    support for multiple outputs, formats, and environment-specific settings.
    """
    
    def __init__(self, config: Optional[LoggerConfig] = None):
        """
        Initialize the logger configurator with optional custom configuration.
        
        Args:
            config: Optional custom logger configuration. If None, default settings are used.
        """
        self.config = config or self._get_environment_config()
        self.logger_config = self._build_config()
        logging.config.dictConfig(self.logger_config)
        self.logger = logging.getLogger("shortsgen")

    def _get_environment_config(self) -> LoggerConfig:
        """
        Create configuration based on environment variables.
        
        Returns:
            LoggerConfig instance with environment-specific settings
        """
        # Determine log level from environment or use INFO as default
        env_level = os.getenv("LOG_LEVEL", "INFO").upper()
        try:
            level = LogLevel[env_level]
        except KeyError:
            level = LogLevel.INFO
        
        # Check if file logging is enabled
        log_to_file = os.getenv("LOG_TO_FILE", "").lower() in ("true", "1", "yes")
        log_file_path = os.getenv("LOG_FILE_PATH")
        
        return LoggerConfig(
            level=level,
            log_to_file=log_to_file,
            log_file_path=log_file_path
        )

    def _build_config(self) -> Dict[str, Any]:
        """
        Build the logging configuration dictionary based on the settings.
        
        Returns:
            Complete logging configuration dictionary compatible with logging.config.dictConfig
        """
        handlers = {}
        handler_names = []

        # Configure console handler if enabled
        if self.config.log_to_console:
            handlers["console"] = {
                "level": self.config.level.value,
                "formatter": "standard",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            }
            handler_names.append("console")
        
        # Configure file handler if enabled
        if self.config.log_to_file and self.config.log_file_path:
            handlers["file"] = {
                "level": self.config.level.value,
                "formatter": "standard",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": self.config.log_file_path,
                "maxBytes": self.config.max_file_size_mb * 1024 * 1024,
                "backupCount": self.config.backup_count,
            }
            handler_names.append("file")
        
        # Add any additional handlers
        for idx, handler in enumerate(self.config.additional_handlers):
            name = f"custom_{idx}"
            handlers[name] = handler
            handler_names.append(name)
        
        # Default to at least console handler if nothing else is configured
        if not handler_names:
            handlers["console"] = {
                "level": LogLevel.INFO.value,
                "formatter": "standard",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            }
            handler_names.append("console")
        
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': self.config.format
                },
            },
            'handlers': handlers,
            'loggers': {
                '': {  # root logger
                    'handlers': handler_names,
                    'level': self.config.level.value,
                    'propagate': self.config.propagate
                },
                'shortsgen': {  # application logger
                    'level': self.config.level.value,
                    'propagate': self.config.propagate
                },
                '__main__': {  # if __name__ == '__main__'
                    'level': LogLevel.DEBUG.value,
                    'propagate': True
                },
            }
        }

    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """
        Returns a configured logger instance.
        
        Args:
            name: Optional name for the logger. If None, returns the default application logger.
        
        Returns:
            Configured logger instance
        """
        if name:
            return logging.getLogger(name)
        return self.logger

    def update_level(self, level: Union[LogLevel, str]) -> None:
        """
        Dynamically update the logging level.
        
        Args:
            level: New logging level (either LogLevel enum or string name)
        """
        if isinstance(level, str):
            try:
                level = LogLevel[level.upper()]
            except KeyError:
                raise ValueError(f"Invalid log level: {level}")
        
        # Update root logger and all handlers
        root = logging.getLogger()
        root.setLevel(level.value)
        
        for handler in root.handlers:
            handler.setLevel(level.value)
        
        self.logger.info(f"Logging level updated to {level.name}")
