import psutil
from typing import Dict, Any
from backend.core.logger import app_logger
from backend.database.sqlite import db_manager
from backend.core.config import config_manager
from sqlalchemy import text

class HealthMonitor:
    """
    Monitors health of Database, Runtime, Config, Services.
    """
    def __init__(self):
        self.status: Dict[str, Any] = {}

    def check_database(self) -> bool:
        try:
            with db_manager.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            app_logger.error(f"Database health check failed: {e}")
            return False

    def check_runtime(self) -> Dict[str, Any]:
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.1)
        return {
            "cpu_percent": cpu,
            "memory_percent": memory.percent,
            "memory_available_mb": memory.available / (1024 * 1024)
        }

    def check_configuration(self) -> bool:
        try:
            config = config_manager.get_config()
            return config is not None
        except Exception:
            return False

    def get_full_health_report(self) -> Dict[str, Any]:
        report = {
            "database_ok": self.check_database(),
            "configuration_ok": self.check_configuration(),
            "runtime": self.check_runtime(),
            "status": "healthy"
        }
        if not report["database_ok"] or not report["configuration_ok"]:
            report["status"] = "unhealthy"
        return report

health_monitor = HealthMonitor()
