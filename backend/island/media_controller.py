import asyncio
import base64
import os
import datetime
from typing import Optional, Dict, Any
from backend.core.logger import app_logger

try:
    import winsdk.windows.media.control as wmc
    import winsdk.windows.storage.streams as streams
    WINSDK_AVAILABLE = True
except ImportError:
    WINSDK_AVAILABLE = False
    app_logger.warning("[MediaController] winsdk not installed; media detection disabled.")

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

class SystemMediaController:
    """
    Global Windows Media Transport Controller for ADA Dynamic Island.
    Extracts real-time now-playing song title, artist, album art thumbnail,
    duration, and playback status from Spotify, YouTube, Chrome, Edge, and media players.
    """

    def __init__(self):
        self._cached_thumb: Optional[str] = None
        self._cached_track_key: Optional[str] = None
        self._last_media_info: Optional[Dict[str, Any]] = None

    async def get_current_media(self) -> Optional[Dict[str, Any]]:
        if not WINSDK_AVAILABLE:
            return None

        try:
            manager = await wmc.GlobalSystemMediaTransportControlsSessionManager.request_async()
            sessions = manager.get_sessions()
            curr = manager.get_current_session()
            if not curr and sessions and len(sessions) > 0:
                curr = sessions[0]

            if not curr:
                self._last_media_info = None
                return None

            info = curr.get_playback_info()
            status_num = info.playback_status if info else 0
            status_map = {4: "playing", 5: "paused", 3: "stopped", 2: "changing", 1: "opened", 0: "closed"}
            status = status_map.get(status_num, "idle")

            # We show active media if it's playing or paused
            if status not in ["playing", "paused"]:
                self._last_media_info = None
                return None

            props = await curr.try_get_media_properties_async()
            if not props or not props.title:
                return None

            title = props.title.strip()
            artist = (props.artist or "").strip()
            album = (props.album_title or "").strip()
            track_key = f"{title}::{artist}"

            # Cached thumbnail extraction
            thumbnail_url = None
            if track_key == self._cached_track_key and self._cached_thumb:
                thumbnail_url = self._cached_thumb
            elif props.thumbnail:
                try:
                    stream = await props.thumbnail.open_read_async()
                    if stream.size > 0:
                        reader = streams.DataReader(stream)
                        await reader.load_async(stream.size)
                        buf = bytearray(stream.size)
                        reader.read_bytes(buf)
                        b64_str = base64.b64encode(buf).decode("ascii")
                        thumbnail_url = f"data:image/jpeg;base64,{b64_str}"
                        self._cached_thumb = thumbnail_url
                        self._cached_track_key = track_key
                except Exception as e:
                    app_logger.debug(f"[MediaController] Thumbnail load notice: {e}")

            # Timeline properties (Real-time GSMTC calculation)
            pos = 0.0
            dur = 0.0
            try:
                tl = curr.get_timeline_properties()
                if tl:
                    base_pos = tl.position.total_seconds() if tl.position else 0.0
                    dur = tl.end_time.total_seconds() if tl.end_time else 0.0
                    if status == "playing" and tl.last_updated_time:
                        now_utc = datetime.datetime.now(datetime.timezone.utc)
                        delta = (now_utc - tl.last_updated_time).total_seconds()
                        if 0 <= delta <= (dur if dur > 0 else 7200):
                            base_pos += delta
                    pos = min(dur, base_pos) if dur > 0 else base_pos
            except Exception as e:
                app_logger.debug(f"[MediaController] Timeline calc notice: {e}")

            app_id = curr.source_app_user_model_id or ""
            clean_app = app_id.split("!")[0].split(".exe")[0].split("\\")[-1]
            if not clean_app:
                clean_app = "Media Player"

            data = {
                "title": title,
                "artist": artist if artist else "Unknown Artist",
                "album": album,
                "status": status,
                "app": clean_app,
                "position": round(pos, 1),
                "duration": round(dur, 1),
                "thumbnail": thumbnail_url
            }
            self._last_media_info = data
            return data
        except Exception as e:
            app_logger.debug(f"[MediaController] Query error: {e}")
            return self._last_media_info

    async def toggle_play_pause(self) -> bool:
        if WINSDK_AVAILABLE:
            try:
                manager = await wmc.GlobalSystemMediaTransportControlsSessionManager.request_async()
                curr = manager.get_current_session()
                if curr:
                    success = await curr.try_toggle_play_pause_async()
                    if success:
                        return True
            except Exception as e:
                app_logger.warning(f"[MediaController] WinRT toggle play/pause notice: {e}")

        if PYAUTOGUI_AVAILABLE:
            try:
                pyautogui.press("playpause")
                return True
            except Exception:
                pass
        return False

    async def skip_next(self) -> bool:
        if WINSDK_AVAILABLE:
            try:
                manager = await wmc.GlobalSystemMediaTransportControlsSessionManager.request_async()
                curr = manager.get_current_session()
                if curr:
                    success = await curr.try_skip_next_async()
                    if success:
                        return True
            except Exception as e:
                app_logger.warning(f"[MediaController] WinRT skip next notice: {e}")

        if PYAUTOGUI_AVAILABLE:
            try:
                pyautogui.press("nexttrack")
                return True
            except Exception:
                pass
        return False

    async def skip_previous(self) -> bool:
        if WINSDK_AVAILABLE:
            try:
                manager = await wmc.GlobalSystemMediaTransportControlsSessionManager.request_async()
                curr = manager.get_current_session()
                if curr:
                    success = await curr.try_skip_previous_async()
                    if success:
                        return True
            except Exception as e:
                app_logger.warning(f"[MediaController] WinRT skip previous notice: {e}")

        if PYAUTOGUI_AVAILABLE:
            try:
                pyautogui.press("prevtrack")
                return True
            except Exception:
                pass
        return False

system_media_controller = SystemMediaController()
