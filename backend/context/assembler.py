from typing import List
from backend.context.schema import ContextPackage, ContextItem, ContextType

class ContextAssembler:
    """Assembles the final filtered/compressed items into a ContextPackage."""
    @staticmethod
    def assemble(items: List[ContextItem]) -> ContextPackage:
        package = ContextPackage()
        total_tokens = 0
        
        for item in items:
            total_tokens += item.estimated_tokens
            
            if item.type == ContextType.CONVERSATION:
                package.conversation_context.append(item)
            elif item.type in [ContextType.WORKING_MEMORY, ContextType.LONG_TERM_MEMORY]:
                package.memory_context.append(item)
            elif item.type in [ContextType.PLANNER_STATE, ContextType.EXECUTION_STATE, ContextType.VERIFICATION_RESULT]:
                package.execution_context.append(item)
            elif item.type == ContextType.DESKTOP_STATE:
                package.desktop_context.append(item)
            elif item.type == ContextType.BROWSER_STATE:
                package.browser_context.append(item)
            elif item.type == ContextType.SYSTEM:
                package.preference_context.append(item)
                
        package.total_estimated_tokens = total_tokens
        return package
