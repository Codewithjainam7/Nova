import time
import uuid
import asyncio
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from backend.core.logger import app_logger

class IncomingMessage(BaseModel):
    id: str
    sender: str
    platform: str = "whatsapp"  # whatsapp | telegram | sms | app
    message: str
    suggested_reply: str
    timestamp: float
    status: str = "pending"  # pending | sent | dismissed

class MessagingHub:
    """
    Autonomous Messaging Hub for ADA.
    Handles incoming message queuing, cognitive smart reply drafting,
    real-time Dynamic Island event dispatch, and silent background sending.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MessagingHub, cls).__new__(cls)
            cls._instance.active_message = None
            cls._instance.history = []
            cls._instance.provider_manager = None
        return cls._instance

    def _ensure_provider(self):
        if self.provider_manager is None:
            try:
                from backend.providers.core import AIProviderManager
                self.provider_manager = AIProviderManager()
                self.provider_manager.bootstrap()
            except Exception as e:
                app_logger.warning(f"[MessagingHub] AIProviderManager init fallback: {e}")

    async def draft_reply(self, sender: str, platform: str, message: str) -> str:
        """
        Synthesizes a smart, natural, contextual reply draft from Jainam's perspective
        using ADA's AI provider. Falls back to deterministic heuristics if AI is offline.
        """
        self._ensure_provider()
        
        prompt = (
            f"You are ADA, the personal AI assistant for Jainam.\n"
            f"An incoming {platform.upper()} message has arrived from '{sender}':\n"
            f'"{message}"\n\n'
            f"Write a concise, natural, polite 1-sentence reply that Jainam can send back.\n"
            f"Tone: relaxed, helpful, conversational.\n"
            f"Rules: Return ONLY the exact reply text. Do NOT add quotes, greetings, or prefixes."
        )

        if self.provider_manager:
            try:
                from backend.providers.schema import GenerationRequest, ProviderType
                req = GenerationRequest(
                    prompt=prompt,
                    provider_type=ProviderType.OPENROUTER,
                    max_tokens=60,
                    temperature=0.6
                )
                resp = await self.provider_manager.generate(req)
                if resp and resp.content:
                    draft = resp.content.strip().strip('"').strip("'")
                    if draft:
                        return draft
            except Exception as e:
                app_logger.warning(f"[MessagingHub] LLM reply draft failed, using heuristic: {e}")

        # Intelligent heuristic fallback
        msg_lower = message.lower()
        if any(w in msg_lower for w in ["call", "free", "available", "time", "busy"]):
            return "Hey, currently working on a project, will get back to you shortly!"
        elif any(w in msg_lower for w in ["done", "status", "complete", "update"]):
            return "Hey! Working on the final updates right now, almost done."
        elif any(w in msg_lower for w in ["where", "reach", "coming"]):
            return "On my way, should be there soon!"
        elif any(w in msg_lower for w in ["hi", "hello", "hey"]):
            return f"Hey {sender}! What's up?"
        else:
            return f"Got it, thanks for letting me know {sender}!"

    async def receive_message(
        self,
        sender: str,
        platform: str,
        message: str,
        suggested_reply: Optional[str] = None,
        events_manager = None
    ) -> IncomingMessage:
        """
        Registers an incoming message, generates an autonomous reply draft,
        and broadcasts it to the Dynamic Island via WebSocket events.
        """
        if not suggested_reply:
            suggested_reply = await self.draft_reply(sender, platform, message)

        msg_id = f"msg_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        inc_msg = IncomingMessage(
            id=msg_id,
            sender=sender,
            platform=platform.lower(),
            message=message,
            suggested_reply=suggested_reply,
            timestamp=time.time(),
            status="pending"
        )

        self.active_message = inc_msg
        self.history.append(inc_msg)

        app_logger.info(f"[MessagingHub] Incoming {platform} message from '{sender}': '{message}' -> Draft: '{suggested_reply}'")

        # Broadcast to Dynamic Island WebSocket clients
        if events_manager:
            try:
                import json
                event_payload = {
                    "type": "INCOMING_MESSAGE",
                    "payload": inc_msg.dict()
                }
                await events_manager.broadcast(json.dumps(event_payload))
                app_logger.info(f"[MessagingHub] Broadcasted INCOMING_MESSAGE to WebSocket clients")
            except Exception as e:
                app_logger.error(f"[MessagingHub] Failed to broadcast event: {e}")

        return inc_msg

    async def send_reply(
        self,
        reply_text: str,
        message_id: Optional[str] = None,
        events_manager = None
    ) -> Dict[str, Any]:
        """
        Dispatches the reply via background device manager, updates message status,
        and notifies Dynamic Island.
        """
        target_msg = self.active_message
        if message_id:
            for m in reversed(self.history):
                if m.id == message_id:
                    target_msg = m
                    break

        if not target_msg:
            return {"status": "error", "message": "No active message found to reply to."}

        target_msg.status = "sent"
        self.active_message = None

        app_logger.info(f"[MessagingHub] Sending reply to '{target_msg.sender}' on {target_msg.platform}: '{reply_text}'")

        # Execute background dispatch via DeviceManager
        dispatch_result = "Queued for background delivery"
        try:
            from backend.devices.core import DeviceManager
            dm = DeviceManager()
            # Send message command
            res = dm.execute_command(
                "send_message",
                contact=target_msg.sender,
                message=reply_text,
                app=target_msg.platform
            )
            dispatch_result = str(res)
            app_logger.info(f"[MessagingHub] DeviceManager dispatch result: {dispatch_result}")
        except Exception as e:
            app_logger.warning(f"[MessagingHub] Background device dispatch notice: {e}")

        # Broadcast dismissal / completion
        if events_manager:
            try:
                import json
                event_payload = {
                    "type": "MESSAGE_REPLIED",
                    "payload": {
                        "id": target_msg.id,
                        "sender": target_msg.sender,
                        "reply": reply_text,
                        "result": dispatch_result
                    }
                }
                await events_manager.broadcast(json.dumps(event_payload))
            except Exception as e:
                app_logger.error(f"[MessagingHub] Failed to broadcast MESSAGE_REPLIED: {e}")

        return {
            "status": "success",
            "message": f"Reply successfully sent to {target_msg.sender}",
            "reply": reply_text,
            "dispatch_result": dispatch_result
        }

    async def dismiss_message(self, message_id: Optional[str] = None, events_manager = None) -> Dict[str, Any]:
        """
        Dismisses the active heads-up message without sending a reply.
        """
        if self.active_message:
            self.active_message.status = "dismissed"
            dismissed_id = self.active_message.id
            self.active_message = None
        else:
            dismissed_id = message_id

        if events_manager:
            try:
                import json
                await events_manager.broadcast(json.dumps({
                    "type": "MESSAGE_DISMISSED",
                    "payload": {"id": dismissed_id}
                }))
            except Exception as e:
                app_logger.error(f"[MessagingHub] Failed to broadcast MESSAGE_DISMISSED: {e}")

        return {"status": "success", "message": "Message dismissed."}

messaging_hub = MessagingHub()
