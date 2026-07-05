import asyncio
import sys

from backend.core.config import config_manager
from backend.core.logger import app_logger
from backend.database.sqlite import db_manager, Base
from backend.services.settings import settings_service
from backend.core.events import event_bus
from backend.core.di import di_container
from backend.core.scheduler import task_scheduler
from backend.core.permissions import permission_manager, PermissionType
from backend.core.health import health_monitor

async def test_all():
    print("Verifying Core Infrastructure...")
    
    # 1. Config
    print("1. Configuration")
    config = config_manager.get_config()
    assert config is not None
    
    # 2. Logging
    print("2. Logging")
    app_logger.info("Test log from core verification.")
    
    # 3. SQLite
    print("3. SQLite")
    db_manager.initialize_database()
    print("Database initialized.")
    
    # 4. Settings
    print("4. Settings")
    assert settings_service.get("theme") == "dark"
    
    # 5. Event Bus
    print("5. Event Bus")
    event_handled = False
    async def handler(event):
        nonlocal event_handled
        event_handled = True
    event_bus.subscribe("test_topic", handler)
    await event_bus.publish("test_topic", payload="test_payload")
    # allow tasks to run
    await asyncio.sleep(0.1)
    assert event_handled
    
    # 6. Dependency Injection
    print("6. DI")
    class TestService:
        pass
    di_container.register_singleton(TestService, TestService())
    assert isinstance(di_container.resolve(TestService), TestService)
    
    # 7. Scheduler
    print("7. Scheduler")
    task_scheduler.start()
    task_scheduler.stop()
    
    # 8. Permissions
    print("8. Permissions")
    assert permission_manager.is_dangerous_action("rm -rf /", "/")
    
    # 9. Health Monitor
    print("9. Health Monitor")
    report = health_monitor.get_full_health_report()
    assert report["database_ok"]
    assert report["configuration_ok"]
    assert report["status"] == "healthy"
    
    print("ALL CORE SYSTEMS VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_all())
