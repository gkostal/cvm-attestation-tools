# memory_logger.py
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import logging
import io
from typing import List


class MemoryLogHandler(logging.Handler):
    """Custom logging handler that stores log messages in memory."""
    
    def __init__(self):
        super().__init__()
        self.log_messages = []
        
    def emit(self, record):
        """Store the formatted log message in memory."""
        log_entry = self.format(record)
        self.log_messages.append(log_entry)
    
    def get_logs(self) -> List[str]:
        """Return all collected log messages."""
        return self.log_messages.copy()
    
    def clear_logs(self):
        """Clear all stored log messages."""
        self.log_messages.clear()


class MemoryLogger:
    """Logger implementation that collects messages in memory for API responses."""
    
    def __init__(self, name: str = "attestation_api"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Create memory handler
        self.memory_handler = MemoryLogHandler()
        formatter = logging.Formatter('%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
        self.memory_handler.setFormatter(formatter)
        
        # Clear existing handlers and add our memory handler
        self.logger.handlers.clear()
        self.logger.addHandler(self.memory_handler)
        
    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)
        
    def error(self, message: str):
        """Log error message."""
        self.logger.error(message)
        
    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)
        
    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)
        
    def get_logs(self) -> List[str]:
        """Get all collected log messages."""
        return self.memory_handler.get_logs()
        
    def clear_logs(self):
        """Clear all stored log messages."""
        self.memory_handler.clear_logs()