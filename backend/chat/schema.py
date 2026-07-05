from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class ChatMessageType(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"
    TOOL = "TOOL"
    EXECUTION = "EXECUTION"
    ERROR = "ERROR"
    WARNING = "WARNING"
    STREAMING = "STREAMING"
    THINKING = "THINKING"
    NOTIFICATION = "NOTIFICATION"

class ChatAttachmentType(str, Enum):
    IMAGE = "IMAGE"
    PDF = "PDF"
    MARKDOWN = "MARKDOWN"
    TEXT = "TEXT"
    CODE = "CODE"
    CSV = "CSV"
    JSON = "JSON"
    LOGS = "LOGS"
    SCREENSHOT = "SCREENSHOT"
    VOICE = "VOICE"

class ChatAttachment(BaseModel):
    attachment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: ChatAttachmentType
    name: str
    content: Optional[bytes] = None
    uri: Optional[str] = None
    metadata: Dict[str, Any] = {}

class ChatMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: ChatMessageType
    content: str
    attachments: List[ChatAttachment] = []
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = {}

class ChatConversation(BaseModel):
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "New Conversation"
    messages: List[ChatMessage] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    tags: List[str] = []
    folder: str = "Default"
    is_pinned: bool = False
    is_archived: bool = False

class ChatSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    active_conversation_id: Optional[str] = None

class ChatMetrics(BaseModel):
    total_messages: int = 0
    total_conversations: int = 0
    avg_stream_latency_ms: float = 0.0
    avg_render_latency_ms: float = 0.0

class ChatConfiguration(BaseModel):
    max_history_length: int = 1000
    enable_markdown: bool = True
    enable_syntax_highlighting: bool = True
