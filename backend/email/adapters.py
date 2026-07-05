import asyncio
from typing import List, Any
from backend.email.schema import EmailMessage, EmailAction
from backend.core.logger import app_logger

class BaseEmailAdapter:
    async def execute(self, action: EmailAction) -> Any:
        raise NotImplementedError()

class GmailAdapter(BaseEmailAdapter):
    async def execute(self, action: EmailAction):
        app_logger.debug(f"[GMAIL] Executing {action.action_type}")
        await asyncio.sleep(0.2)
        if action.action_type.name in ["READ", "SEARCH"]:
            return [
                EmailMessage(
                    subject="Mock Gmail Subject",
                    body="Mock Gmail Body",
                    sender="test@gmail.com",
                    recipients=["user@gmail.com"]
                )
            ]
        return True

class OutlookAdapter(BaseEmailAdapter):
    async def execute(self, action: EmailAction):
        app_logger.debug(f"[OUTLOOK] Executing {action.action_type}")
        await asyncio.sleep(0.2)
        if action.action_type.name in ["READ", "SEARCH"]:
            return []
        return True

class IMAPAdapter(BaseEmailAdapter):
    async def execute(self, action: EmailAction):
        app_logger.debug(f"[IMAP] Executing {action.action_type}")
        await asyncio.sleep(0.3)
        if action.action_type.name in ["READ", "SEARCH"]:
            return []
        return True

class SMTPAdapter(BaseEmailAdapter):
    async def execute(self, action: EmailAction):
        app_logger.debug(f"[SMTP] Executing {action.action_type}")
        await asyncio.sleep(0.3)
        return True

class EmailProviderRegistry:
    def __init__(self):
        self._providers = {
            "GMAIL": GmailAdapter(),
            "OUTLOOK": OutlookAdapter(),
            "IMAP": IMAPAdapter(),
            "SMTP": SMTPAdapter(),
        }
        
    def get(self, provider_type: str) -> BaseEmailAdapter:
        return self._providers.get(provider_type)
