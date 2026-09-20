import sqlite3
import json
from typing import List, Optional
from datetime import datetime
from backend.memory.schema import MemoryItem, MemoryType
from backend.chat.schema import ChatConversation, ChatMessage, ChatMessageType
from backend.core.logger import app_logger

class SQLiteStore:
    def __init__(self, db_path: str = "nova_memory.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Conversations Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    title TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    is_pinned INTEGER,
                    is_archived INTEGER
                )
            ''')
            
            # Messages Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    type TEXT,
                    content TEXT,
                    timestamp TEXT,
                    metadata TEXT,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(conversation_id)
                )
            ''')
            
            # Memory Metadata Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memory_metadata (
                    memory_id TEXT PRIMARY KEY,
                    memory_type TEXT,
                    content TEXT,
                    metadata TEXT,
                    importance REAL,
                    created_at TEXT,
                    last_accessed_at TEXT,
                    expires_at TEXT
                )
            ''')
            conn.commit()

    # --- Memory Metadata CRUD ---
    def save_memory_metadata(self, item: MemoryItem):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO memory_metadata 
                (memory_id, memory_type, content, metadata, importance, created_at, last_accessed_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item.memory_id,
                item.memory_type.value,
                item.content,
                json.dumps(item.metadata),
                item.importance,
                item.created_at.isoformat(),
                item.last_accessed_at.isoformat(),
                item.expires_at.isoformat() if item.expires_at else None
            ))
            conn.commit()

    def get_memory_metadata(self, memory_id: str) -> Optional[MemoryItem]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM memory_metadata WHERE memory_id = ?', (memory_id,))
            row = cursor.fetchone()
            if row:
                return MemoryItem(
                    memory_id=row[0],
                    memory_type=MemoryType(row[1]),
                    content=row[2],
                    metadata=json.loads(row[3]),
                    importance=row[4],
                    created_at=datetime.fromisoformat(row[5]),
                    last_accessed_at=datetime.fromisoformat(row[6]),
                    expires_at=datetime.fromisoformat(row[7]) if row[7] else None
                )
        return None

    def get_all_memory_metadata(self) -> List[MemoryItem]:
        results = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM memory_metadata')
            rows = cursor.fetchall()
            for row in rows:
                results.append(MemoryItem(
                    memory_id=row[0],
                    memory_type=MemoryType(row[1]),
                    content=row[2],
                    metadata=json.loads(row[3]),
                    importance=row[4],
                    created_at=datetime.fromisoformat(row[5]),
                    last_accessed_at=datetime.fromisoformat(row[6]),
                    expires_at=datetime.fromisoformat(row[7]) if row[7] else None
                ))
        return results

    def delete_memory_metadata(self, memory_id: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM memory_metadata WHERE memory_id = ?', (memory_id,))
            conn.commit()

    # --- Chat History CRUD ---
    def save_conversation(self, conv: ChatConversation):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO conversations 
                (conversation_id, title, created_at, updated_at, is_pinned, is_archived)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                conv.conversation_id,
                conv.title,
                conv.created_at.isoformat(),
                conv.updated_at.isoformat(),
                int(conv.is_pinned),
                int(conv.is_archived)
            ))
            
            # Save messages
            for msg in conv.messages:
                cursor.execute('''
                    INSERT OR REPLACE INTO messages 
                    (message_id, conversation_id, type, content, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    msg.message_id,
                    conv.conversation_id,
                    msg.type.name,
                    msg.content,
                    msg.timestamp.isoformat(),
                    json.dumps(msg.metadata)
                ))
            conn.commit()

    def get_conversation(self, conv_id: str) -> Optional[ChatConversation]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM conversations WHERE conversation_id = ?', (conv_id,))
            c_row = cursor.fetchone()
            if not c_row:
                return None
                
            cursor.execute('SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC', (conv_id,))
            m_rows = cursor.fetchall()
            
            messages = []
            for m in m_rows:
                messages.append(ChatMessage(
                    message_id=m[0],
                    type=ChatMessageType[m[2]],
                    content=m[3],
                    timestamp=datetime.fromisoformat(m[4]),
                    metadata=json.loads(m[5])
                ))
                
            return ChatConversation(
                conversation_id=c_row[0],
                title=c_row[1],
                created_at=datetime.fromisoformat(c_row[2]),
                updated_at=datetime.fromisoformat(c_row[3]),
                is_pinned=bool(c_row[4]),
                is_archived=bool(c_row[5]),
                messages=messages
            )

    def get_all_conversations(self) -> List[ChatConversation]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT conversation_id FROM conversations')
            c_rows = cursor.fetchall()
            
            return [self.get_conversation(r[0]) for r in c_rows if self.get_conversation(r[0])]
