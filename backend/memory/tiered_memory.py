import os
import time
import sqlite3
from typing import Dict, Any, List, Optional
from backend.core.logger import app_logger

class TieredMemoryManager:
    """
    Hermes-style Tiered Memory Architecture:
    1. USER.md: High-priority, compact user profile & preferences (<1500 chars).
    2. MEMORY.md: High-level environmental facts & verified lessons (<3000 chars).
    3. SQLite FTS5: Indexed historical episodic conversation memory.
    """

    def __init__(self, root_dir: Optional[str] = None):
        if not root_dir:
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.root_dir = root_dir
        self.user_md_path = os.path.join(root_dir, "USER.md")
        self.memory_md_path = os.path.join(root_dir, "MEMORY.md")
        self.db_path = os.path.join(root_dir, "database", "sqlite", "episodic_fts.db")

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._ensure_files()
        self._init_fts()

    def _ensure_files(self):
        if not os.path.exists(self.user_md_path):
            with open(self.user_md_path, "w", encoding="utf-8") as f:
                f.write(
                    "# User Profile & Preferences\n"
                    "- Name: Jainam\n"
                    "- Preferred Tone: Concise, proactive, premium executive assistant\n"
                    "- Primary Devices: Windows Laptop, POCO X6 Neo 5G (HyperOS)\n"
                    "- Primary Apps: Telegram, WhatsApp, Spotify, Chrome\n"
                    "- Rules: Human confirmation for destructive actions; real-time volume & low latency\n"
                )

        if not os.path.exists(self.memory_md_path):
            with open(self.memory_md_path, "w", encoding="utf-8") as f:
                f.write(
                    "# System Memory & Environment Facts\n"
                    "- Project: NOVA / ADA AI Operating Layer\n"
                    "- Telephony: Dual-SIM HyperOS InCallUI with Groq Whisper & LLaMA 3.3\n"
                    "- Touchpad: Ultra-precision multi-touch wireless trackpad with USB reverse tunnel (0ms)\n"
                    "- Audio: Windows GSMTC real-time volume sync + Edge-TTS Neural\n"
                    "- Skills: Auto-synthesized modular procedural skills in backend/skills/\n"
                )

    def _init_fts(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS episodic_memory USING fts5(
                        timestamp,
                        session_id,
                        role,
                        content,
                        tags
                    )
                """)
        except Exception as e:
            app_logger.warning(f"[TieredMemory] FTS5 initialization notice: {e}")

    def read_user_profile(self) -> str:
        try:
            if os.path.exists(self.user_md_path):
                with open(self.user_md_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
        except Exception as e:
            app_logger.error(f"[TieredMemory] Read USER.md error: {e}")
        return ""

    def read_system_facts(self) -> str:
        try:
            if os.path.exists(self.memory_md_path):
                with open(self.memory_md_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
        except Exception as e:
            app_logger.error(f"[TieredMemory] Read MEMORY.md error: {e}")
        return ""

    def append_lesson(self, lesson: str):
        """Appends a verified lesson to MEMORY.md with micro-compaction bound."""
        facts = self.read_system_facts()
        new_entry = f"- Lesson [{time.strftime('%Y-%m-%d')}]: {lesson.strip()}"
        if new_entry in facts:
            return

        lines = facts.splitlines()
        # Keep under ~40 lines to avoid token explosion
        if len(lines) > 45:
            lines = lines[:5] + lines[-35:]
        lines.append(new_entry)

        with open(self.memory_md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        app_logger.info(f"[TieredMemory] Recorded new lesson: {lesson[:40]}...")

    def index_conversation_turn(self, role: str, content: str, session_id: str = "default", tags: str = ""):
        """Stores a turn in SQLite FTS5 for deep historical semantic retrieval."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO episodic_memory (timestamp, session_id, role, content, tags) VALUES (?, ?, ?, ?, ?)",
                    (time.time(), session_id, role, content, tags)
                )
        except Exception as e:
            app_logger.debug(f"[TieredMemory] Index turn notice: {e}")

    def search_episodic_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Fast BM25 full-text search across all historical sessions."""
        results = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT timestamp, role, content, tags FROM episodic_memory WHERE episodic_memory MATCH ? ORDER BY rank LIMIT ?",
                    (query, limit)
                )
                for row in cur.fetchall():
                    results.append({
                        "timestamp": row[0],
                        "role": row[1],
                        "content": row[2],
                        "tags": row[3]
                    })
        except Exception as e:
            app_logger.debug(f"[TieredMemory] FTS search notice: {e}")
        return results

    def get_system_prompt_tier(self) -> str:
        """Assembles high-density, bounded memory prompt for LLM context injection."""
        user_p = self.read_user_profile()
        sys_f = self.read_system_facts()

        prompt_parts = []
        if user_p:
            prompt_parts.append(f"=== USER PROFILE (USER.md) ===\n{user_p}")
        if sys_f:
            prompt_parts.append(f"=== SYSTEM & CONVENTIONS (MEMORY.md) ===\n{sys_f}")

        return "\n\n".join(prompt_parts)

tiered_memory = TieredMemoryManager()
