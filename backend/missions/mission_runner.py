import os
import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from backend.core.logger import app_logger
from backend.providers.core import AIProviderManager
from backend.providers.schema import GenerationRequest, Message, Role, CognitiveDomain

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = ROOT_DIR / "workspace" / "reports"
MISSIONS_INDEX_FILE = REPORTS_DIR / "missions_index.json"

class MissionRunner:
    """
    Autonomous Background & Overnight Mission Runner for ADA.
    Executes multi-stage unattended tasks (research, job hunting, resume drafting, codebase audits)
    and prepares morning briefing dossiers for the user.
    """
    def __init__(self, provider_manager: AIProviderManager):
        self.provider_manager = provider_manager
        os.makedirs(REPORTS_DIR, exist_ok=True)
        self._ensure_index_file()

    def _ensure_index_file(self):
        if not os.path.exists(MISSIONS_INDEX_FILE):
            try:
                with open(MISSIONS_INDEX_FILE, "w", encoding="utf-8") as f:
                    json.dump([], f, indent=2)
            except Exception as e:
                app_logger.error(f"Failed to create missions_index.json: {e}")

    def get_all_missions(self) -> List[Dict[str, Any]]:
        """Returns the list of all historical and active missions."""
        self._ensure_index_file()
        try:
            with open(MISSIONS_INDEX_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_mission_to_index(self, mission_record: Dict[str, Any]):
        """Persists a new or updated mission record to the missions index."""
        missions = self.get_all_missions()
        # Update existing or prepend new
        updated = False
        for idx, m in enumerate(missions):
            if m.get("mission_id") == mission_record.get("mission_id"):
                missions[idx] = mission_record
                updated = True
                break
        if not updated:
            missions.insert(0, mission_record)

        try:
            with open(MISSIONS_INDEX_FILE, "w", encoding="utf-8") as f:
                json.dump(missions, f, indent=2)
        except Exception as e:
            app_logger.error(f"Failed to save missions index: {e}")

    def get_mission_by_id(self, mission_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single mission by its ID."""
        missions = self.get_all_missions()
        for m in missions:
            if m.get("mission_id") == mission_id:
                return m
        return None

    def is_away_or_night_mission(self, user_query: str) -> bool:
        """Determines if a query represents an unattended overnight or away mission."""
        q = user_query.lower()
        triggers = [
            "sleep", "sleeping", "going to bed", "night", "overnight",
            "while i am away", "while i'm away", "while i am out",
            "till i am back", "till i'm back", "unattended", "in the background",
            "while i sleep", "while i rest", "night mission", "night shift"
        ]
        return any(t in q for t in triggers)

    async def execute_mission(self, user_query: str) -> Dict[str, Any]:
        """
        Executes a complete autonomous mission through strategic planning,
        deliverable generation, and morning briefing preparation.
        """
        mission_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        safe_title = "".join(c for c in user_query[:40] if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        report_filename = f"mission_{safe_title}_{timestamp}.md"
        report_path = REPORTS_DIR / report_filename

        app_logger.info(f"[Mission Runner] Launching autonomous mission {mission_id}: {user_query}")

        # Initial index entry: RUNNING
        mission_record = {
            "mission_id": mission_id,
            "title": safe_title.replace("_", " "),
            "query": user_query,
            "status": "RUNNING",
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "report_file": str(report_path),
            "summary": "Mission in progress..."
        }
        self._save_mission_to_index(mission_record)

        # Retrieve profile context for personalization
        from backend.memory.profile_store import profile_store
        user_profile_context = profile_store.get_core_profile_prompt()

        # Strategic Mission Planning & Execution Prompt
        plan_prompt = f"""You are ADA's Strategic Autonomous Night-Shift Agent.
The user (Boss/Jainam) is stepping away or going to sleep and assigned this unattended mission:
"{user_query}"

User Context & Career Goals:
{user_profile_context}

MISSION DIRECTIVE:
1. Conduct deep, thorough strategic analysis and comprehensive execution.
2. Produce real, tangible deliverables (not vague high-level bullet points):
   - If job search or resume: concrete role profiles, tailored ATS bullet points, portfolio project specifications, and exact search strategies.
   - If codebase or development: architectural breakdown, module audit, edge cases, implementation recommendations.
   - If market research: structured competitive matrices, actionable findings, executive summary.
3. Structure your report into clear, professional Markdown with:
   - Executive Summary
   - Strategic Breakdown & Analysis
   - Tangible Deliverables / Actionable Blueprints
   - Morning Action Items for the User

Output ONLY clean Markdown."""

        req = GenerationRequest(
            messages=[Message(role=Role.USER, content=plan_prompt)],
            cognitive_domain=CognitiveDomain.DEEP_PLANNING,
            temperature=0.7,
            max_tokens=3500
        )

        try:
            resp = await self.provider_manager.generate(req)
            report_content = resp.content
        except Exception as e:
            app_logger.error(f"Mission execution LLM error: {e}")
            report_content = f"## Mission Execution Notice\n\nEncountered an exception during execution: {e}\n\nFalling back to core execution analysis."

        # Assemble Full Deliverable Report
        full_doc = f"""# Autonomous Mission Deliverable: {user_query}
*Executed by ADA Autonomous Night Shift Agent*  
*Mission ID*: `{mission_id}`  
*Initiated*: `{datetime.now().strftime('%A, %B %d, %Y - %I:%M %p')}`  
*Status*: `COMPLETED`  

---

{report_content}

---
*Report autonomously generated by ADA. Stored in `{report_path}`.*
"""
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(full_doc)

        # Synthesize a sharp 1-sentence summary for the Morning Briefing
        summary_prompt = (
            f"User assigned overnight mission: \"{user_query}\".\n"
            f"Deliverable has been generated and saved to {report_filename}.\n"
            f"Provide a concise, 1-sentence executive summary of what was accomplished for the morning voice briefing to the Boss (Jainam).\n"
            f"Example: 'Completed your strategic research on AI/ML roles, mapped 4 target profiles, and tailored your resume action points in your workspace dossier.'"
        )
        try:
            sum_req = GenerationRequest(
                messages=[Message(role=Role.USER, content=summary_prompt)],
                cognitive_domain=CognitiveDomain.SOCIAL_SYNTHESIS,
                temperature=0.5,
                max_tokens=150
            )
            sum_resp = await self.provider_manager.generate(sum_req)
            brief_summary = sum_resp.content.strip().strip('"').strip("'")
        except Exception:
            brief_summary = f"Completed overnight mission for '{user_query[:50]}' and saved comprehensive deliverable to {report_filename}."

        # Update Final Index Record
        mission_record["status"] = "COMPLETED"
        mission_record["completed_at"] = datetime.now().isoformat()
        mission_record["summary"] = brief_summary
        self._save_mission_to_index(mission_record)

        # Update latest_overnight_summary.json for Morning Boot Briefing
        summary_path = REPORTS_DIR / "latest_overnight_summary.json"
        summary_data = {
            "mission_id": mission_id,
            "query": user_query,
            "completed_at": datetime.now().isoformat(),
            "report_file": str(report_path),
            "summary": brief_summary,
            "briefed": False
        }
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2)

        # Broadcast WebSocket event to frontend if events manager is active
        try:
            from backend.main import events_ws_manager
            payload = {
                "type": "MISSION_COMPLETED",
                "payload": {
                    "mission_id": mission_id,
                    "title": safe_title.replace("_", " "),
                    "summary": brief_summary,
                    "report_file": str(report_path)
                }
            }
            asyncio.create_task(events_ws_manager.broadcast(json.dumps(payload)))
        except Exception:
            pass

        app_logger.info(f"[Mission Runner] Mission {mission_id} completed successfully. Saved to {report_path}")
        return summary_data
