"""
Media & Wallpaper Controller for ADA.
Finds and downloads genuine high-resolution / 4K photos via silent backend search,
saves wallpapers to D:\ADA_Wallpapers (or Downloads\ADA_Wallpapers fallback, never Pictures),
and optionally applies desktop wallpaper or provides exact PowerShell/CMD commands.
"""

import ctypes
import os
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Dict, Any
from backend.desktop.controllers.base_controller import AppController
from backend.core.logger import app_logger


def _find_local_subject_images(subject: str, limit: int = 4) -> List[str]:
    """Searches D:\\ADA_Wallpapers, D:\\Wallpaper, Downloads, and Pictures for images matching a subject."""
    search_roots = [
        r"D:\ADA_Wallpapers",
        r"D:\Wallpaper",
        os.path.join(os.path.expanduser("~"), "Downloads"),
        os.path.join(os.path.expanduser("~"), "Pictures"),
    ]
    tokens = [t for t in re.split(r"[^a-z0-9]+", subject.lower()) if len(t) >= 3 and t not in ("the", "and", "for", "4k")]
    matches: List[tuple] = []
    seen = set()

    for root_dir in search_roots:
        if not os.path.exists(root_dir):
            continue
        for cur, _, files in os.walk(root_dir):
            if "collages" in cur.lower():
                continue
            cur_low = cur.lower()
            for fname in files:
                if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue
                full = os.path.join(cur, fname)
                if full in seen:
                    continue
                hay = f"{cur_low} {fname.lower()}"
                # Match either full token or prefix/stem (e.g. "doom" matches "doomsday")
                score = sum(1 for tok in tokens if tok in hay)
                if score > 0:
                    seen.add(full)
                    size = os.path.getsize(full) if os.path.exists(full) else 0
                    matches.append((score, size, full))

    matches.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [m[2] for m in matches[:limit]]


