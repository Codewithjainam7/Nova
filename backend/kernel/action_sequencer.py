from typing import List, Dict, Any, Optional
from backend.core.logger import app_logger

class ActionSequenceStep:
    def __init__(self, action_type: str, payload: Dict[str, Any], engine: str = "desktop"):
        self.action_type = action_type
        self.payload = payload
        self.engine = engine
        self.status = "PENDING"

class StatefulActionSequencer:
    """
    Decomposes high-level intents into a sequence of atomic, stateful actions.
    """
    
    @staticmethod
    def decompose_intent(app: str, intent: str, entity: str) -> List[ActionSequenceStep]:
        app_logger.info(f"Decomposing intent '{intent}' for '{app}' into atomic sequence.")
        steps = []
        
        # 1. Launch
        steps.append(ActionSequenceStep("APP_LAUNCH", {"name": app}))
        
        # 2. Wait / Verify
        steps.append(ActionSequenceStep("WAIT_READY", {"app": app, "timeout": 10}))
        
        # 3. Focus
        steps.append(ActionSequenceStep("WINDOW_FOCUS", {"title": app}))
        
        if intent == "play_media":
            if app.lower() == "spotify":
                # Spotify specific atomic sequence
                steps.append(ActionSequenceStep("KEYBOARD_SHORTCUT", {"keys": ["ctrl", "l"]}))
                steps.append(ActionSequenceStep("WAIT", {"ms": 500}))
                steps.append(ActionSequenceStep("KEYBOARD_TYPE", {"text": entity}))
                steps.append(ActionSequenceStep("WAIT", {"ms": 500}))
                steps.append(ActionSequenceStep("KEYBOARD_SHORTCUT", {"keys": ["enter"]}))
                steps.append(ActionSequenceStep("WAIT", {"ms": 2500})) # Network load
                steps.append(ActionSequenceStep("KEYBOARD_SHORTCUT", {"keys": ["tab"]}))
                steps.append(ActionSequenceStep("WAIT", {"ms": 100}))
                steps.append(ActionSequenceStep("KEYBOARD_SHORTCUT", {"keys": ["tab"]}))
                steps.append(ActionSequenceStep("WAIT", {"ms": 100}))
                steps.append(ActionSequenceStep("KEYBOARD_SHORTCUT", {"keys": ["enter"]}))
            else:
                # Generic media
                steps.append(ActionSequenceStep("UI_SEARCH", {"query": entity}))
                steps.append(ActionSequenceStep("KEYBOARD_SHORTCUT", {"keys": ["enter"]}))
                steps.append(ActionSequenceStep("WAIT", {"ms": 2000}))
                steps.append(ActionSequenceStep("KEYBOARD_SHORTCUT", {"keys": ["tab", "tab", "enter"]}))
                
        elif intent == "search" or intent == "write":
            steps.append(ActionSequenceStep("UI_SEARCH", {"query": entity}))
            steps.append(ActionSequenceStep("KEYBOARD_SHORTCUT", {"keys": ["enter"]}))
            
        # 4. Final Verify
        steps.append(ActionSequenceStep("VERIFY_STATE", {"expected": "action_completed"}))
        
        return steps
