import asyncio
from typing import List, Optional
from backend.chat.schema import ChatConversation, ChatMessage
from backend.core.logger import app_logger

class ChatMessageStore:
    """Manages CRUD for messages within a conversation memory."""
    def __init__(self):
        self._conversations = {} # Mock DB
        
    def save_conversation(self, conv: ChatConversation):
        self._conversations[conv.conversation_id] = conv
        
    def get_conversation(self, conv_id: str) -> Optional[ChatConversation]:
        return self._conversations.get(conv_id)
        
    def get_all(self) -> List[ChatConversation]:
        return list(self._conversations.values())

class ChatHistory:
    """Handles logic for grouping, folders, pinning, and archiving."""
    def __init__(self, store: ChatMessageStore):
        self.store = store

    def pin_conversation(self, conv_id: str, pin: bool = True):
        conv = self.store.get_conversation(conv_id)
        if conv:
            conv.is_pinned = pin
            
    def archive_conversation(self, conv_id: str, archive: bool = True):
         conv = self.store.get_conversation(conv_id)
         if conv:
             conv.is_archived = archive

class ChatSearchManager:
    """Handles full-text search over the local UI message store."""
    def __init__(self, store: ChatMessageStore):
        self.store = store
        
    def search(self, query: str) -> List[ChatMessage]:
        app_logger.debug(f"[CHAT SEARCH] Querying for '{query}'")
        results = []
        for conv in self.store.get_all():
            for msg in conv.messages:
                if query.lower() in msg.content.lower():
                    results.append(msg)
        return results

class ChatStateManager:
    """Holds the active ViewModel state for the Chat UI."""
    def __init__(self):
        self.active_conversation: Optional[ChatConversation] = None
        
    def switch_conversation(self, conversation: ChatConversation):
        app_logger.info(f"[CHAT STATE] Switching to conversation {conversation.conversation_id}")
        self.active_conversation = conversation