class MediaWallpaperController(AppController):
    """Controller for searching, downloading, and applying 4K photos & wallpapers."""

    def __init__(self):
        self.last_output: Optional[str] = None
        self.last_file_path: Optional[str] = None
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

            # Convert .webp -> .jpg so Windows SystemParametersInfo / Wallpaper Registry works cleanly
            if ext == ".webp":
                try:
                    from PIL import Image
                    jpg_path = os.path.splitext(fpath)[0] + ".jpg"
                    with Image.open(fpath) as im:
                        im.convert("RGB").save(jpg_path, "JPEG", quality=95)
                    os.remove(fpath)
                    fpath = jpg_path
                except Exception:
                    pass

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

    def _resolve_target_dir(self, intent: str, slug: str) -> str:
        """Resolves destination folder: D:\\ADA_Wallpapers for wallpapers (fallback Downloads), Downloads\\Images for general photos."""
        intent_low = (intent or "").lower().strip()
        downloads_root = os.path.join(os.path.expanduser("~"), "Downloads")
        if "image" in intent_low and "wallpaper" not in intent_low:
            base = os.path.join(downloads_root, "Images")
        elif os.path.exists("D:\\"):
            base = r"D:\ADA_Wallpapers"
        else:
            base = os.path.join(downloads_root, "ADA_Wallpapers")
        target = os.path.join(base, slug)
        os.makedirs(target, exist_ok=True)
        return target

    def _download_for_subject(self, subject: str, limit: int = 3) -> List[str]:
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", f"{subject.lower()} 4k wallpaper").strip("_")[:40] or "wallpaper"
        dest_dir = self._resolve_target_dir("find_wallpaper", slug)
        candidates = self._search_high_res_images(f"{subject} 4k wallpaper", max_results=10)
        if not candidates:
            return []
        saved_paths: List[str] = []
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [
                pool.submit(self._download_single, item, dest_dir, slug, idx)
                for idx, item in enumerate(candidates[:7], 1)
            ]
            for fut in as_completed(futures):
                res = fut.result()
                if res and os.path.exists(res["path"]):
                    saved_paths.append(res["path"])
                if len(saved_paths) >= limit:
                    break
        return saved_paths

    def _create_collage(self, subjects_raw: str) -> Optional[Dict[str, Any]]:
        """
        Composes a 3840x2160 (4K) stylized asymmetric bento wallpaper collage from local
        downloaded photos across D:\\ADA_Wallpapers, D:\\Wallpaper, Downloads, and Pictures,
        fetching high-res photos for any missing subject automatically.
        """
        from PIL import Image, ImageOps, ImageFilter, ImageDraw, ImageEnhance

        raw_str = subjects_raw or ""
        is_borderless = bool(re.search(r"\b(?:borderless|no\s+borders?|without\s+borders?|seamless)\b|\[borderless\]", raw_str, re.IGNORECASE))
        clean_subj = re.sub(
            r"\[borderless\]|\b(?:create|make|build|generate|collage|college|with\s+no\s+borders?|without\s+borders?|no\s+borders?|borderless|seamless|like\s+proper|proper|prope|like|of|the|photos?|pictures?|pics?|images?|wallpapers?|using\s+paint|using\s+mspaint|in\s+paint|with\s+paint|for\s+my|together|with)\b",
            " ",
            raw_str,
            flags=re.IGNORECASE,
        )
        subjects = [s.strip() for s in re.split(r"\s*\|\s*|\s+and\s+|,", clean_subj) if s.strip()]
        if not subjects:
            subjects = ["tony stark", "dr doom"]

        subject_pools: List[List[str]] = []
        for subj in subjects[:3]:
            local_hits = _find_local_subject_images(subj, limit=6)
            if len(local_hits) < 3:
                fetched = self._download_for_subject(subj, limit=3)
                for fpath in fetched:
                    if fpath not in local_hits:
                        local_hits.append(fpath)
            if local_hits:
                subject_pools.append(local_hits)

        if not subject_pools:
            fallback = _find_local_subject_images("wallpaper", limit=6)
            if fallback:
                subject_pools.append(fallback)
            else:
                return None

        # Deduplicate left and right pools cleanly so every panel displays a distinct image
        used_paths: set = set()
        pool_left: List[str] = []
        for p in subject_pools[0]:
            if p not in used_paths:
                pool_left.append(p)
                used_paths.add(p)

        right_raw = subject_pools[1] if len(subject_pools) > 1 else subject_pools[0]
        pool_right: List[str] = []
        for p in right_raw:
            if p not in used_paths:
                pool_right.append(p)
                used_paths.add(p)

        # Top up from fallback wallpapers if a pool still has < 3 distinct files
        extra_pool = [p for p in (subject_pools[0] + right_raw + _find_local_subject_images("wallpaper", limit=12)) if p not in used_paths]
        while len(pool_left) < 3 and extra_pool:
            p = extra_pool.pop(0)
            pool_left.append(p)
            used_paths.add(p)
        while len(pool_right) < 3 and extra_pool:
            p = extra_pool.pop(0)
            pool_right.append(p)
            used_paths.add(p)

        def _pick(pool: List[str], idx: int) -> str:
            return pool[idx % len(pool)] if pool else pool_left[0]

        # Symmetric dual-side 4K layout: edge-to-edge zero borders when borderless=True, or framed bento cards
        if is_borderless:
            slot_specs = [
                (0, 0, 1920, 1200, _pick(pool_left, 0), None),
                (0, 1200, 960, 960, _pick(pool_left, 1), None),
                (960, 1200, 960, 960, _pick(pool_left, 2), None),
                (1920, 0, 1920, 1200, _pick(pool_right, 0), None),
                (1920, 1200, 960, 960, _pick(pool_right, 1), None),
                (2880, 1200, 960, 960, _pick(pool_right, 2), None),
            ]
        else:
            slot_specs = [
                (56, 56, 1840, 1180, _pick(pool_left, 0), (222, 74, 58)),
                (56, 1268, 904, 836, _pick(pool_left, 1), (225, 173, 66)),
                (992, 1268, 904, 836, _pick(pool_left, 2), (222, 74, 58)),
                (1944, 56, 1840, 1180, _pick(pool_right, 0), (52, 199, 118)),
                (1944, 1268, 904, 836, _pick(pool_right, 1), (138, 212, 168)),
                (2880, 1268, 904, 836, _pick(pool_right, 2), (52, 199, 118)),
            ]
        center_candidate = _pick(pool_right, 0)

        W, H = 3840, 2160
        if is_borderless:
            canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
            for x, y, pw, ph, img_path, _ in slot_specs:
                try:
                    with Image.open(img_path) as im:
                        tile = ImageOps.fit(im.convert("RGB"), (pw, ph), method=Image.Resampling.LANCZOS).convert("RGBA")
                        tile = ImageEnhance.Contrast(tile).enhance(1.06)
                        tile = ImageEnhance.Color(tile).enhance(1.08)
                        canvas.paste(tile, (x, y))
                except Exception:
                    continue
        else:
            try:
                with Image.open(center_candidate) as bg_src:
                    bg = ImageOps.fit(bg_src.convert("RGB"), (W, H), method=Image.Resampling.LANCZOS)
            except Exception:
                bg = Image.new("RGB", (W, H), (14, 16, 22))
            bg = bg.filter(ImageFilter.GaussianBlur(radius=46))
            bg = ImageEnhance.Brightness(bg).enhance(0.24)
            canvas = bg.convert("RGBA")

            # Subtle left warm crimson & right emerald radial mood wash
            glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            gdraw = ImageDraw.Draw(glow)
            gdraw.ellipse((-400, -200, 1800, 2200), fill=(180, 35, 35, 55))
            gdraw.ellipse((2000, -200, 4200, 2200), fill=(25, 145, 85, 55))
            glow = glow.filter(ImageFilter.GaussianBlur(radius=160))
            canvas = Image.alpha_composite(canvas, glow)

            radius = 30
            for x, y, pw, ph, img_path, accent_rgb in slot_specs:
                # Soft shadow layer
                shadow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                sdraw = ImageDraw.Draw(shadow_layer)
                sdraw.rounded_rectangle([x - 4, y + 10, x + pw + 4, y + ph + 14], radius=radius + 4, fill=(0, 0, 0, 175))
                shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=18))
                canvas = Image.alpha_composite(canvas, shadow_layer)

                try:
                    with Image.open(img_path) as im:
                        tile = ImageOps.fit(im.convert("RGB"), (pw, ph), method=Image.Resampling.LANCZOS).convert("RGBA")
                        tile = ImageEnhance.Contrast(tile).enhance(1.06)
                        tile = ImageEnhance.Color(tile).enhance(1.08)
                except Exception:
                    continue

                mask = Image.new("L", (pw, ph), 0)
                mdraw = ImageDraw.Draw(mask)
                mdraw.rounded_rectangle([0, 0, pw - 1, ph - 1], radius=radius, fill=255)

                framed = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
                framed.paste(tile, (0, 0), mask)

                # Metallic accent border
                bdraw = ImageDraw.Draw(framed)
                bdraw.rounded_rectangle([1, 1, pw - 2, ph - 2], radius=radius, outline=(*accent_rgb, 210), width=4)
                canvas.alpha_composite(framed, (x, y))

        slug = re.sub(r"[^a-zA-Z0-9]+", "_", "_".join(subjects).lower()).strip("_")[:45] or "ada"
        if is_borderless:
            slug = f"{slug}_borderless"
        if os.path.exists("D:\\"):
            out_dir = r"D:\ADA_Wallpapers\collages"
        else:
            out_dir = os.path.join(os.path.expanduser("~"), "Downloads", "ADA_Wallpapers", "collages")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{slug}_4k_collage.jpg")
        canvas.convert("RGB").save(out_path, "JPEG", quality=96, subsampling=0)

        used_files = list(dict.fromkeys([s[4] for s in slot_specs]))
        return {
            "path": out_path,
            "size_kb": round(os.path.getsize(out_path) / 1024),
            "used_files": used_files,
            "subjects": subjects,
        }

    def execute(self, intent: str, entity: Optional[str]) -> bool:
        app_logger.info(f"MediaWallpaperController executing intent='{intent}' entity='{entity}'")
        self.last_output = None
        self.last_file_path = None

        intent_low = (intent or "").lower().strip()
        if intent_low in ("create_collage", "make_collage"):
            result = self._create_collage(entity or "tony stark | dr doom")
            if not result:
                self.last_output = "I couldn't find enough photos to build the 4K collage right now, Boss."
                return False
            out_path = result["path"]
            self.last_file_path = out_path
            app_logger.info(f"Saved 4K collage at {out_path} ({result['size_kb']} KB) from {result['used_files']}")
            # Save a ready helper script beside the collage without cluttering voice/HUD response
            try:
                ps_file = os.path.join(os.path.dirname(out_path), "apply_collage_wallpaper.ps1")
                with open(ps_file, "w", encoding="utf-8") as pf:
                    pf.write(
                        "Add-Type -TypeDefinition 'using System.Runtime.InteropServices; public class W { "
                        '[DllImport("user32.dll", CharSet=CharSet.Auto)] public static extern int '
                        "SystemParametersInfo(int uAction, int uParam, string lpvParam, int fuWinIni); }'; "
                        f'[W]::SystemParametersInfo(20, 0, "{out_path}", 3)\n'
                    )
            except Exception:
                pass
            subjects_disp = " and ".join([s.title() for s in result["subjects"]])
            loc_phrase = "your D drive ADA Wallpapers collages folder" if out_path.startswith("D:\\") else "your Downloads collages folder"
            self.last_output = f"Done, Boss. I created your 4K {subjects_disp} collage wallpaper and saved it in {loc_phrase}. Should I open the file for you?"
            return True

        raw_topic = (entity or "4k wallpaper").strip()
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", raw_topic.lower()).strip("_")[:40] or "wallpaper"

        dest_dir = self._resolve_target_dir(intent, slug)

        candidates = self._search_high_res_images(raw_topic, max_results=12)
        if not candidates:
            self.last_output = f"Could not find downloadable high-res images for '{raw_topic}' right now."
            return False

        saved: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [
                pool.submit(self._download_single, item, dest_dir, slug, idx)
                for idx, item in enumerate(candidates[:8], 1)
            ]
            for fut in as_completed(futures):
                res = fut.result()
                if res:
                    saved.append(res)
                if len(saved) >= 3:
                    break

        if not saved:
            self.last_output = f"I found high-resolution links for {raw_topic}, though direct downloads were blocked by the host."
            return True

        # Prefer .jpg / .png for native Windows wallpaper compatibility
        saved.sort(key=lambda s: (0 if s["path"].lower().endswith((".jpg", ".jpeg", ".png")) else 1))
        primary = saved[0]["path"]
        self.last_file_path = primary
        app_logger.info(f"Saved {len(saved)} photos to {dest_dir}; primary={primary}")

        try:
            ps_file = os.path.join(dest_dir, "apply_wallpaper.ps1")
            with open(ps_file, "w", encoding="utf-8") as pf:
                pf.write(
                    "Add-Type -TypeDefinition 'using System.Runtime.InteropServices; public class W { "
                    '[DllImport("user32.dll", CharSet=CharSet.Auto)] public static extern int '
                    "SystemParametersInfo(int uAction, int uParam, string lpvParam, int fuWinIni); }'; "
                    f'[W]::SystemParametersInfo(20, 0, "{primary}", 3)\n'
                )
        except Exception:
            pass

        topic_clean = re.sub(r"\b(?:4k|wallpaper)\b", "", raw_topic, flags=re.IGNORECASE).strip() or raw_topic
        loc_phrase = "your D drive ADA Wallpapers folder" if dest_dir.startswith("D:\\") else "your Downloads folder"

        if intent_low == "set_wallpaper" and self._apply_wallpaper(primary):
            self.last_output = f"Done, Boss. I downloaded and applied your new 4K {topic_clean} wallpaper. Should I open the file for you?"
        else:
            self.last_output = f"Done, Boss. I downloaded {len(saved)} high-resolution 4K {topic_clean} photos and saved them in {loc_phrase}. Should I open it for you?"
        return True
