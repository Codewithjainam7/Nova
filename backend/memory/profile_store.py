import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.core.logger import app_logger

MEMORY_DIR = Path(__file__).resolve().parent
PROFILE_FILE = MEMORY_DIR / "profile_data.json"
KNOWN_CONTACTS_FILE = Path(__file__).resolve().parent.parent / "devices" / "known_contacts.json"

DEFAULT_PROFILE = {
    "user": {
        "name": "Jainam",
        "preferred_salutation": "Boss",
        "career_focus": "AI/ML Engineering, Autonomous Systems",
        "active_project": "NOVA AI (ADA - Autonomous Digital Assistant)",
        "preferred_messaging_platform": "whatsapp"
    },
    "contacts": {
        "manav": {
            "name": "Manav",
            "alias": "Vedya (WhatsApp only)",
            "platforms": {"whatsapp": "Vedya", "instagram": "Manav", "telegram": "Manav", "default": "Manav"},
            "notes": "Close friend. Saved as Vedya strictly on WhatsApp. On Instagram and other apps his name is Manav."
        },
        "nandini": {
            "name": "Nandini",
            "alias": "Nandini",
            "platforms": {"instagram": "Nandini", "whatsapp": "Nandini", "default": "Nandini"},
            "notes": "Saved as Nandini on both Instagram and WhatsApp."
        }
    },
    "rules": [
        "Always default to WhatsApp if no platform is mentioned for messaging.",
        "Never attempt to launch mobile apps (Instagram, WhatsApp, Telegram) as Windows desktop processes.",
        "Maintain a natural, warm, human-nuanced tone with proper capitalization and punctuation."
    ],
    "preferences": {
        "browser": "Brave",
        "communication_tone": "Warm, witty, articulate, human-like.",
        "phone_connection": "192.168.0.101:5555 (Wireless ADB)"
    }
}

class ProfileStore:
    """
    Persistent store for ADA's Core User Profile, Social Graph, and System Rules.
    Maintains immutable facts and high-confidence user preferences across reboots.
    """
    def __init__(self):
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(PROFILE_FILE):
            try:
                with open(PROFILE_FILE, "w", encoding="utf-8") as f:
                    json.dump(DEFAULT_PROFILE, f, indent=2)
            except Exception as e:
                app_logger.error(f"Failed to initialize profile_data.json: {e}")

    def get_profile(self) -> Dict[str, Any]:
        """Returns the complete user profile and social graph."""
        self._ensure_file()
        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            app_logger.error(f"Failed to read profile_data.json: {e}")
            return DEFAULT_PROFILE

    def save_profile(self, data: Dict[str, Any]):
        """Persists updated profile data to disk and synchronizes known contacts."""
        try:
            with open(PROFILE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            self._sync_to_known_contacts(data)
        except Exception as e:
            app_logger.error(f"Failed to save profile_data.json: {e}")

    def _sync_to_known_contacts(self, profile: Dict[str, Any]):
        """Synchronizes contacts to backend/devices/known_contacts.json for adb execution."""
        try:
            contacts = profile.get("contacts", {})
            mapping = {}
            for key, val in contacts.items():
                k_low = key.lower()
                platforms = val.get("platforms", {})
                default_alias = val.get("alias", key)
                if platforms:
                    mapping[k_low] = platforms
                else:
                    mapping[k_low] = default_alias

            with open(KNOWN_CONTACTS_FILE, "w", encoding="utf-8") as f:
                json.dump(mapping, f, indent=2)
        except Exception as e:
            app_logger.warning(f"Failed to sync known_contacts.json: {e}")

    def upsert_contact(self, name: str, alias: Optional[str] = None, platform: Optional[str] = None, notes: Optional[str] = None):
        """Adds or updates a contact in the social graph."""
        profile = self.get_profile()
        contacts = profile.setdefault("contacts", {})
        key = name.lower().strip()
        
        entry = contacts.setdefault(key, {
            "name": name.strip(),
            "alias": alias.strip() if alias else name.strip(),
            "platforms": {},
            "notes": ""
        })

        if alias:
            entry["alias"] = alias.strip()
            if platform:
                entry.setdefault("platforms", {})[platform.lower()] = alias.strip()
            else:
                entry.setdefault("platforms", {})["default"] = alias.strip()
        
        if notes:
            entry["notes"] = notes.strip()
            
        self.save_profile(profile)
        app_logger.info(f"[ProfileStore] Upserted contact '{name}' (alias: {entry.get('alias')})")

    def update_preference(self, key: str, value: Any):
        """Updates a user preference setting."""
        profile = self.get_profile()
        profile.setdefault("preferences", {})[key] = value
        self.save_profile(profile)

    def add_rule(self, rule_text: str):
        """Appends a new persistent operating rule."""
        profile = self.get_profile()
        rules = profile.setdefault("rules", [])
        if rule_text not in rules:
            rules.append(rule_text)
            self.save_profile(profile)
            app_logger.info(f"[ProfileStore] Added rule: {rule_text}")

    def get_core_profile_prompt(self) -> str:
        """
        Formats permanent profile facts and social context for prompt injection.
        """
        profile = self.get_profile()
        user = profile.get("user", {})
        contacts = profile.get("contacts", {})
        rules = profile.get("rules", [])

        lines = [
            f"User: {user.get('name', 'Jainam')} (Salutation: '{user.get('preferred_salutation', 'Boss')}')",
            f"Active Project: {user.get('active_project', 'NOVA AI (ADA)')}",
            f"Career Focus: {user.get('career_focus', 'AI/ML Engineering')}",
            f"Default Messaging Platform: {user.get('preferred_messaging_platform', 'whatsapp').capitalize()}",
            "Key Social Contacts:"
        ]

        for k, v in contacts.items():
            alias_info = f" (Saved as '{v.get('alias')}')" if v.get("alias") and v.get("alias") != v.get("name") else ""
            notes = f" - {v.get('notes')}" if v.get("notes") else ""
            lines.append(f"  * {v.get('name', k.capitalize())}{alias_info}{notes}")

        if rules:
            lines.append("Permanent User Rules:")
            for r in rules:
                lines.append(f"  - {r}")

        return "\n".join(lines)

# Singleton instance
profile_store = ProfileStore()
