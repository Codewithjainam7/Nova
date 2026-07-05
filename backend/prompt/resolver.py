from typing import Dict, Any
from backend.prompt.schema import PromptRequest
from datetime import datetime

class PromptVariableResolver:
    """Resolves variables from context, environment, and user requests."""
    
    def resolve(self, request: PromptRequest) -> Dict[str, Any]:
        variables = {}
        
        # 1. Global / System Variables
        variables["current_time"] = datetime.now().isoformat()
        
        # 2. Context Package extraction
        # We flatten context into string blocks for the template
        context_text = ""
        for item in request.context_package.conversation_context:
            context_text += f"[History] {item.content}\n"
        for item in request.context_package.memory_context:
            context_text += f"[Memory] {item.content}\n"
            
        variables["context_text"] = context_text.strip()
        variables["history_text"] = context_text.strip() # simplified for demo
        
        # 3. User Request
        variables["user_input"] = request.user_input or ""
        
        # 4. Request Custom Variables (Overrides)
        for k, v in request.variables.items():
            variables[k] = v
            
        return variables
