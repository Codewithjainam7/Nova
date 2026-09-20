import logging
import json
import os
from datetime import datetime

# Setup standard logger
logger = logging.getLogger("UIAutomation")
logger.setLevel(logging.DEBUG)

# Ensure logs directory exists
log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
os.makedirs(log_dir, exist_ok=True)

# Add file handler for structured logging
fh = logging.FileHandler(os.path.join(log_dir, "ui_automation.log"))
fh.setLevel(logging.DEBUG)

# Add console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

class UILogger:
    @staticmethod
    def log_action(action, target, result, execution_time_ms, error=None):
        """Structured logging for UI actions."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "target": target,
            "result": "SUCCESS" if result else "FAILED",
            "execution_time_ms": execution_time_ms,
            "error": str(error) if error else None
        }
        logger.info(json.dumps(log_entry))
        
    @staticmethod
    def log_search(target_type, search_params, found):
        """Structured logging for searches."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "SEARCH",
            "target_type": target_type,
            "params": search_params,
            "found": found
        }
        logger.debug(json.dumps(log_entry))
        
    @staticmethod
    def error(msg, exc_info=False):
        logger.error(msg, exc_info=exc_info)
        
    @staticmethod
    def info(msg):
        logger.info(msg)
        
    @staticmethod
    def debug(msg):
        logger.debug(msg)
