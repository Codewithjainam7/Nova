import time
import asyncio
from typing import AsyncGenerator
from backend.chat.schema import ChatConfiguration, ChatMetrics, ChatSession, ChatMessage, ChatConversation, ChatMessageType
from backend.chat.presentation import ChatMessageRenderer, ChatStreamRenderer, ChatAttachmentManager, ChatExportManager
from backend.chat.state import ChatMessageStore, ChatHistory, ChatSearchManager, ChatStateManager
from backend.core.logger import app_logger

class ChatLogger:
    @staticmethod
    def log_message(msg: ChatMessage):
        app_logger.info(f"[CHAT] {msg.type.name} message created: {msg.message_id}")

class ChatNotificationManager:
    """Handles ephemeral toasts in the chat UI."""
    def show_toast(self, message: str, level: str = "INFO"):
        app_logger.info(f"[CHAT TOAST - {level}] {message}")

class ChatManager:
    """Dependency Injection Container for the Chat subsystem."""
    def __init__(self, config: ChatConfiguration):
        self.config = config
        self.store = ChatMessageStore()
        self.history = ChatHistory(self.store)
        self.search = ChatSearchManager(self.store)
        self.state = ChatStateManager()
        self.msg_renderer = ChatMessageRenderer()
        self.stream_renderer = ChatStreamRenderer()
        self.attachments = ChatAttachmentManager()
        self.exports = ChatExportManager()
        self.notifications = ChatNotificationManager()

class ChatSystem:
    """Central entrypoint for the NOVA Chat presentation subsystem."""
    def __init__(self):
        self.config = ChatConfiguration()
        self.metrics = ChatMetrics()
        self.session = ChatSession()
        self.manager = ChatManager(self.config)

    async def add_message(self, conversation_id: str, message: ChatMessage):
        start = time.time()
        conv = self.manager.store.get_conversation(conversation_id)
        if not conv:
            conv = ChatConversation(conversation_id=conversation_id)
            self.manager.store.save_conversation(conv)
            
        conv.messages.append(message)
        ChatLogger.log_message(message)
        
        # Trigger UI Render
        await self.manager.msg_renderer.render(message)
        
        self.metrics.total_messages += 1
        elapsed = (time.time() - start) * 1000
        self._update_metric("avg_render_latency_ms", elapsed)
        
    async def stream_response(self, conversation_id: str, stream: AsyncGenerator[str, None]):
        """Consumes a generator from the Response Generator engine and streams to UI."""
        start = time.time()
        
        full_content = await self.manager.stream_renderer.process_stream(stream)
        
        # Once complete, save the final message
        msg = ChatMessage(type=ChatMessageType.ASSISTANT, content=full_content)
        await self.add_message(conversation_id, msg)
        
        elapsed = (time.time() - start) * 1000
        self._update_metric("avg_stream_latency_ms", elapsed)
        return msg

    def _update_metric(self, attr: str, elapsed: float):
        n = getattr(self.metrics, "total_messages", 1)
        if n > 0:
            current = getattr(self.metrics, attr)
            new_val = ((current * (n - 1)) + elapsed) / n
            setattr(self.metrics, attr, new_val)
