import os
import json
from datetime import datetime
from pathlib import Path
from backend.core.logger import app_logger
from backend.providers.core import AIProviderManager
from backend.providers.schema import GenerationRequest, Message, Role, CognitiveDomain

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = ROOT_DIR / "workspace" / "reports"

class BriefingEngine:
    """
    Generates dynamic, context-aware morning and system boot briefings for ADA.
    Incorporates accurate time perception, completed overnight missions, and system status.
    """
    def __init__(self, provider_manager: AIProviderManager):
        self.provider_manager = provider_manager

    def get_latest_overnight_summary(self) -> str:
        """Reads the latest mission summary only if not already briefed and was a real overnight task."""
        summary_path = REPORTS_DIR / "latest_overnight_summary.json"
        if os.path.exists(summary_path):
            try:
                with open(summary_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Check if already briefed
                if data.get("briefed", False):
                    return ""

                # Mark as briefed so it's not repeated on reconnects
                data["briefed"] = True
                with open(summary_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)

                return data.get("summary", "")
            except Exception:
                pass
        return ""

    async def generate_boot_briefing(self) -> str:
        """
        Dynamically synthesizes a natural, human-nuanced Jarvis greeting using Groq/Gemini.
        """
        now = datetime.now()
        hour = now.hour
        
        # Proper human time perception
        if 0 <= hour < 5:
            time_slot = "late night"
            time_instruction = "It is currently LATE NIGHT (past midnight). The user is working late. Do NOT call this morning! Greet Jainam with a cool late-night tone like 'Burning the midnight oil tonight, Boss?' or 'Late night session, Boss?'."
        elif 5 <= hour < 12:
            time_slot = "morning"
            time_instruction = "It is MORNING. Greet Jainam warmly with 'Good morning, Boss.'."
        elif 12 <= hour < 17:
            time_slot = "afternoon"
            time_instruction = "It is AFTERNOON. Greet Jainam with 'Good afternoon, Boss.'."
        else:
            time_slot = "evening"
            time_instruction = "It is EVENING. Greet Jainam with 'Good evening, Boss.'."

        day_str = now.strftime("%A, %B %d")
        time_str = now.strftime("%I:%M %p")
        
        overnight_context = self.get_latest_overnight_summary()

        if overnight_context:
            mission_prompt_segment = f"The user recently ran an overnight mission: \"{overnight_context}\". Mention that it's completed."
        else:
            mission_prompt_segment = "No pending missions to report. DO NOT invent or mention any overnight jobs, resumes, or tasks!"

        prompt = (
            f"You are ADA (Autonomous Digital Assistant), a Jarvis-tier AI Operating System with a female persona.\n"
            f"The user (Boss/Jainam) is at his laptop.\n"
            f"Current Local Time: {time_str} on {day_str}.\n"
            f"Time Perception Guidance: {time_instruction}\n"
            f"Task Status: {mission_prompt_segment}\n\n"
            f"Task: Generate a dynamic, natural, 1 to 2 sentence greeting.\n"
            f"Rules:\n"
            f"1. Confident, crisp, natural Jarvis persona.\n"
            f"2. Follow the Time Perception Guidance strictly.\n"
            f"3. Keep it to 1 or 2 sentences max.\n"
            f"4. Output ONLY the greeting text. No quotes, no markdown."
        )

        try:
            req = GenerationRequest(
                messages=[Message(role=Role.USER, content=prompt)],
                cognitive_domain=CognitiveDomain.SOCIAL_SYNTHESIS,
                temperature=0.7,
                max_tokens=200
            )
            resp = await self.provider_manager.generate(req)
            briefing = resp.content.strip().strip('"').strip("'")
            if briefing and len(briefing) > 10:
                return briefing
        except Exception as e:
            app_logger.warning(f"Dynamic briefing generation fallback: {e}")

        # Fallback based on time
        if 0 <= hour < 5:
            return "Burning the midnight oil tonight, Boss? ADA is online and all subsystems are green. What are we working on?"
        return f"System online. Good {time_slot}, Boss. All local subsystems are nominal. What are we working on today?"

    async def generate_comprehensive_briefing(self) -> str:
        """
        Generates a full executive Jarvis morning or status briefing when requested by user.
        Includes local time, system vitals, device status, missions, and greeting.
        """
        now = datetime.now()
        hour = now.hour
        day_str = now.strftime("%A, %B %d, %Y")
        time_str = now.strftime("%I:%M %p")

        if 0 <= hour < 5:
            salutation = "Late-night status briefing, Boss."
        elif 5 <= hour < 12:
            salutation = "Good morning, Boss."
        elif 12 <= hour < 17:
            salutation = "Good afternoon, Boss."
        else:
            salutation = "Good evening, Boss."

        # Device connection check
        device_status = "Phone bridge is in standby (no wireless device attached)."
        try:
            from backend.devices.core import DeviceManager
            dm = DeviceManager()
            devs = dm.get_connected_devices()
            if devs and len(devs) > 0:
                device_status = f"Phone bridge active ({len(devs)} device linked via ADB)."
        except Exception as de:
            app_logger.debug(f"Device status check notice: {de}")

        # Mission reports
        missions_summary = ""
        index_file = REPORTS_DIR / "missions_index.json"
        if os.path.exists(index_file):
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    missions = json.load(f)
                    if missions:
                        latest = missions[-1]
                        missions_summary = f"Latest autonomous deliverable: '{latest.get('mission_id', '')}' saved in workspace."
            except Exception:
                pass

        prompt = (
            f"You are ADA, an elite Jarvis-style AI Operating System.\n"
            f"Deliver an executive oral briefing to Boss (Jainam).\n"
            f"Salutation: {salutation}\n"
            f"Time & Date: {time_str} on {day_str}\n"
            f"Subsystem Status: All cognitive neural layers, desktop controllers, and WebSocket daemons are operating at peak performance.\n"
            f"Device Link: {device_status}\n"
            f"{missions_summary}\n\n"
            f"Task: Synthesize a crisp, inspiring, 3 to 4 sentence executive Jarvis briefing.\n"
            f"Format it beautifully, confident, articulate, and ready for his instructions. Output only the briefing text."
        )

        try:
            req = GenerationRequest(
                messages=[Message(role=Role.USER, content=prompt)],
                cognitive_domain=CognitiveDomain.SOCIAL_SYNTHESIS,
                temperature=0.7,
                max_tokens=400
            )
            resp = await self.provider_manager.generate(req)
            content = resp.content.strip().strip('"').strip("'")
            if content and len(content) > 20:
                return content
        except Exception as e:
            app_logger.warning(f"Comprehensive briefing LLM synthesis failed: {e}")

        # Fallback
        return (
            f"{salutation} It is currently {time_str} on {day_str}. "
            f"All ADA operating subsystems are running nominally at peak responsiveness. "
            f"{device_status} "
            f"I am standing by for your commands."
        )
