"""
Structured Logging with Crash Detection

Provides comprehensive logging infrastructure with structured JSON logs,
crash detection, and traceback capture for the HAAI system.
"""

import logging
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class StructuredLogHandler(logging.Handler):
    """Custom handler that outputs structured JSON logs."""
    
    def __init__(self, log_file: str = "haai_logs.json"):
        super().__init__()
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        # Ensure file exists
        self.log_file.touch(exist_ok=True)
    
    def emit(self, record: logging.LogRecord) -> None:
        """Emit a structured log record."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self._format_exception(record.exc_info)
        
        # Add extra attributes
        if hasattr(record, 'crash_id'):
            log_data["crash_id"] = record.crash_id
        
        if hasattr(record, 'context'):
            log_data["context"] = record.context
        
        # Write to file
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_data) + '\n')
    
    def _format_exception(self, exc_info) -> str:
        """Format exception info as string."""
        import traceback
        return ''.join(traceback.format_exception(*exc_info))


class CrashDetectionLogger:
    """
    Structured logger with crash detection capabilities.
    
    Provides:
    - Structured JSON logging
    - Crash ID generation
    - Traceback capture
    - Context tracking
    """
    
    def __init__(self, name: str, log_file: str = "crash_detection.log", 
                 json_log_file: str = "haai_logs.json"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        self.log_file = Path(log_file)
        self.json_log_file = Path(json_log_file)
        
        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Formatters
        self._setup_formatters()
        
        # Add handlers
        self._setup_handlers()
        
        # Track crash IDs
        self.crash_history: list = []
    
    def _setup_formatters(self) -> None:
        """Setup log formatters."""
        # Standard formatter for console
        self.console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # JSON formatter for structured logs
        self.json_formatter = logging.Formatter('%(message)s')
    
    def _setup_handlers(self) -> None:
        """Setup log handlers."""
        # File handler for crash logs
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(self.console_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(self.console_formatter)
        self.logger.addHandler(console_handler)
        
        # JSON structured log handler
        json_handler = StructuredLogHandler(self.json_log_file)
        json_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(json_handler)
    
    def log_crash(self, error: Exception, context: Dict[str, Any] = None) -> str:
        """
        Log a crash event and return crash ID.
        
        Args:
            error: The exception that occurred
            context: Additional context information
            
        Returns:
            Unique crash ID string
        """
        import traceback
        
        crash_id = f"CRASH-{datetime.now().strftime('%Y%m%d%H%M%S')}-{abs(hash(str(error)) % 100000):05d}"
        
        crash_data = {
            "crash_id": crash_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "timestamp": datetime.now().isoformat(),
            "stack_trace": ''.join(traceback.format_exception(
                type(error), error, error.__traceback__
            ))
        }
        
        self.crash_history.append(crash_data)
        
        # Log with extra context
        extra = {'crash_id': crash_id, 'context': crash_data}
        self.logger.critical(
            f"CRASH DETECTED: {crash_id} | {type(error).__name__}: {str(error)}",
            extra=extra
        )
        
        return crash_id
    
    def log_error_with_context(self, message: str, context: Dict[str, Any] = None) -> None:
        """
        Log an error with additional context.
        
        Args:
            message: Error message
            context: Additional context dictionary
        """
        extra = {'context': context or {}}
        self.logger.error(message, extra=extra)
    
    def log_warning_with_context(self, message: str, context: Dict[str, Any] = None) -> None:
        """
        Log a warning with additional context.
        
        Args:
            message: Warning message
            context: Additional context dictionary
        """
        extra = {'context': context or {}}
        self.logger.warning(message, extra=extra)
    
    def log_info_with_context(self, message: str, context: Dict[str, Any] = None) -> None:
        """
        Log an info message with additional context.
        
        Args:
            message: Info message
            context: Additional context dictionary
        """
        extra = {'context': context or {}}
        self.logger.info(message, extra=extra)
    
    def get_crash_history(self, limit: int = 100) -> list:
        """
        Get recent crash history.
        
        Args:
            limit: Maximum number of crashes to return
            
        Returns:
            List of crash data dictionaries
        """
        return self.crash_history[-limit:]
    
    def clear_crash_history(self) -> None:
        """Clear the in-memory crash history."""
        self.crash_history.clear()


def get_logger(name: str, log_file: str = None) -> CrashDetectionLogger:
    """
    Factory function to get a structured logger.
    
    Args:
        name: Logger name (usually __name__)
        log_file: Optional custom log file path
        
    Returns:
        Configured CrashDetectionLogger instance
    """
    if log_file is None:
        log_file = f"logs/{name.replace('.', '_')}.log"
    
    return CrashDetectionLogger(name, log_file=log_file)


# Singleton for application-wide logging
_app_logger: Optional[CrashDetectionLogger] = None


def get_app_logger() -> CrashDetectionLogger:
    """Get the application-wide logger singleton."""
    global _app_logger
    if _app_logger is None:
        _app_logger = CrashDetectionLogger("HAAI", log_file="logs/haai.log")
    return _app_logger
