import time
import os
import shutil
import ctypes
import re
import datetime
from typing import Optional, Dict, Any, List
from backend.desktop.controllers.base_controller import AppController
from backend.core.logger import app_logger
import uiautomation as auto

def _ensure_desktop():
    try:
        user32 = ctypes.windll.user32
        h_default = user32.OpenDesktopW("Default", 0, False, 0x01FF)
        if h_default:
            user32.SetThreadDesktop(h_default)
    except Exception:
        pass

class FileExplorerController(AppController):
    """
    Dedicated controller for Windows File Explorer.
    Handles opening folders, navigating directory trees, organizing files, and file management via Explorer.
    """

    KNOWN_FOLDERS = {
        "downloads": os.path.expanduser(r"~\Downloads"),
        "documents": os.path.expanduser(r"~\Documents"),
        "desktop": os.path.expanduser(r"~\Desktop"),
        "pictures": os.path.expanduser(r"~\Pictures"),
        "screenshots": os.path.join(os.path.expanduser("~"), "OneDrive", "Pictures", "Screenshots") if os.path.exists(os.path.join(os.path.expanduser("~"), "OneDrive", "Pictures", "Screenshots")) else os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots"),
        "videos": os.path.expanduser(r"~\Videos"),
        "music": os.path.expanduser(r"~\Music"),
        "c": r"C:\\",
        "c drive": r"C:\\",
        "c:": r"C:\\",
        "d": r"D:\\",
        "d drive": r"D:\\",
        "d:": r"D:\\",
    }

    CATEGORIES = {
        "Documents": [
            ".pdf", ".docx", ".doc", ".txt", ".pptx", ".ppt", ".xlsx", ".xls",
            ".csv", ".odt", ".rtf", ".epub", ".md", ".tex"
        ],
        "Images": [
            ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".bmp", ".ico",
            ".tiff", ".psd", ".raw", ".ai"
        ],
        "Videos": [
            ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".3gp"
        ],
        "Audio": [
            ".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg", ".wma", ".opus"
        ],
        "Archives": [
            ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso", ".tgz"
        ],
        "Installers": [
            ".exe", ".msi", ".dmg", ".pkg", ".deb", ".apk"
        ],
        "Code": [
            ".py", ".js", ".ts", ".html", ".css", ".json", ".java", ".cpp",
            ".c", ".rs", ".go", ".sh", ".bat", ".ps1", ".sql", ".php"
        ]
    }

    def __init__(self):
        self.last_result: Optional[str] = None

    def _get_explorer_window(self) -> Optional[auto.WindowControl]:
        _ensure_desktop()
        root = auto.GetRootControl()
        for child in root.GetChildren():
            if child.ClassName == "CabinetWClass":
                return child
        return None

    def is_open(self) -> bool:
        return self._get_explorer_window() is not None

    def launch(self, path: Optional[str] = None):
        _ensure_desktop()
        target = path or "explorer.exe"
        if target.lower() in self.KNOWN_FOLDERS:
            target = self.KNOWN_FOLDERS[target.lower()]
        app_logger.info(f"Launching File Explorer for path: {target}")
        os.startfile(target)

    def wait_ready(self, timeout: int = 10) -> bool:
        _ensure_desktop()
        start = time.time()
        while time.time() - start < timeout:
            win = self._get_explorer_window()
            if win:
                return True
            time.sleep(0.5)
        return False

    def open_folder(self, folder_path: str) -> bool:
        _ensure_desktop()
        target = folder_path.strip().lower()
        resolved_path = self.KNOWN_FOLDERS.get(target, folder_path.strip())
        
        if not os.path.exists(resolved_path):
            app_logger.warning(f"Path does not exist: {resolved_path}, attempting to open raw query")
            
        try:
            os.startfile(resolved_path)
            time.sleep(1)
            return True
        except Exception as e:
            app_logger.error(f"Failed to open folder {resolved_path}: {e}")
            return False

    def _resolve_target_folder(self, folder_target: Optional[str]) -> str:
        """Smart folder path resolver aware of OneDrive redirection and direct user paths."""
        if not folder_target or not folder_target.strip() or folder_target.strip().lower() in ["any", "all", "auto"]:
            user_home = os.path.expanduser("~")
            onedrive_dt = os.path.join(user_home, "OneDrive", "Desktop")
            local_dt = os.path.join(user_home, "Desktop")
            dl = os.path.join(user_home, "Downloads")
            for dt in [onedrive_dt, local_dt]:
                if os.path.exists(dt):
                    files = [f for f in os.listdir(dt) if os.path.isfile(os.path.join(dt, f)) and not f.startswith(".") and f.lower() != "desktop.ini"]
                    if len(files) > 2:
                        return dt
            return dl

        raw = folder_target.strip().lower()
        clean = raw.replace("my ", "").replace(" folder", "").replace(" directory", "").strip()

        user_home = os.path.expanduser("~")
        candidates = {
            "screenshot": [
                os.path.join(user_home, "OneDrive", "Pictures", "Screenshots"),
                os.path.join(user_home, "Pictures", "Screenshots"),
                os.path.join(user_home, "OneDrive", "Screenshots"),
                os.path.join(user_home, "Screenshots")
            ],
            "desktop": [os.path.join(user_home, "OneDrive", "Desktop"), os.path.join(user_home, "Desktop")],
            "documents": [os.path.join(user_home, "OneDrive", "Documents"), os.path.join(user_home, "Documents")],
            "downloads": [os.path.join(user_home, "Downloads"), os.path.join(user_home, "OneDrive", "Downloads")],
            "pictures": [os.path.join(user_home, "OneDrive", "Pictures"), os.path.join(user_home, "Pictures")],
            "videos": [os.path.join(user_home, "Videos"), os.path.join(user_home, "OneDrive", "Videos")],
            "music": [os.path.join(user_home, "Music"), os.path.join(user_home, "OneDrive", "Music")]
        }

        for name, paths in candidates.items():
            if name in clean:
                for p in paths:
                    if os.path.exists(p):
                        return p

        if clean in self.KNOWN_FOLDERS:
            return self.KNOWN_FOLDERS[clean]

        if os.path.exists(folder_target.strip()):
            return folder_target.strip()

        return self.KNOWN_FOLDERS.get("downloads", os.path.expanduser(r"~\Downloads"))

    def organize_folder(self, folder_target: Optional[str] = None) -> bool:
        """
        Organizes files inside the specified folder into category subfolders
        (Documents, Images, Videos, Audio, Archives, Installers, Code, Other).
        Safe against collisions and ignores system/temporary files.
        """
        self.last_result = None
        folder_path = self._resolve_target_folder(folder_target)
        
        if not os.path.exists(folder_path):
            self.last_result = f"Error: Folder '{folder_path}' does not exist."
            app_logger.error(self.last_result)
            return False

        app_logger.info(f"[FileExplorer] Starting organization of: {folder_path}")
        
        # Inverted mapping: extension -> Category
        ext_to_cat: Dict[str, str] = {}
        for cat, exts in self.CATEGORIES.items():
            for ext in exts:
                ext_to_cat[ext.lower()] = cat

        system_files = {"desktop.ini", "thumbs.db", ".ds_store"}
        ignore_exts = {".crdownload", ".tmp", ".part", ".download"}

        moved_stats: Dict[str, int] = {}
        total_moved = 0

        try:
            entries = os.listdir(folder_path)
        except Exception as e:
            self.last_result = f"Failed to list folder contents: {e}"
            app_logger.error(self.last_result)
            return False

        is_screenshot_folder = (
            "screenshot" in folder_path.lower() or 
            (folder_target is not None and "screenshot" in folder_target.lower())
        )

        for item in entries:
            src = os.path.join(folder_path, item)
            
            # Skip if it is already a directory
            if os.path.isdir(src):
                continue
                
            # Skip system and hidden files
            if item.lower() in system_files or item.startswith("."):
                continue

            _, ext = os.path.splitext(item)
            ext_lower = ext.lower()

            if ext_lower in ignore_exts:
                continue

            if is_screenshot_folder:
                # Group screenshots by Month Year (e.g. "October 2026", "November 2026")
                category = "Other Screenshots"
                m = re.search(r'(\d{4})[-_](\d{2})', item)
                if m:
                    try:
                        category = datetime.date(int(m.group(1)), int(m.group(2)), 1).strftime("%B %Y")
                    except Exception:
                        pass
                if category == "Other Screenshots":
                    try:
                        mtime = os.path.getmtime(src)
                        category = datetime.datetime.fromtimestamp(mtime).strftime("%B %Y")
                    except Exception:
                        pass
            else:
                category = ext_to_cat.get(ext_lower, "Other")

            dest_dir = os.path.join(folder_path, category)
            os.makedirs(dest_dir, exist_ok=True)

            dest_file = os.path.join(dest_dir, item)
            # Safe collision rename
            if os.path.exists(dest_file):
                base_name, f_ext = os.path.splitext(item)
                counter = 1
                while os.path.exists(os.path.join(dest_dir, f"{base_name}_{counter}{f_ext}")):
                    counter += 1
                dest_file = os.path.join(dest_dir, f"{base_name}_{counter}{f_ext}")

            try:
                shutil.move(src, dest_file)
                moved_stats[category] = moved_stats.get(category, 0) + 1
                total_moved += 1
            except Exception as e:
                app_logger.warning(f"Could not move {item} to {dest_file}: {e}")

        folder_display = os.path.basename(folder_path.rstrip("\\/")) or folder_path
        if total_moved > 0:
            breakdown = ", ".join(f"{cnt} {cat}" for cat, cnt in sorted(moved_stats.items(), key=lambda x: -x[1]))
            self.last_result = (
                f"Done, Boss. I've organized {total_moved} files in your {folder_display} folder into {len(moved_stats)} categories: "
                f"{breakdown}."
            )
        else:
            self.last_result = f"Your {folder_display} folder is already organized, Boss. No loose files were found to sort."

        app_logger.info(f"[FileExplorer] {self.last_result}")
        return True

    def execute(self, intent: str, entity: Optional[str]) -> bool:
        _ensure_desktop()
        intent = intent.lower().strip()
        
        if intent in ["organize", "organize_folder", "sort_folder", "clean_folder"]:
            return self.organize_folder(entity)
            
        elif intent in ["open_app", "launch"]:
            self.launch()
            return True
            
        elif intent in ["open_folder", "navigate", "explore"] and entity:
            return self.open_folder(entity)
            
        elif intent == "close_app":
            win = self._get_explorer_window()
            if win:
                win.SendKeys("{Alt}{F4}")
                return True
                
        return False
