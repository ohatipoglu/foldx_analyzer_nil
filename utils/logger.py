"""
Logging utility for FoldX Analyzer.

Provides dual logging functionality:
- Standard Python logging for console/file output
- UI log callback for real-time GUI updates
"""

import logging
from typing import Optional, Callable, List
from datetime import datetime
import threading

from .config import LOG_MAX_LINES


class UILogHandler:
    """
    Thread-safe log handler that buffers messages for UI updates.
    
    This handler stores log messages in a thread-safe list and provides
    methods for the UI to retrieve and display them.
    """
    
    def __init__(self, max_lines: int = LOG_MAX_LINES):
        self.max_lines = max_lines
        self._buffer: List[str] = []
        self._lock = threading.Lock()
        self._callback: Optional[Callable[[str], None]] = None
    
    def set_callback(self, callback: Callable[[str], None]) -> None:
        """Set the callback function to be called when a new log message arrives."""
        self._callback = callback
    
    def add_message(self, message: str) -> None:
        """Add a message to the buffer (thread-safe)."""
        with self._lock:
            self._buffer.append(message)
            # Trim buffer if it exceeds max lines
            if len(self._buffer) > self.max_lines:
                self._buffer = self._buffer[-self.max_lines:]
        
        # Call the callback if set (for real-time UI updates)
        if self._callback:
            try:
                self._callback(message)
            except Exception:
                pass  # Silently ignore callback errors
    
    def get_messages(self) -> List[str]:
        """Get all buffered messages (thread-safe)."""
        with self._lock:
            return self._buffer.copy()
    
    def clear(self) -> None:
        """Clear all buffered messages (thread-safe)."""
        with self._lock:
            self._buffer.clear()


class Logger:
    """
    Centralized logger for FoldX Analyzer.
    
    Provides both standard logging and UI log integration.
    """
    
    def __init__(self, name: str = "FoldXAnalyzer"):
        self._logger = logging.getLogger(name)
        self._logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if not self._logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            self._logger.addHandler(console_handler)
        
        self._ui_handler: Optional[UILogHandler] = None
    
    def set_ui_handler(self, ui_handler: UILogHandler) -> None:
        """Attach a UI log handler."""
        self._ui_handler = ui_handler
    
    def _log_to_ui(self, message: str, level: str = "INFO") -> None:
        """Send a message to the UI log if handler is attached."""
        if self._ui_handler:
            timestamp = datetime.now().strftime('%H:%M:%S')
            formatted_message = f"[{timestamp}] {level}: {message}"
            self._ui_handler.add_message(formatted_message)
    
    def debug(self, message: str) -> None:
        """Log a debug message."""
        self._logger.debug(message)
        self._log_to_ui(message, "DEBUG")
    
    def info(self, message: str) -> None:
        """Log an info message."""
        self._logger.info(message)
        self._log_to_ui(message, "INFO")
    
    def warning(self, message: str) -> None:
        """Log a warning message."""
        self._logger.warning(message)
        self._log_to_ui(message, "WARNING")
    
    def error(self, message: str) -> None:
        """Log an error message."""
        self._logger.error(message)
        self._log_to_ui(message, "ERROR")
    
    def critical(self, message: str) -> None:
        """Log a critical error message."""
        self._logger.critical(message)
        self._log_to_ui(message, "CRITICAL")
    
    def success(self, message: str) -> None:
        """Log a success message (info level with visual distinction)."""
        self._logger.info(f"✓ {message}")
        self._log_to_ui(f"✓ {message}", "SUCCESS")


# Global logger instance
_global_logger: Optional[Logger] = None


def get_logger() -> Logger:
    """Get or create the global logger instance."""
    global _global_logger
    if _global_logger is None:
        _global_logger = Logger()
    return _global_logger


def set_ui_callback(callback: Callable[[str], None]) -> None:
    """Set the UI callback for the global logger."""
    logger = get_logger()
    ui_handler = UILogHandler()
    ui_handler.set_callback(callback)
    logger.set_ui_handler(ui_handler)
    return ui_handler


def log_info(message: str) -> None:
    """Convenience function to log an info message."""
    get_logger().info(message)


def log_error(message: str) -> None:
    """Convenience function to log an error message."""
    get_logger().error(message)


def log_success(message: str) -> None:
    """Convenience function to log a success message."""
    get_logger().success(message)


def log_warning(message: str) -> None:
    """Convenience function to log a warning message."""
    get_logger().warning(message)
