import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.core.logger import app_logger

MEMORY_DIR = Path(__file__).resolve().parent
ROUTINE_FILE = MEMORY_DIR / "routine_data.json"

DEFAULT_ROUTINE = {
    "sessions": [],
    "frequent_apps": {
        "whatsapp": 5,
        "brave": 3,
        "vscode": 2
    },
    "frequent_contacts": {
        "Vedya": 4,
        "Nandini": 2
    },
    "habits": [
        "Prefers late-night sessions between 22:00 and 02:00.",
        "Primary communication tool is WhatsApp on wireless Android device.",
        "Developer workflow centered around Python, AI/ML, and Vite/React frontend."
    ]
}

class RoutineTracker:
    """
    Tracks session frequencies, active hours, frequent apps, and communication habits.
    Generates contextual routine perceptions for ADA to anticipate user needs.
    """
    def __init__(self):
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(ROUTINE_FILE):
            try:
                with open(ROUTINE_FILE, "w", encoding="utf-8") as f:
                    json.dump(DEFAULT_ROUTINE, f, indent=2)
            except Exception as e:
                app_logger.error(f"Failed to initialize routine_data.json: {e}")

    def _read_data(self) -> Dict[str, Any]:
        self._ensure_file()
        try:
            with open(ROUTINE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_ROUTINE

    def _write_data(self, data: Dict[str, Any]):
        try:
            with open(ROUTINE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            app_logger.error(f"Failed to save routine_data.json: {e}")

    def record_activity(self, app: Optional[str] = None, contact: Optional[str] = None, action_type: Optional[str] = None):
        """Records an action occurrence to build frequency statistics."""
        data = self._read_data()
        
        if app:
            apps = data.setdefault("frequent_apps", {})
            k = app.lower().strip()
            apps[k] = apps.get(k, 0) + 1

        if contact:
            contacts = data.setdefault("frequent_contacts", {})
            c = contact.strip()
            contacts[c] = contacts.get(c, 0) + 1

        # Keep last 50 session markers
        now = datetime.now()
        sessions = data.setdefault("sessions", [])
        sessions.append({
            "timestamp": now.isoformat(),
            "hour": now.hour,
            "action": action_type or "command"
        })
        if len(sessions) > 50:
            data["sessions"] = sessions[-50:]

        self._write_data(data)

    def get_routine_context(self) -> str:
        """
        Synthesizes a short, punchy summary of active routine and habit context.
        """
        data = self._read_data()
        now = datetime.now()
        hour = now.hour

        # Determine time of day dynamic
        if 0 <= hour < 5:
            time_context = "Late Night (past midnight) - Focus session"
        elif 5 <= hour < 12:
            time_context = "Morning - Start of workday"
        elif 12 <= hour < 17:
            time_context = "Afternoon - Active workflow"
        else:
            time_context = "Evening / Night - Development & personal comms"

        top_apps = sorted(data.get("frequent_apps", {}).items(), key=lambda x: x[1], reverse=True)[:3]
        app_str = ", ".join([f"{a[0]}" for a in top_apps]) if top_apps else "WhatsApp, Brave, VS Code"

        top_contacts = sorted(data.get("frequent_contacts", {}).items(), key=lambda x: x[1], reverse=True)[:2]
        contact_str = ", ".join([f"{c[0]}" for c in top_contacts]) if top_contacts else "Vedya, Nandini"

        habits = data.get("habits", [])
        habit_str = "; ".join(habits[:2]) if habits else "Prefers direct, efficient execution."

        return (
            f"Active Session Phase: {time_context} ({now.strftime('%I:%M %p')})\n"
            f"Frequent Tools: {app_str}\n"
            f"Frequent Contacts: {contact_str}\n"
            f"Known Habits: {habit_str}"
        )

    def get_routine_stats(self) -> Dict[str, Any]:
        return self._read_data()

# Singleton instance
routine_tracker = RoutineTracker()
