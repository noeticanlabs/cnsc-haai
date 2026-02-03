"""
Global Exception Handler

Catches unhandled exceptions globally, including thread exceptions,
signal handlers, and uncaught exceptions in the main thread.
"""

import sys
import signal
import threading
import traceback
from typing import Callable, Optional, Dict, Any
from datetime import datetime
from functools import wraps

from .logging import CrashDetectionLogger


class GlobalExceptionHandler:
    """
    Catches unhandled exceptions globally.
    
    Features:
    - Main thread uncaught exception handler
    - Background thread exception hook
    - Signal handlers for graceful shutdown
    - Automatic crash logging and ID generation
    """
    
    def __init__(self, logger: CrashDetectionLogger = None, 
                 fail_fast: bool = False):
        """
        Initialize the exception handler.
        
        Args:
            logger: Optional custom logger instance
            fail_fast: If True, re-raise exceptions after logging
        """
        self.logger = logger or CrashDetectionLogger("ExceptionHandler")
        self.fail_fast = fail_fast
        self.original_handlers = {}
        self._original_thread_excepthook = None
        self.is_installed = False
        
        # Track active crashes
        self.active_crashes: Dict[str, Dict[str, Any]] = {}
    
    def install(self) -> None:
        """Install global exception handlers."""
        if self.is_installed:
            self.logger.logger.warning("Exception handler already installed")
            return
        
        # Store original handlers
        self.original_handlers = {
            'excepthook': sys.excepthook,
            'thread_excepthook': getattr(threading, 'excepthook', None)
        }
        
        # Set up thread exception hook (Python 3.8+)
        if hasattr(threading, 'excepthook'):
            self._original_thread_excepthook = threading.excepthook
            threading.excepthook = self._handle_thread_exception
        
        # Set up uncaught exception handler for main thread
        sys.excepthook = self._handle_uncaught_exception
        
        # Set up signal handlers
        self._setup_signal_handlers()
        
        self.is_installed = True
        self.logger.logger.info("Global exception handler installed successfully")
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        signals = ['SIGTERM', 'SIGINT', 'SIGHUP']
        
        for sig_name in signals:
            try:
                sig = getattr(signal, sig_name)
                signal.signal(sig, self._handle_signal)
            except (ValueError, OSError):
                # Signal not available on this platform
                pass
    
    def _handle_uncaught_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions in main thread."""
        crash_data = {
            "source": "main_thread",
            "uncaught": True,
            "thread_name": "MainThread"
        }
        
        crash_id = self.logger.log_crash(exc_value, crash_data)
        
        # Log the traceback
        tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        self.logger.logger.error(f"Traceback:\n{tb_str}")
        
        # Call original handler if exists
        if self.original_handlers.get('excepthook'):
            try:
                self.original_handlers['excepthook'](exc_type, exc_value, exc_traceback)
            except Exception as e:
                self.logger.logger.error(f"Original excepthook failed: {e}")
        
        if self.fail_fast:
            raise exc_value
    
    def _handle_thread_exception(self, args):
        """
        Handle exceptions in background threads.
        
        Args:
            args: Thread exception args with exception, thread, and traceback
        """
        crash_data = {
            "source": "thread",
            "thread_name": getattr(args.thread, 'name', 'Unknown'),
            "thread_id": getattr(args.thread, 'ident', None)
        }
        
        crash_id = self.logger.log_crash(args.exception, crash_data)
        
        # Log the traceback
        if args.traceback:
            tb_str = ''.join(traceback.format_exception(
                type(args.exception), args.exception, args.traceback
            ))
            self.logger.logger.error(f"Thread {args.thread.name} traceback:\n{tb_str}")
    
    def _handle_signal(self, signum, frame):
        """Handle termination signals."""
        sig_name = signal.Signals(signum).name
        self.logger.logger.info(f"Received {sig_name} signal, initiating graceful shutdown...")
        
        # Allow some time for cleanup
        import asyncio
        
        async def shutdown():
            self.logger.logger.info("Performing graceful shutdown...")
            # Trigger shutdown events here if needed
            self.logger.logger.info("Shutdown complete")
            sys.exit(0)
        
        # Run shutdown asynchronously
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(shutdown())
        except Exception as e:
            self.logger.logger.error(f"Shutdown error: {e}")
            sys.exit(1)
    
    def uninstall(self) -> None:
        """Uninstall exception handlers and restore originals."""
        if not self.is_installed:
            return
        
        # Restore original handlers
        if self.original_handlers.get('excepthook'):
            sys.excepthook = self.original_handlers['excepthook']
        
        if self._original_thread_excepthook and hasattr(threading, 'excepthook'):
            threading.excepthook = self._original_thread_excepthook
        
        self.is_installed = False
        self.logger.logger.info("Exception handler uninstalled")


def with_exception_handling(logger: CrashDetectionLogger = None,
                           reraise: bool = False):
    """
    Decorator to wrap functions with exception handling.
    
    Args:
        logger: Optional logger instance
        reraise: If True, re-raise exceptions after logging
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log = logger or CrashDetectionLogger(func.__module__)
                context = {
                    "function": func.__name__,
                    "args_types": [type(a).__name__ for a in args],
                    "kwargs_keys": list(kwargs.keys())
                }
                log.log_crash(e, context)
                if reraise:
                    raise
                return None
        return wrapper
    return decorator


class ExceptionGuard:
    """
    Context manager to guard code blocks with exception handling.
    
    Usage:
        with ExceptionGuard(logger, context={"operation": "data_processing"}):
            # Code that might raise exceptions
            pass
    """
    
    def __init__(self, logger: CrashDetectionLogger = None,
                 context: Dict[str, Any] = None,
                 reraise: bool = False,
                 default_return: Any = None):
        """
        Initialize the exception guard.
        
        Args:
            logger: Logger instance
            context: Additional context for crash logs
            reraise: If True, re-raise exceptions
            default_return: Value to return if exception occurs and not reraised
        """
        self.logger = logger or get_app_logger()
        self.context = context or {}
        self.reraise = reraise
        self.default_return = default_return
        self.crash_id: Optional[str] = None
    
    def __enter__(self) -> 'ExceptionGuard':
        """Enter the context manager."""
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the context manager."""
        if exc_type is not None:
            # Exception occurred
            self.crash_id = self.logger.log_crash(exc_value, self.context)
            
            if self.reraise:
                return False  # Re-raise the exception
            
            # Suppress the exception and return default
            return True
        
        # No exception
        return False


def get_exception_handler() -> GlobalExceptionHandler:
    """Get the global exception handler singleton."""
    return GlobalExceptionHandler(get_app_logger())


# Convenience function for quick imports
def get_logger(name: str) -> CrashDetectionLogger:
    """Get a logger instance."""
    return CrashDetectionLogger(name)
