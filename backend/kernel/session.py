from typing import Dict, Any, Optional
import uuid
from datetime import datetime
from backend.kernel.schema import KernelContext, KernelState

class KernelSession:
    def __init__(self, parent_id: Optional[str] = None):
        self.session_id: str = str(uuid.uuid4())
        self.parent_id: Optional[str] = parent_id
        self.context = KernelContext(session_id=self.session_id)
        self.state: KernelState = KernelState.INITIALIZING
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()
        self.is_cancelled: bool = False

    def update_state(self, new_state: KernelState):
        self.state = new_state
        self.updated_at = datetime.now()

    def cancel(self):
        self.is_cancelled = True
        self.update_state(KernelState.ERROR)
