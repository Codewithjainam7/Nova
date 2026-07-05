import asyncio
from backend.email.schema import EmailAction, EmailPermissionLevel
from backend.core.logger import app_logger

class EmailPolicy:
    """Configures rules like max attachments, blocked domains."""
    blocked_domains = ["malicious.com"]

class EmailPermissionManager:
    def __init__(self, current_level: EmailPermissionLevel):
        self.level = current_level

    def check(self, action: EmailAction) -> bool:
        write_actions = ["SEND", "REPLY", "REPLY_ALL", "FORWARD", "DELETE", "MOVE"]
        if self.level == EmailPermissionLevel.READ_ONLY and action.action_type.name in write_actions:
            app_logger.warning(f"Permission denied for {action.action_type.name} in READ_ONLY mode.")
            return False
            
        if self.level == EmailPermissionLevel.COMPOSE and action.action_type.name == "SEND":
             app_logger.warning(f"Permission denied for SEND in COMPOSE mode.")
             return False
             
        # Add policy checks (e.g., checking recipients against blocked domains)
        if "recipients" in action.payload:
            for rec in action.payload["recipients"]:
                if any(domain in rec for domain in EmailPolicy.blocked_domains):
                    app_logger.warning(f"Blocked domain in recipient list: {rec}")
                    return False
                    
        return True

class EmailWorkflow:
    """Orchestrates the steps for complex email operations (e.g. AI Drafting)."""
    
    async def process_ai_draft(self, action: EmailAction) -> dict:
        app_logger.info("Executing AI Draft generation")
        # In a real scenario, this would contact Prompt Engine -> Provider Manager
        await asyncio.sleep(0.5)
        return {"draft_id": "draft_123", "content": "Generated draft text."}
        
    async def summarize_thread(self, action: EmailAction) -> str:
        app_logger.info("Summarizing email thread")
        await asyncio.sleep(0.4)
        return "This thread is about scheduling a meeting."
