from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import time
from backend.core.logger import app_logger

class AppState(BaseModel):
    name: str
    is_running: bool = False
    focused: bool = False
    last_interaction: float = 0.0

class AuthState(BaseModel):
    service: str
    is_authenticated: bool = False
    token_expiry: Optional[float] = None
    last_verified: float = 0.0

class WorldState(BaseModel):
    running_apps: Dict[str, AppState] = Field(default_factory=dict)
    browser_tabs: List[str] = Field(default_factory=list)
    clipboard_content: str = ""
    auth_states: Dict[str, AuthState] = Field(default_factory=dict)
    active_workflow: Optional[str] = None
    last_updated: float = 0.0

class WorldModelEngine:
    """
    Maintains a live, in-memory representation of the OS and API environment.
    Provides context to the Planner and Execution engines to avoid redundant actions.
    """
    def __init__(self):
        self.state = WorldState()

    def update_app_state(self, name: str, is_running: bool, focused: bool = False):
        self.state.running_apps[name] = AppState(
            name=name, 
            is_running=is_running, 
            focused=focused, 
            last_interaction=time.time()
        )
        self.state.last_updated = time.time()
        app_logger.debug(f"[WorldModel] Updated app state for {name}")

    def update_auth_state(self, service: str, is_authenticated: bool, expiry: Optional[float] = None):
        self.state.auth_states[service] = AuthState(
            service=service,
            is_authenticated=is_authenticated,
            token_expiry=expiry,
            last_verified=time.time()
        )
        self.state.last_updated = time.time()
        app_logger.debug(f"[WorldModel] Updated auth state for {service}")

    def get_context_snapshot(self) -> str:
        """Generates a text summary of the current world state for the Planner LLM."""
        lines = ["[Current World State]"]
        
        apps = [name for name, s in self.state.running_apps.items() if s.is_running]
        lines.append(f"Running Apps: {', '.join(apps) if apps else 'None'}")
        
        focused = [name for name, s in self.state.running_apps.items() if s.focused]
        lines.append(f"Focused App: {focused[0] if focused else 'Desktop'}")
        
        auths = [srv for srv, s in self.state.auth_states.items() if s.is_authenticated]
        lines.append(f"Authenticated APIs: {', '.join(auths) if auths else 'None'}")
        
        return "\n".join(lines)
