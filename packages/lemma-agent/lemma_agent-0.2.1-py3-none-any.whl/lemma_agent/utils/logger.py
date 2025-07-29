"""
Logging utilities for AgentDebugger SDK.

Provides structured logging with multiple output formats and integration
with existing logging systems.
"""

import logging
import json
import sys
from typing import Any, Dict, Optional, Union
from datetime import datetime, timezone
from pathlib import Path
import os


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels for terminal output."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green  
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        if hasattr(record, 'levelname') and record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}"
                f"{self.COLORS['RESET']}"
            )
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'trace_id'):
            log_entry['trace_id'] = record.trace_id
        if hasattr(record, 'event_type'):
            log_entry['event_type'] = record.event_type
        if hasattr(record, 'event_data'):
            log_entry['event_data'] = record.event_data
        if hasattr(record, 'context'):
            log_entry['context'] = record.context
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        return json.dumps(log_entry, default=str)


class Logger:
    """
    Main logger class for AgentDebugger SDK with structured logging capabilities.
    """
    
    _instance = None
    _logger = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def setup_logger(
        cls,
        log_level: str = "INFO",
        output_format: str = "json",
        log_to_file: bool = True,
        log_directory: Optional[Union[str, Path]] = None,
        logger_name: str = "agentdebugger"
    ) -> 'Logger':
        """
        Setup and configure the logger with specified options.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            output_format: Output format ('json', 'text', 'colored')
            log_to_file: Whether to log to file in addition to console
            log_directory: Directory for log files (default: ~/.agentdebugger/logs)
            logger_name: Name for the logger instance
            
        Returns:
            Configured Logger instance
        """
        instance = cls()
        
        # Create logger
        instance._logger = logging.getLogger(logger_name)
        instance._logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear any existing handlers
        instance._logger.handlers.clear()
        
        # Setup console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        
        # Choose formatter based on output format
        if output_format.lower() == "json":
            formatter = JSONFormatter()
        elif output_format.lower() == "colored":
            formatter = ColoredFormatter(
                '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
                datefmt='%H:%M:%S'
            )
        else:  # text format
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        console_handler.setFormatter(formatter)
        instance._logger.addHandler(console_handler)
        
        # Setup file handler if requested
        if log_to_file:
            if log_directory is None:
                log_directory = Path.home() / ".agentdebugger" / "logs"
            else:
                log_directory = Path(log_directory)
            
            # Create log directory if it doesn't exist
            log_directory.mkdir(parents=True, exist_ok=True)
            
            # Create log file with timestamp
            log_file = log_directory / f"agentdebugger_{datetime.now().strftime('%Y%m%d')}.log"
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(getattr(logging, log_level.upper()))
            
            # Always use JSON format for file logs for better parsing
            file_formatter = JSONFormatter()
            file_handler.setFormatter(file_formatter)
            
            instance._logger.addHandler(file_handler)
        
        return instance
    
    def log_debug_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        level: str = "INFO"
    ) -> None:
        """
        Log a structured debug event with event type and data.
        
        Args:
            event_type: Type of event (e.g., 'function_start', 'trace_completed')
            data: Event-specific data
            context: Additional context information
            level: Log level for this event
        """
        if not self._logger:
            # Fallback to basic logging if logger not setup
            print(f"[{level}] {event_type}: {data}")
            return
        
        message = f"Debug event: {event_type}"
        
        # Create log record with extra fields
        log_level = getattr(logging, level.upper())
        record = self._logger.makeRecord(
            self._logger.name,
            log_level,
            __file__,
            0,
            message,
            (),
            None
        )
        
        # Add custom fields
        record.event_type = event_type
        record.event_data = data
        if context:
            record.context = context
        
        self._logger.handle(record)
    
    def log_trace_event(
        self,
        trace_id: str,
        event: str,
        data: Dict[str, Any],
        level: str = "INFO"
    ) -> None:
        """
        Log an event related to a specific trace.
        
        Args:
            trace_id: Unique trace identifier
            event: Event description
            data: Event data
            level: Log level
        """
        if not self._logger:
            print(f"[{level}] Trace {trace_id}: {event} - {data}")
            return
        
        message = f"Trace event: {event}"
        
        log_level = getattr(logging, level.upper())
        record = self._logger.makeRecord(
            self._logger.name,
            log_level,
            __file__,
            0,
            message,
            (),
            None
        )
        
        # Add trace-specific fields
        record.trace_id = trace_id
        record.event_type = "trace_event"
        record.event_data = {
            "event": event,
            **data
        }
        
        self._logger.handle(record)
    
    def log_performance_metrics(
        self,
        metrics: Dict[str, Any],
        trace_id: Optional[str] = None
    ) -> None:
        """
        Log performance metrics for analysis.
        
        Args:
            metrics: Performance metrics dictionary
            trace_id: Associated trace ID if available
        """
        self.log_debug_event(
            "performance_metrics",
            metrics,
            {"trace_id": trace_id} if trace_id else None,
            level="INFO"
        )
    
    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ) -> None:
        """
        Log an error with full context and trace information.
        
        Args:
            error: Exception that occurred
            context: Additional context about the error
            trace_id: Associated trace ID if available
        """
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "trace_id": trace_id
        }
        
        if context:
            error_data["context"] = context
        
        if not self._logger:
            print(f"[ERROR] {error_data}")
            return
        
        # Log with exception info for traceback
        try:
            raise error
        except Exception:
            self._logger.exception("Agent execution error", extra={
                "event_type": "execution_error",
                "event_data": error_data,
                "trace_id": trace_id
            })
    
    def log_config_event(
        self,
        event: str,
        config_data: Dict[str, Any],
        level: str = "INFO"
    ) -> None:
        """
        Log configuration-related events.
        
        Args:
            event: Configuration event description
            config_data: Configuration data (sensitive data will be redacted)
            level: Log level
        """
        # Redact sensitive configuration data
        safe_config = self._redact_sensitive_data(config_data)
        
        self.log_debug_event(
            "config_event",
            {
                "event": event,
                "config": safe_config
            },
            level=level
        )
    
    def debug(self, message: str, **kwargs) -> None:
        """Standard debug logging."""
        if self._logger:
            self._logger.debug(message, extra=kwargs)
        else:
            print(f"[DEBUG] {message}")
    
    def info(self, message: str, **kwargs) -> None:
        """Standard info logging."""
        if self._logger:
            self._logger.info(message, extra=kwargs)
        else:
            print(f"[INFO] {message}")
    
    def warning(self, message: str, **kwargs) -> None:
        """Standard warning logging."""
        if self._logger:
            self._logger.warning(message, extra=kwargs)
        else:
            print(f"[WARNING] {message}")
    
    def error(self, message: str, **kwargs) -> None:
        """Standard error logging."""
        if self._logger:
            self._logger.error(message, extra=kwargs)
        else:
            print(f"[ERROR] {message}")
    
    def critical(self, message: str, **kwargs) -> None:
        """Standard critical logging."""
        if self._logger:
            self._logger.critical(message, extra=kwargs)
        else:
            print(f"[CRITICAL] {message}")
    
    def _redact_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact sensitive information from data before logging.
        
        Args:
            data: Dictionary that may contain sensitive data
            
        Returns:
            Dictionary with sensitive values redacted
        """
        sensitive_keys = {
            "api_key", "secret", "password", "token", "key", "auth",
            "credentials", "private_key", "access_token", "refresh_token"
        }
        
        def redact_value(key: str, value: Any) -> Any:
            if isinstance(key, str) and any(sensitive in key.lower() for sensitive in sensitive_keys):
                if isinstance(value, str) and len(value) > 4:
                    return f"***{value[-4:]}"
                else:
                    return "***"
            elif isinstance(value, dict):
                return {k: redact_value(k, v) for k, v in value.items()}
            elif isinstance(value, list):
                return [redact_value("", item) for item in value]
            else:
                return value
        
        return {key: redact_value(key, value) for key, value in data.items()}
    
    def get_logger(self) -> Optional[logging.Logger]:
        """Get the underlying Python logger instance."""
        return self._logger
    
    def set_level(self, level: str) -> None:
        """Change the logging level."""
        if self._logger:
            self._logger.setLevel(getattr(logging, level.upper()))
            for handler in self._logger.handlers:
                handler.setLevel(getattr(logging, level.upper()))