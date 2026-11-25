"""
Media & Wallpaper Controller for ADA.
Finds and downloads genuine high-resolution / 4K photos via silent backend search,
saves them locally to Pictures/ADA_Wallpapers, and optionally applies desktop wallpaper
or provides exact PowerShell/CMD commands for immediate use.
"""

import ctypes
import os
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Dict, Any
from backend.desktop.controllers.base_controller import AppController
from backend.core.logger import app_logger


class MediaWallpaperController(AppController):
    """Controller for searching, downloading, and applying 4K photos & wallpapers."""

    def __init__(self):
        self.last_output: Optional[str] = None
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )

    def is_open(self) -> bool:
        return True

    def launch(self):
        pass

    def wait_ready(self, timeout: int = 10) -> bool:
        return True

    def _search_high_res_images(self, query: str, max_results: int = 12) -> List[Dict[str, Any]]:
        """Fetches direct high-res / 4K image candidates silently via DDGS."""
        from ddgs import DDGS

        search_q = query.strip()
        if "4k" not in search_q.lower():
            search_q = f"{search_q} 4k"
        if "wallpaper" not in search_q.lower():
            search_q = f"{search_q} wallpaper"

        candidates: List[Dict[str, Any]] = []
        with DDGS() as ddgs:
            try:
                candidates = list(ddgs.images(search_q, size="Wallpaper", max_results=max_results))
            except Exception as e:
                app_logger.warning(f"DDGS Wallpaper image query notice: {e}")
            if not candidates:
                try:
                    candidates = list(ddgs.images(search_q, size="Large", max_results=max_results))
                except Exception as e:
                    app_logger.warning(f"DDGS Large image query notice: {e}")

        # Prefer highest resolution images first (e.g. 3840x2160, 1920x1080)
        def _res_score(item: Dict[str, Any]) -> int:
            try:
                w = int(item.get("width") or 0)
                h = int(item.get("height") or 0)
                return w * h
            except Exception:
                return 0

        candidates.sort(key=_res_score, reverse=True)
        return candidates

    def _download_single(self, item: Dict[str, Any], dest_dir: str, slug: str, idx: int) -> Optional[Dict[str, Any]]:
        img_url = (item.get("image") or "").strip()
        if not img_url.startswith("http"):
            return None

        try:
            req = urllib.request.Request(
                img_url,
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
                    "Referer": "https://duckduckgo.com/",
                },
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                ctype = (resp.headers.get("Content-Type") or "").lower()
                if ctype and not ("image" in ctype or "octet-stream" in ctype):
                    return None
                data = resp.read(25 * 1024 * 1024)  # Cap at 25MB

            # Reject tiny thumbnails or HTML error pages
            if len(data) < 30 * 1024:
                return None

            ext = ".jpg"
            if "png" in ctype or img_url.lower().endswith(".png"):
                ext = ".png"
            elif "webp" in ctype or img_url.lower().endswith(".webp"):
                ext = ".webp"

            filename = f"{slug}_{idx}{ext}"
            fpath = os.path.join(dest_dir, filename)
            with open(fpath, "wb") as f:
                f.write(data)

            return {
                "path": fpath,
                "url": img_url,
                "width": item.get("width") or "?",
                "height": item.get("height") or "?",
                "size_kb": round(len(data) / 1024),
            }
        except Exception:
            return None

    def _apply_wallpaper(self, image_path: str) -> bool:
        """Applies desktop wallpaper immediately via Win32 SystemParametersInfoW."""
        try:
            abs_path = os.path.abspath(image_path)
            res = ctypes.windll.user32.SystemParametersInfoW(20, 0, abs_path, 3)
            return bool(res)
        except Exception as e:
            app_logger.warning(f"Wallpaper apply notice: {e}")
            return False

    def execute(self, intent: str, entity: Optional[str]) -> bool:
        app_logger.info(f"MediaWallpaperController executing intent='{intent}' entity='{entity}'")
        self.last_output = None

        raw_topic = (entity or "4k wallpaper").strip()
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", raw_topic.lower()).strip("_")[:40] or "wallpaper"

        pictures_dir = os.path.join(os.path.expanduser("~"), "Pictures", "ADA_Wallpapers", slug)
        os.makedirs(pictures_dir, exist_ok=True)

        candidates = self._search_high_res_images(raw_topic, max_results=12)
        if not candidates:
            self.last_output = f"Could not find downloadable high-res images for '{raw_topic}' right now."
            return False

        saved: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [
                pool.submit(self._download_single, item, pictures_dir, slug, idx)
                for idx, item in enumerate(candidates[:8], 1)
            ]
            for fut in as_completed(futures):
                res = fut.result()
                if res:
                    saved.append(res)
                if len(saved) >= 3:
                    break

        if not saved:
            top_urls = "\n".join([f"- {c.get('image')}" for c in candidates[:3] if c.get("image")])
            self.last_output = (
                f"Found high-res image links for '{raw_topic}', though direct hotlink downloads were blocked:\n{top_urls}"
            )
            return True

        primary = saved[0]["path"]
        applied_msg = ""
        if intent.lower().strip() == "set_wallpaper":
            if self._apply_wallpaper(primary):
                applied_msg = f"Applied `{os.path.basename(primary)}` as your desktop wallpaper, Boss.\n\n"

        files_summary = "\n".join(
            [f"- `{s['path']}` ({s['width']}x{s['height']}, {s['size_kb']} KB)" for s in saved]
        )
        ps_cmd = (
            "Add-Type -TypeDefinition 'using System.Runtime.InteropServices; public class W { "
            '[DllImport("user32.dll", CharSet=CharSet.Auto)] public static extern int '
            "SystemParametersInfo(int uAction, int uParam, string lpvParam, int fuWinIni); }'; "
            f'[W]::SystemParametersInfo(20, 0, "{primary}", 3)'
        )
        cmd_one_liner = (
            f'reg add "HKCU\\Control Panel\\Desktop" /v Wallpaper /t REG_SZ /d "{primary}" /f && '
            f'RUNDLL32.EXE user32.dll,UpdatePerUserSystemParameters ,1 ,True'
        )

        self.last_output = (
            f"{applied_msg}"
            f"Downloaded {len(saved)} high-resolution 4K photos for '{raw_topic}' into `{pictures_dir}`:\n"
            f"{files_summary}\n\n"
            f"PowerShell wallpaper command:\n```powershell\n{ps_cmd}\n```\n"
            f"CMD wallpaper command:\n```cmd\n{cmd_one_liner}\n```"
        )
        return True
