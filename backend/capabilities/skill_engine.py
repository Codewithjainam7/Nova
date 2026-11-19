import os
import sys
import time
import importlib.util
import traceback
from typing import Dict, Any, List, Optional
from backend.core.logger import app_logger

class HermesSkillEngine:
    """
    Hermes Procedural Closed-Loop Skill Engine.
    Discovers, validates, executes, and synthesizes modular executable Python skills.
    Skills are stored in backend/skills/<skill_name>.py.
    """

    def __init__(self, skills_dir: Optional[str] = None):
        if not skills_dir:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            skills_dir = os.path.join(project_root, "backend", "skills")
        self.skills_dir = skills_dir
        os.makedirs(self.skills_dir, exist_ok=True)
        self._ensure_starter_skills()

    def _ensure_starter_skills(self):
        # 1. System Telemetry Skill
        sys_skill = os.path.join(self.skills_dir, "system_telemetry.py")
        if not os.path.exists(sys_skill):
            with open(sys_skill, "w", encoding="utf-8") as f:
                f.write('''"""
Skill: system_telemetry
Description: Gathers real-time CPU, RAM, battery, and disk statistics.
"""
import psutil

def run(**kwargs):
    cpu = psutil.cpu_percent(interval=0.2)
    ram = psutil.virtual_memory().percent
    battery = psutil.sensors_battery()
    bat_pct = battery.percent if battery else None
    power_plugged = battery.power_plugged if battery else None
    
    return {
        "status": "SUCCESS",
        "cpu_percent": cpu,
        "ram_percent": ram,
        "battery_percent": bat_pct,
        "charging": power_plugged
    }
''')

        # 2. Desktop Quick Tidy Skill
        tidy_skill = os.path.join(self.skills_dir, "desktop_tidy.py")
        if not os.path.exists(tidy_skill):
            with open(tidy_skill, "w", encoding="utf-8") as f:
                f.write('''"""
Skill: desktop_tidy
Description: Scans the user desktop for unorganized files and categorizes them.
"""
import os

def run(target_dir=None, **kwargs):
    if not target_dir:
        target_dir = os.path.expanduser("~/Desktop")
    
    if not os.path.exists(target_dir):
        return {"status": "ERROR", "message": f"Directory not found: {target_dir}"}
        
    files = [f for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f))]
    extensions = {}
    for f in files:
        ext = os.path.splitext(f)[1].lower() or "no_ext"
        extensions[ext] = extensions.get(ext, 0) + 1
        
    return {
        "status": "SUCCESS",
        "total_files": len(files),
        "extension_breakdown": extensions,
        "preview": files[:8]
    }
''')

    def list_skills(self) -> List[Dict[str, Any]]:
        """Scans skills directory and returns metadata for all loaded skills."""
        skills = []
        for f in os.listdir(self.skills_dir):
            if f.endswith(".py") and not f.startswith("__"):
                name = f[:-3]
                path = os.path.join(self.skills_dir, f)
                doc = ""
                try:
                    with open(path, "r", encoding="utf-8") as file:
                        lines = file.readlines()
                        collecting = False
                        doc_lines = []
                        for line in lines:
                            if '"""' in line or "'''" in line:
                                if collecting:
                                    break
                                collecting = True
                                continue
                            if collecting:
                                doc_lines.append(line.strip())
                        doc = " ".join(doc_lines)
                except Exception:
                    pass
                skills.append({
                    "name": name,
                    "file": f,
                    "description": doc or f"Custom executable skill: {name}"
                })
        return skills

    def execute_skill(self, name: str, **kwargs) -> Dict[str, Any]:
        """Loads and executes a skill function run(**kwargs) dynamically."""
        py_file = os.path.join(self.skills_dir, f"{name}.py")
        if not os.path.exists(py_file):
            return {"status": "ERROR", "message": f"Skill '{name}' does not exist in {self.skills_dir}"}

        try:
            spec = importlib.util.spec_from_file_location(name, py_file)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            if not hasattr(mod, "run"):
                return {"status": "ERROR", "message": f"Skill '{name}' has no run() entrypoint."}

            start_t = time.time()
            result = mod.run(**kwargs)
            duration_ms = int((time.time() - start_t) * 1000)

            app_logger.info(f"[SkillEngine] Skill '{name}' executed in {duration_ms}ms.")
            return {
                "status": "SUCCESS",
                "skill": name,
                "duration_ms": duration_ms,
                "result": result
            }
        except Exception as e:
            app_logger.error(f"[SkillEngine] Execution error in '{name}': {e}")
            return {
                "status": "ERROR",
                "skill": name,
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def synthesize_skill(self, name: str, code: str, description: str = "") -> Dict[str, Any]:
        """Allows NOVA to write and persist new self-learned skills."""
        safe_name = "".join(c for c in name if c.isalnum() or c == "_").lower()
        if not safe_name:
            return {"status": "ERROR", "message": "Invalid skill name."}

        target_path = os.path.join(self.skills_dir, f"{safe_name}.py")
        header = f'''"""\nSkill: {safe_name}\nDescription: {description}\nAuto-synthesized by NOVA on {time.strftime("%Y-%m-%d %H:%M:%S")}\n"""\n\n'''
        
        full_code = header + code.strip() + "\n"
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(full_code)
            app_logger.info(f"[SkillEngine] Synthesized and saved new skill: {safe_name}")
            return {"status": "SUCCESS", "skill": safe_name, "path": target_path}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

skill_engine = HermesSkillEngine()
