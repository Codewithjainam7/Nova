from backend.kernel.schema import KernelState
from backend.core.logger import app_logger

class KernelStateManager:
    def __init__(self):
        self._global_state: KernelState = KernelState.BOOTING

    def transition_to(self, new_state: KernelState):
        app_logger.info(f"Kernel State Transition: {self._global_state.value} -> {new_state.value}")
        self._global_state = new_state

    @property
    def current_state(self) -> KernelState:
        return self._global_state
