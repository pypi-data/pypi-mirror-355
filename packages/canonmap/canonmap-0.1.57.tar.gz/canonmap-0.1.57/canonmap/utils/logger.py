import logging
import sys
from typing import Optional

class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG':    '\033[94m🐛 DEBUG\033[0m',
        'INFO':     '\033[92mℹ️  INFO\033[0m',
        'WARNING':  '\033[93m⚠️  WARNING\033[0m',
        'ERROR':    '\033[91m❌ ERROR\033[0m',
        'CRITICAL': '\033[95m🔥 CRITICAL\033[0m'
    }

    def format(self, record):
        levelname = self.COLORS.get(record.levelname, record.levelname)
        message = super().format(record)
        return f"{levelname} | {message}"

# Global logger instance
_logger: Optional[logging.Logger] = None

def get_logger() -> logging.Logger:
    """
    Get the global logger instance. If it hasn't been initialized yet,
    it will be created with default settings.
    """
    global _logger
    if _logger is None:
        _logger = logging.getLogger("canonmap")
        _logger.setLevel(logging.DEBUG)
        
        if not _logger.handlers:
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            formatter = ColoredFormatter(
                '%(asctime)s | %(name)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            ch.setFormatter(formatter)
            _logger.addHandler(ch)
    
    return _logger

def set_logger(logger: Optional[logging.Logger] = None) -> logging.Logger:
    """
    Set the global logger instance. If no logger is provided,
    a new one will be created with default settings.
    """
    global _logger
    if logger is not None:
        _logger = logger
    return get_logger() 