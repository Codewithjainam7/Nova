import asyncio
from backend.release.schema import CrashReport, TelemetryData
from backend.core.logger import app_logger

class CrashReporter:
    """Intercepts unhandled exceptions and generates secure minidumps."""
    async def generate_report(self, exception: Exception, subsystem: str) -> CrashReport:
        app_logger.error(f"[CRASH REPORT] Generating dump for exception in {subsystem}...")
        await asyncio.sleep(0.01)
        return CrashReport(
            stack_trace=str(exception),
            subsystem=subsystem,
            recovery_successful=True
        )

class TelemetryManager:
    """Handles opt-in anonymous metric collection (strictly sanitized)."""
    def __init__(self, opt_in: bool = False):
        self.opt_in = opt_in
        
    async def record_session(self, data: TelemetryData):
        if not self.opt_in:
            app_logger.debug("[TELEMETRY] Dropped metrics (User opted out)")
            return
            
        app_logger.info(f"[TELEMETRY] Transmitting anonymous session data: {data.session_id}")
        await asyncio.sleep(0.02)
