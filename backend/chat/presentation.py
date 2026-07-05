import asyncio
import json
from typing import List, AsyncGenerator
from backend.chat.schema import ChatMessage, ChatConversation, ChatAttachment
from backend.core.logger import app_logger

class ChatMessageRenderer:
    """Handles parsing and UI-friendly rendering of complete messages (Markdown, LaTeX, etc)."""
    async def render(self, message: ChatMessage) -> dict:
        app_logger.debug(f"[CHAT RENDERER] Rendering {message.type.name} message.")
        await asyncio.sleep(0.01) # Simulate CPU parsing bound
        return {
            "id": message.message_id,
            "html_content": f"<p>{message.content}</p>", # Simplified
            "type": message.type.name
        }

class ChatStreamRenderer:
    """Handles real-time stream updates, partial tokens, and typing indicators."""
    def __init__(self):
        self.is_streaming = False
        
    async def process_stream(self, token_stream: AsyncGenerator[str, None]):
        self.is_streaming = True
        app_logger.debug("[CHAT STREAM] Started streaming response.")
        
        full_content = ""
        async for token in token_stream:
            full_content += token
            # Yield partial update to UI here
            await asyncio.sleep(0.005) # Simulate 60fps pacing
            
        self.is_streaming = False
        app_logger.debug("[CHAT STREAM] Finished streaming response.")
        return full_content

class ChatAttachmentManager:
    """Handles rendering and indexing UI attachments."""
    async def attach(self, attachment: ChatAttachment) -> dict:
        app_logger.debug(f"[CHAT ATTACHMENT] Processing {attachment.type.name}")
        return {"id": attachment.attachment_id, "url": attachment.uri or f"/blob/{attachment.attachment_id}"}

class ChatExportManager:
    """Handles exporting conversations to various formats."""
    def export_to_json(self, conversation: ChatConversation) -> str:
        app_logger.info(f"[CHAT EXPORT] Exporting conversation {conversation.conversation_id} to JSON.")
        return json.dumps(conversation.model_dump(), default=str)
        
    def export_to_markdown(self, conversation: ChatConversation) -> str:
        app_logger.info(f"[CHAT EXPORT] Exporting conversation {conversation.conversation_id} to Markdown.")
        md = f"# {conversation.title}\n\n"
        for msg in conversation.messages:
            md += f"**{msg.type.name}**: {msg.content}\n\n"
        return md
