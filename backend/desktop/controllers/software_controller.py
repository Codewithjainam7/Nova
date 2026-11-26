"""
Software Installer & Download Controller for ADA.
Automates downloading and installing developer tools and desktop software
via Windows Package Manager (winget) and official vendor download portals.
"""

import os
import re
import shutil
import subprocess
import threading
import time
from typing import Optional, Dict, Any
from backend.desktop.controllers.base_controller import AppController
from backend.core.logger import app_logger

SOFTWARE_CATALOG: Dict[str, Dict[str, Any]] = {
    "android studio": {
        "name": "Android Studio",
        "winget_id": "Google.AndroidStudio",
        "url": "https://developer.android.com/studio",
        "version": "latest",
        "aliases": ["android studio", "andriod studio", "androidstudio", "android ide"]
    },
    "vs code": {
        "name": "Visual Studio Code",
        "winget_id": "Microsoft.VisualStudioCode",
        "url": "https://code.visualstudio.com",
        "version": "latest",
        "aliases": ["vs code", "vscode", "visual studio code"]
    },
    "git": {
        "name": "Git",
        "winget_id": "Git.Git",
        "url": "https://git-scm.com",
        "version": "latest",
        "aliases": ["git", "git scm"]
    },
    "nodejs": {
        "name": "Node.js (LTS)",
        "winget_id": "OpenJS.NodeJS.LTS",
        "url": "https://nodejs.org",
        "version": "LTS",
        "aliases": ["nodejs", "node.js", "node js", "node"]
    },
    "python": {
        "name": "Python 3.12",
        "winget_id": "Python.Python.3.12",
        "url": "https://python.org",
        "version": "3.12",
        "aliases": ["python", "python3"]
    },
    "flutter": {
        "name": "Flutter SDK",
        "winget_id": "Flutter.Flutter",
        "url": "https://flutter.dev",
        "version": "latest",
        "aliases": ["flutter", "flutter sdk"]
    },
    "docker": {
        "name": "Docker Desktop",
        "winget_id": "Docker.DockerDesktop",
        "url": "https://docker.com",
        "version": "latest",
        "aliases": ["docker", "docker desktop"]
    },
    "chrome": {
        "name": "Google Chrome",
        "winget_id": "Google.Chrome",
        "url": "https://google.com/chrome",
        "version": "latest",
        "aliases": ["chrome", "google chrome"]
    },
    "brave": {
        "name": "Brave Browser",
        "winget_id": "Brave.Brave",
        "url": "https://brave.com",
        "version": "latest",
        "aliases": ["brave", "brave browser"]
    }
}

class SoftwareInstallerController(AppController):
    """Controller for automating software package downloading and installation."""

    def __init__(self):
        self.last_output: Optional[str] = None

    def is_open(self) -> bool:
        return True

    def launch(self):
        pass

    def wait_ready(self, timeout: int = 10) -> bool:
        return True

    def _resolve_software(self, query: str) -> Optional[Dict[str, Any]]:
        q = (query or "").lower().strip()
        for key, info in SOFTWARE_CATALOG.items():
            for alias in info["aliases"]:
                if re.search(r'\b' + re.escape(alias) + r'\b', q):
                    return info
        return None

    def execute(self, intent: str, entity: Optional[str]) -> bool:
        app_logger.info(f"SoftwareInstallerController executing intent='{intent}' entity='{entity}'")
        self.last_output = None
        
        info = self._resolve_software(entity or intent)
        if not info:
            # Fallback: Treat entity as direct name
            target_name = (entity or "software").strip()
            winget_id = target_name
            url = f"https://www.google.com/search?q=download+{target_name}"
            info = {
                "name": target_name.title(),
                "winget_id": winget_id,
                "url": url,
                "version": "latest"
            }

        name = info["name"]
        winget_id = info["winget_id"]
        url = info["url"]

        has_winget = bool(shutil.which("winget"))
        
        # 1. Trigger winget background installation if winget is available
        if has_winget and winget_id:
            def _run_installer():
                try:
                    cflags = 0x08000000  # CREATE_NO_WINDOW
                    cmd = [
                        "winget", "install", "--id", winget_id,
                        "-e", "--accept-package-agreements", "--accept-source-agreements"
                    ]
                    app_logger.info(f"Starting background winget install: {' '.join(cmd)}")
                    subprocess.run(cmd, creationflags=cflags, capture_output=True, text=True, timeout=600)
                except Exception as ex:
                    app_logger.warning(f"Winget install notice for {name}: {ex}")

            threading.Thread(target=_run_installer, daemon=True).start()

        # 2. Launch official download portal in browser in the background
        if url:
            try:
                import win32gui, win32con
                c_fg = win32gui.GetForegroundWindow()
                cflags = 0x08000000
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 7  # SW_SHOWMINNOACTIVE
                chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                if os.path.exists(chrome_exe):
                    subprocess.Popen([chrome_exe, url], creationflags=cflags, startupinfo=startupinfo)
                else:
                    os.startfile(url)
                if c_fg:
                    def _restore_fg():
                        time.sleep(0.4)
                        try:
                            win32gui.SetForegroundWindow(c_fg)
                        except Exception:
                            pass
                    threading.Thread(target=_restore_fg, daemon=True).start()
            except Exception as e:
                app_logger.warning(f"Could not open official download URL: {e}")

        if has_winget:
            self.last_output = f"Started downloading and installing the latest {name} cleanly in the background, Boss."
        else:
            self.last_output = f"Opened the official download page for {name} in the background, Boss."

        return True
