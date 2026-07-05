from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class EmailPermissionLevel(str, Enum):
    READ_ONLY = "READ_ONLY"
    COMPOSE = "COMPOSE"
    SEND = "SEND"
    DELETE = "DELETE"
    DANGEROUS = "DANGEROUS"

class EmailProviderType(str, Enum):
    GMAIL = "GMAIL"
    OUTLOOK = "OUTLOOK"
    IMAP = "IMAP"
    SMTP = "SMTP"

class EmailActionType(str, Enum):
    READ = "READ"
    SEND = "SEND"
    REPLY = "REPLY"
    REPLY_ALL = "REPLY_ALL"
    FORWARD = "FORWARD"
    DRAFT = "DRAFT"
    DELETE = "DELETE"
    ARCHIVE = "ARCHIVE"
    LABEL = "LABEL"
    MOVE = "MOVE"
    MARK_READ = "MARK_READ"
    MARK_UNREAD = "MARK_UNREAD"
    SEARCH = "SEARCH"
    DOWNLOAD_ATTACHMENT = "DOWNLOAD_ATTACHMENT"
    UPLOAD_ATTACHMENT = "UPLOAD_ATTACHMENT"
    SUMMARIZE_THREAD = "SUMMARIZE_THREAD"
    COMPOSE_AI = "COMPOSE_AI"

class EmailMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subject: str
    body: str
    sender: str
    recipients: List[str]
    cc: List[str] = []
    bcc: List[str] = []
    attachments: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.now)
    is_read: bool = False
    labels: List[str] = []

class EmailAction(BaseModel):
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action_type: EmailActionType
    payload: Dict[str, Any] = {}
    provider: EmailProviderType = EmailProviderType.GMAIL

class EmailSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    permissions: EmailPermissionLevel = EmailPermissionLevel.READ_ONLY
    created_at: datetime = Field(default_factory=datetime.now)

class EmailMetrics(BaseModel):
    total_actions: int = 0
    failed_actions: int = 0
    avg_read_latency_ms: float = 0.0
    avg_send_latency_ms: float = 0.0
    avg_ai_latency_ms: float = 0.0
