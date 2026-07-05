import asyncio
from typing import Dict, List
from backend.kernel.schema import KernelRequest, KernelResponse, KernelState, KernelConfiguration, KernelMetrics
from backend.kernel.session import KernelSession
from backend.kernel.events import KernelEventBus, KernelEventType
from backend.kernel.state import KernelStateManager
from backend.kernel.pipeline import KernelPipeline
from backend.core.logger import app_logger

class KernelLogger:
    @staticmethod
    def log_lifecycle(event: str):
        app_logger.info(f"[NOVA KERNEL] {event}")

class NovaKernel:
    """
    The central orchestration Kernel for NOVA.
    No subsystem orchestrates another. Everything flows through here.
    """
    def __init__(self, config: KernelConfiguration = KernelConfiguration()):
        self.config = config
        self.state_manager = KernelStateManager()
        self.event_bus = KernelEventBus()
        self.pipeline = KernelPipeline(self.event_bus)
        self.metrics = KernelMetrics()
        
        self.active_sessions: Dict[str, KernelSession] = {}
        self._setup_internal_events()

    def _setup_internal_events(self):
        self.event_bus.subscribe(KernelEventType.ERROR, self._handle_error)

    async def _handle_error(self, payload: str):
        KernelLogger.log_lifecycle(f"Caught Pipeline Error: {payload}")

    async def startup(self):
        """Boot sequence for the Kernel."""
        self.state_manager.transition_to(KernelState.INITIALIZING)
        KernelLogger.log_lifecycle("Kernel initializing subsystems...")
        # Simulate loading subsystems
        await asyncio.sleep(0.1)
        self.state_manager.transition_to(KernelState.IDLE)
        await self.event_bus.publish(KernelEventType.KERNEL_STARTED)
        KernelLogger.log_lifecycle("Kernel ready.")

    async def shutdown(self):
        """Safe shutdown sequence."""
        self.state_manager.transition_to(KernelState.SHUTDOWN)
        KernelLogger.log_lifecycle("Kernel shutting down...")
        
        # Cancel all active sessions
        for session in self.active_sessions.values():
            session.cancel()
            
        self.active_sessions.clear()
        KernelLogger.log_lifecycle("Kernel shutdown complete.")

    async def dispatch(self, request: KernelRequest) -> KernelResponse:
        """Main entrypoint for User requests."""
        if self.state_manager.current_state not in [KernelState.IDLE, KernelState.EXECUTING]:
            return KernelResponse(
                request_id=request.request_id,
                session_id="",
                status=KernelState.ERROR,
                content="",
                error="Kernel is not ready to accept requests."
            )
            
        if len(self.active_sessions) >= self.config.max_concurrent_sessions:
             return KernelResponse(
                request_id=request.request_id,
                session_id="",
                status=KernelState.ERROR,
                content="",
                error="Max concurrent sessions reached."
            )

        self.metrics.total_requests += 1
        
        # 1. Create Session
        session = KernelSession()
        self.active_sessions[session.session_id] = session
        self.metrics.active_sessions = len(self.active_sessions)
        
        await self.event_bus.publish(KernelEventType.REQUEST_RECEIVED, request)
        
        # 2. Execute Pipeline
        try:
            # We timeout the pipeline if it hangs
            timeout = request.timeout or self.config.timeout_seconds
            response = await asyncio.wait_for(
                self.pipeline.execute(session, request),
                timeout=timeout
            )
            
            if response.status == KernelState.ERROR:
                self.metrics.failed_requests += 1
            else:
                self.metrics.successful_requests += 1
                
            return response
            
        except asyncio.TimeoutError:
            self.metrics.failed_requests += 1
            session.update_state(KernelState.ERROR)
            return KernelResponse(
                request_id=request.request_id,
                session_id=session.session_id,
                status=KernelState.ERROR,
                content="",
                error="Kernel Pipeline Timeout Exceeded."
            )
        finally:
            # 3. Cleanup Session
            if session.session_id in self.active_sessions:
                del self.active_sessions[session.session_id]
            self.metrics.active_sessions = len(self.active_sessions)
            await self.event_bus.publish(KernelEventType.SESSION_CLOSED, session)
