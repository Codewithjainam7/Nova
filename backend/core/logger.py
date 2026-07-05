import sys
import os
from loguru import logger
from typing import Any, Dict

class LoggerManager:
    """
    Manages logging configuration across the application.
    Supports console, file, error, performance, and debug logging.
    Structured JSON logs can be output for production.
    """
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.setup()

    def setup(self):
        # Remove default handler
        logger.remove()

        # Console logger
        logger.add(
            sys.stdout,
            level="DEBUG",
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )

        # File Logger (general)
        logger.add(
            os.path.join(self.log_dir, "app.log"),
            rotation="10 MB",
            retention="7 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
        )

        # Error Logger
        logger.add(
            os.path.join(self.log_dir, "error.log"),
            rotation="10 MB",
            retention="14 days",
            level="ERROR",
            backtrace=True,
            diagnose=True,
        )

        # Structured JSON Logs for performance/analytics
        logger.add(
            os.path.join(self.log_dir, "structured.json"),
            rotation="10 MB",
            retention="7 days",
            level="INFO",
            serialize=True
        )

    @staticmethod
    def get_logger():
        return logger

    @staticmethod
    def log_performance(action: str, duration_ms: float, metadata: Dict[str, Any] = None):
        """Helper for performance logging"""
        logger.bind(performance=True, action=action, duration_ms=duration_ms, metadata=metadata).info(f"Performance: {action} took {duration_ms}ms")

# Initialize a default manager
logger_manager = LoggerManager()
app_logger = logger_manager.get_logger()
