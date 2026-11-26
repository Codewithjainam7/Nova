"""
Safe Terminal & Developer Workspace Controller for ADA.
Handles creating project folders, opening directories in VS Code,
running read-only system/network diagnostics, and guarded PowerShell execution.
"""

import os
import re
import shutil
import subprocess
from typing import Optional
import psutil
from backend.desktop.controllers.base_controller import AppController
from backend.core.logger import app_logger


BLOCKED_DANGEROUS_PATTERNS = [
    r"\brm\s+-rf\b",
    r"\bdel\s+/[fsq]",
    r"\brmdir\s+/s",
    r"\bformat\s+[a-z]:",
    r"\bshutdown\b",
    r"\brestart-computer\b",
    r"\bstop-computer\b",
    r"\bremove-item\b.*-recurse.*-force",
    r"\breg\s+delete\b",
    r"\bbcdedit\b",
    r"\bdiskpart\b",
]


class TerminalWorkspaceController(AppController):
    """Controller for developer workspaces, VS Code launching, and safe PowerShell diagnostics."""

    def __init__(self):
        self.last_output: Optional[str] = None
        self.last_file_path: Optional[str] = None

    def is_open(self) -> bool:
        return True

    def launch(self):
        pass

    def wait_ready(self, timeout: int = 10) -> bool:
        return True

    def _resolve_workspace_path(self, folder_spec: str) -> str:
        spec = (folder_spec or "ada_workspace").strip()
        # Explicit drive path
        m_abs = re.search(r"([a-zA-Z]:\\[^\"\'\r\n<>|?*]+)", spec)
        if m_abs:
            return os.path.normpath(m_abs.group(1).strip())

        low = spec.lower()
        name = re.sub(
            r"\b(?:on\s+(?:desktop|downloads|documents|d\s+drive|d:)|in\s+(?:vs\s+code|vscode)|open\s+it|and\s+open|folder|directory|project|called|named)\b",
            " ",
            spec,
            flags=re.IGNORECASE,
        )
        name = re.sub(r"[^a-zA-Z0-9._ -]", "", " ".join(name.split())).strip() or "ada_project"

        home = os.path.expanduser("~")
        if "d drive" in low or "d:" in low:
            root = "D:\\" if os.path.exists("D:\\") else os.path.join(home, "Desktop")
        elif "download" in low:
            root = os.path.join(home, "Downloads")
        elif "document" in low:
            root = os.path.join(home, "Documents")
        else:
            root = os.path.join(home, "Desktop")

        return os.path.join(root, name)

    def _open_in_vscode(self, path: str) -> bool:
        code_bin = shutil.which("code")
        if not code_bin:
            candidates = [
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
                r"C:\Program Files\Microsoft VS Code\Code.exe",
            ]
            for c in candidates:
                if os.path.exists(c):
                    code_bin = c
                    break
        if not code_bin:
            return False

        cflags = 0x08000000  # CREATE_NO_WINDOW
        subprocess.Popen([code_bin, path], creationflags=cflags)
        return True

    def execute(self, intent: str, entity: Optional[str]) -> bool:
        app_logger.info(f"TerminalWorkspaceController executing intent='{intent}' entity='{entity}'")
        self.last_output = None
        self.last_file_path = None
        intent_low = (intent or "").lower().strip()
        raw = (entity or "").strip()

        if intent_low in ["create_workspace", "create_folder"]:
            target_path = self._resolve_workspace_path(raw)
            if any(blk in target_path.lower() for blk in ["\\windows\\", "\\system32"]):
                self.last_output = f"Blocked unsafe system path: `{target_path}`"
                return False

            os.makedirs(target_path, exist_ok=True)
            open_vscode = any(k in raw.lower() for k in ["vs code", "vscode", "visual studio code", "in code"])
            opened = self._open_in_vscode(target_path) if open_vscode else False
            folder_label = os.path.basename(target_path) or target_path
            if open_vscode and opened:
                self.last_output = f"Created your {folder_label} folder and opened it in VS Code, Boss."
            elif open_vscode and not opened:
                self.last_file_path = target_path
                self.last_output = f"Created your {folder_label} folder, though VS Code was not found on PATH. Should I open the folder for you?"
            else:
                self.last_file_path = target_path
                self.last_output = f"Created your {folder_label} workspace folder, Boss. Should I open it for you?"
            return True

        if intent_low == "open_vscode":
            target_path = self._resolve_workspace_path(raw)
            os.makedirs(target_path, exist_ok=True)
            if self._open_in_vscode(target_path):
                self.last_output = f"Opened `{target_path}` in VS Code."
                return True
            self.last_output = "VS Code executable was not found on this machine."
            return False

        if intent_low == "system_diagnostics":
            low = raw.lower()
            if "port" in low:
                conns = [c for c in psutil.net_connections(kind="inet") if c.status == "LISTEN"]
                lines = []
                seen = set()
                for c in conns:
                    port = c.laddr.port if c.laddr else None
                    if port and port not in seen:
                        seen.add(port)
                        pname = "?"
                        try:
                            if c.pid:
                                pname = psutil.Process(c.pid).name()
                        except Exception:
                            pass
                        lines.append(f"- Port `{port}` -> `{pname}` (PID {c.pid})")
                top = "\n".join(sorted(lines)[:12]) or "No listening TCP ports found."
                self.last_output = f"Listening ports on this machine:\n{top}"
                return True

            if "disk" in low or "storage" in low or "space" in low:
                parts = []
                for p in psutil.disk_partitions():
                    if "cdrom" in p.opts or not os.path.exists(p.mountpoint):
                        continue
                    try:
                        u = psutil.disk_usage(p.mountpoint)
                        parts.append(
                            f"- `{p.mountpoint}`: {u.free / (1024**3):.1f} GB free / {u.total / (1024**3):.1f} GB total ({u.percent}% used)"
                        )
                    except Exception:
                        pass
                self.last_output = "Live disk usage:\n" + ("\n".join(parts) or "No fixed drives readable.")
                return True

            # Default: top RAM & CPU processes
            procs = []
            for p in psutil.process_iter(["pid", "name", "memory_info", "cpu_percent"]):
                try:
                    mem_mb = (p.info["memory_info"].rss if p.info["memory_info"] else 0) / (1024 * 1024)
                    procs.append((mem_mb, p.info["name"], p.info["pid"]))
                except Exception:
                    pass
            procs.sort(reverse=True)
            top = "\n".join([f"- `{name}` (PID {pid}): {mem:.0f} MB RAM" for mem, name, pid in procs[:8]])
            self.last_output = f"Top memory-consuming processes right now:\n{top}"
            return True

        if intent_low == "run_command":
            for pat in BLOCKED_DANGEROUS_PATTERNS:
                if re.search(pat, raw, flags=re.IGNORECASE):
                    self.last_output = f"Blocked potentially destructive shell command: `{raw}`"
                    return False

            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", raw],
                creationflags=0x08000000,
                capture_output=True,
                text=True,
                timeout=20,
            )
            out = (res.stdout or res.stderr or "").strip()
            self.last_output = out[:2000] if out else f"Command exited with code {res.returncode}."
            return res.returncode == 0

        self.last_output = f"Unsupported terminal intent: {intent}"
        return False
