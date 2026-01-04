"""
Logging configuration and utilities.
Applies: Structured logging, Multiple handlers, Log rotation
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime


class LoggerConfig:
    """
    Configuration for logger setup.
    
    Design Pattern: Builder Pattern
    """
    
    def __init__(
        self,
        name: str,
        level: str = "INFO",
        log_dir: Optional[Path] = None,
        console_output: bool = True,
        file_output: bool = True,
        json_format: bool = False,
        max_bytes: int = 10485760,  # 10MB
        backup_count: int = 5
    ):
        self.name = name
        self.level = level
        self.log_dir = log_dir or Path("logs")
        self.console_output = console_output
        self.file_output = file_output
        self.json_format = json_format
        self.max_bytes = max_bytes
        self.backup_count = backup_count


class ColoredFormatter(logging.Formatter):
    """
    Colored console formatter.
    
    Adds colors to log levels for better visibility.
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        """Format log record with colors."""
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    """
    
    def format(self, record):
        """Format log record as JSON."""
        import json
        
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        return json.dumps(log_data)


def setup_logger(config: LoggerConfig) -> logging.Logger:
    """
    Set up logger with specified configuration.
    
    Args:
        config: Logger configuration
        
    Returns:
        Configured logger instance
    """
    try:
        # Create logger
        logger = logging.getLogger(config.name)
        logger.setLevel(getattr(logging, config.level.upper()))
        
        # Remove existing handlers
        logger.handlers.clear()
        
        # Console handler
        if config.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, config.level.upper()))
            
            if config.json_format:
                console_formatter = JSONFormatter()
            else:
                console_formatter = ColoredFormatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
            
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        # File handler
        if config.file_output:
            # Ensure log directory exists
            config.log_dir.mkdir(parents=True, exist_ok=True)
            
            # Create log file path
            log_file = config.log_dir / f"{config.name}.log"
            
            # Rotating file handler
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=config.max_bytes,
                backupCount=config.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(getattr(logging, config.level.upper()))
            
            if config.json_format:
                file_formatter = JSONFormatter()
            else:
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - '
                    '%(module)s:%(funcName)s:%(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
            
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        logger.info(f"Logger '{config.name}' initialized successfully")
        return logger
        
    except Exception as e:
        print(f"Failed to setup logger: {e}")
        # Return basic logger as fallback
        return logging.getLogger(config.name)


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Get or create logger with default configuration.
    
    Args:
        name: Logger name
        level: Log level
        
    Returns:
        Logger instance
    """
    config = LoggerConfig(
        name=name,
        level=level,
        console_output=True,
        file_output=True,
        json_format=False
    )
    
    return setup_logger(config)


def configure_root_logger(level: str = "INFO") -> None:
    """
    Configure root logger for the application.
    
    Args:
        level: Log level
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
