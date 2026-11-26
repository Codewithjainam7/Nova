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

    def _recycle_files_silently(self, file_paths: List[str]) -> int:
        """Moves files silently to the Windows Recycle Bin (100% background, undoable)."""
        if not file_paths:
            return 0
        try:
            import ctypes
            from ctypes import wintypes

            class SHFILEOPSTRUCTW(ctypes.Structure):
                _fields_ = [
                    ("hwnd", wintypes.HWND),
                    ("wFunc", ctypes.c_uint),
                    ("pFrom", wintypes.LPCWSTR),
                    ("pTo", wintypes.LPCWSTR),
                    ("fFlags", ctypes.c_uint16),
                    ("fAnyOperationsAborted", wintypes.BOOL),
                    ("hNameMappings", ctypes.c_void_p),
                    ("lpszProgressTitle", wintypes.LPCWSTR),
                ]

            FO_DELETE = 3
            FOF_SILENT = 0x0004
            FOF_NOCONFIRMATION = 0x0010
            FOF_ALLOWUNDO = 0x0040
            FOF_NOERRORUI = 0x0400

            # Batch in chunks of 100 to avoid command string limits
            deleted_count = 0
            for i in range(0, len(file_paths), 100):
                chunk = [os.path.abspath(p) for p in file_paths[i : i + 100] if os.path.exists(p)]
                if not chunk:
                    continue
                p_from = "\0".join(chunk) + "\0\0"
                op = SHFILEOPSTRUCTW(
                    hwnd=None,
                    wFunc=FO_DELETE,
                    pFrom=p_from,
                    pTo=None,
                    fFlags=FOF_SILENT | FOF_NOCONFIRMATION | FOF_ALLOWUNDO | FOF_NOERRORUI,
                    fAnyOperationsAborted=False,
                    hNameMappings=None,
                    lpszProgressTitle=None,
                )
                rc = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
                if rc == 0 and not op.fAnyOperationsAborted:
                    deleted_count += len(chunk)
                else:
                    for p in chunk:
                        if not os.path.exists(p):
                            deleted_count += 1
            return deleted_count
        except Exception as e:
            app_logger.warning(f"SHFileOperationW Recycle fallback to os.remove: {e}")
            count = 0
            for p in file_paths:
                try:
                    os.remove(p)
                    count += 1
                except Exception:
                    pass
            return count

    def delete_files(self, spec: Optional[str] = None) -> bool:
        """
        Safely deletes (moves to Recycle Bin) filtered files in the background without opening Explorer.
        Supports month filters (e.g. 'November', 'October'), extensions ('.png', '.pdf'), and folder targets.
        """
        self.last_result = None
        raw = (spec or "").strip()
        low = raw.lower()

        # Determine folder target cleanly
        if "screenshot" in low:
            folder_target = "screenshots"
        elif "download" in low:
            folder_target = "downloads"
        elif "desktop" in low:
            folder_target = "desktop"
        elif "document" in low:
            folder_target = "documents"
        elif "picture" in low:
            folder_target = "pictures"
        else:
            m_path = re.search(r"([a-zA-Z]:\\[^\"\'\r\n<>|?*]+)", raw)
            folder_target = m_path.group(1).strip() if m_path else "downloads"

        folder_path = self._resolve_target_folder(folder_target)
        if not os.path.exists(folder_path):
            self.last_result = f"I couldn't find the {folder_target} folder, Boss."
            return False

        # Protect critical OS/root locations from blanket deletes
        norm_low = os.path.normpath(folder_path).lower()
        if norm_low in ("c:\\", "d:\\") or "\\windows" in norm_low or "\\system32" in norm_low:
            self.last_result = "Blocked file deletion in protected root or system directories."
            return False

        month_map = {
            "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
            "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6,
            "july": 7, "jul": 7, "august": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9,
            "october": 10, "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12,
        }
        target_month = None
        target_month_name = None
        now = datetime.datetime.now()
        if "this month" in low:
            target_month = now.month
            target_month_name = now.strftime("%B")
        elif "last month" in low or "previous month" in low:
            target_month = 12 if now.month == 1 else now.month - 1
            target_month_name = datetime.date(2026, target_month, 1).strftime("%B")
        else:
            for m_kw, m_num in month_map.items():
                if re.search(r"\b" + m_kw + r"\b", low):
                    target_month = m_num
                    target_month_name = datetime.date(2026, m_num, 1).strftime("%B")
                    break

        year_match = re.search(r"\b(20\d{2})\b", low)
        target_year = int(year_match.group(1)) if year_match else None

        ext_matches = re.findall(r"\.(png|jpg|jpeg|webp|pdf|docx|txt|zip|mp4|tmp|log)\b", low)
        target_exts = {f".{e}" for e in ext_matches}
        if not target_exts and "screenshot" in low:
            target_exts = {".png", ".jpg", ".jpeg", ".webp"}

        system_files = {"desktop.ini", "thumbs.db", ".ds_store"}
        matched_paths: List[str] = []
        candidate_dirs: List[str] = []

        for cur_root, _, files in os.walk(folder_path):
            if cur_root != folder_path:
                candidate_dirs.append(cur_root)
            rel_dir_low = os.path.relpath(cur_root, folder_path).lower()
            for fname in files:
                if fname.lower() in system_files or fname.startswith("."):
                    continue
                full = os.path.join(cur_root, fname)
                _, ext = os.path.splitext(fname)
                if target_exts and ext.lower() not in target_exts:
                    continue

                if target_month is not None:
                    matched_date = False
                    has_explicit_month = False
                    # 1. Check filename date e.g. Screenshot 2026-11-26
                    dm = re.search(r"(20\d{2})[-_](\d{2})", fname)
                    if dm:
                        has_explicit_month = True
                        f_y, f_m = int(dm.group(1)), int(dm.group(2))
                        if f_m == target_month and (target_year is None or f_y == target_year):
                            matched_date = True
                    # 2. Check organized month folder name e.g. "November 2026"
                    folder_months = [mk for mk in month_map if len(mk) > 3 and re.search(r"\b" + mk + r"\b", rel_dir_low)]
                    if folder_months:
                        has_explicit_month = True
                        if not matched_date and target_month_name and target_month_name.lower() in rel_dir_low:
                            if target_year is None or str(target_year) in rel_dir_low:
                                matched_date = True
                    # 3. Fallback to modified timestamp ONLY if neither filename nor subfolder specifies a month
                    if not has_explicit_month and not matched_date:
                        try:
                            mt = datetime.datetime.fromtimestamp(os.path.getmtime(full))
                            if mt.month == target_month and (target_year is None or mt.year == target_year):
                                matched_date = True
                        except Exception:
                            pass
                    if not matched_date:
                        continue

                matched_paths.append(full)

        folder_label = os.path.basename(folder_path.rstrip("\\/")) or folder_target
        if not matched_paths:
            month_txt = f"{target_month_name} " if target_month_name else ""
            self.last_result = f"No {month_txt}files were found to delete in your {folder_label} folder, Boss."
            app_logger.info(f"[FileExplorer] {self.last_result}")
            return True

        deleted = self._recycle_files_silently(matched_paths)
        # Clean up emptied month subfolders cleanly
        for d in sorted(candidate_dirs, reverse=True):
            try:
                if os.path.exists(d) and not os.listdir(d):
                    os.rmdir(d)
            except Exception:
                pass

        month_txt = f"{target_month_name} " if target_month_name else ""
        self.last_result = (
            f"Done, Boss. Moved {deleted} {month_txt}files from your {folder_label} folder to the Recycle Bin."
        )
        app_logger.info(f"[FileExplorer] {self.last_result}")
        return True

    def execute(self, intent: str, entity: Optional[str]) -> bool:
        _ensure_desktop()
        intent = intent.lower().strip()
        
        if intent in ["organize", "organize_folder", "sort_folder", "clean_folder"]:
            return self.organize_folder(entity)

        elif intent in ["delete_files", "delete_file", "delete_screenshots", "remove_files", "clear_files", "delete", "remove"]:
            return self.delete_files(entity)
            
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
