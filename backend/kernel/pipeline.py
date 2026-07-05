from backend.kernel.schema import KernelRequest, KernelResponse, KernelState
from backend.kernel.session import KernelSession
from backend.kernel.events import KernelEventBus, KernelEventType
from backend.core.logger import app_logger

class KernelPipeline:
    """
    Orchestrates the actual synchronous or asynchronous flow between subsystems.
    This simulates the sequence: Planner -> Execution -> Verification -> Context -> Provider.
    """
    def __init__(self, event_bus: KernelEventBus):
        self.event_bus = event_bus

    async def execute(self, session: KernelSession, request: KernelRequest) -> KernelResponse:
        try:
            # 1. Planner
            session.update_state(KernelState.PLANNING)
            await self.event_bus.publish(KernelEventType.PLANNING_STARTED, session)
            # mock planner call...
            
            # 2. Execution
            session.update_state(KernelState.EXECUTING)
            await self.event_bus.publish(KernelEventType.EXECUTION_STARTED, session)
            # mock execution call (which talks to router, resolver, registry)...
            
            # 3. Verification
            session.update_state(KernelState.WAITING)
            await self.event_bus.publish(KernelEventType.VERIFICATION_STARTED, session)
            # mock verification call...
            
            # 4. Context
            await self.event_bus.publish(KernelEventType.CONTEXT_BUILT, session)
            # mock context call...
            
            # 5. AI Provider
            session.update_state(KernelState.STREAMING) # Or just executing
            await self.event_bus.publish(KernelEventType.PROVIDER_INVOKED, session)
            # mock AI Provider call...
            
            session.update_state(KernelState.COMPLETED)
            await self.event_bus.publish(KernelEventType.RESPONSE_COMPLETED, session)
            
            return KernelResponse(
                request_id=request.request_id,
                session_id=session.session_id,
                status=KernelState.COMPLETED,
                content=f"Successfully processed request: {request.user_input}"
            )
            
        except Exception as e:
            app_logger.error(f"Pipeline error for session {session.session_id}: {str(e)}")
            session.update_state(KernelState.ERROR)
            await self.event_bus.publish(KernelEventType.ERROR, str(e))
            return KernelResponse(
                request_id=request.request_id,
                session_id=session.session_id,
                status=KernelState.ERROR,
                content="Internal Engine Error",
                error=str(e)
            )
