"""
ADA Cloudflare Secure Remote Tunnel Manager
Allows your POCO phone (or any mobile device) to connect to ADA from anywhere in the world
over encrypted HTTPS without port forwarding or static IP.
"""

import os
import re
import sys
import time
import subprocess
import threading
from typing import Optional, Dict, Any
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from backend.core.logger import app_logger

router = APIRouter(prefix="/api/cloud", tags=["cloud"])

class CloudflareTunnelManager:
    _instance: Optional["CloudflareTunnelManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_manager()
        return cls._instance

    def _init_manager(self):
        self.process: Optional[subprocess.Popen] = None
        self.public_url: Optional[str] = None
        self.is_running: bool = False
        self.started_at: Optional[float] = None
        self._lock = threading.Lock()
        
        # Locate cloudflared binary
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.binary_path = os.path.join(root_dir, "backend", "cloud", "bin", "cloudflared.exe")

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            # Check if process died
            if self.process and self.process.poll() is not None:
                self.is_running = False
                self.public_url = None
                self.process = None

            return {
                "active": self.is_running,
                "public_url": self.public_url,
                "mobile_app_url": f"{self.public_url}/mobile" if self.public_url else None,
                "touchpad_url": f"{self.public_url}/touchpad" if self.public_url else None,
                "started_at": self.started_at,
                "uptime_seconds": round(time.time() - self.started_at, 1) if (self.is_running and self.started_at) else 0,
                "binary_installed": os.path.exists(self.binary_path)
            }

    def start_tunnel(self, port: int = 8000, timeout: int = 25) -> Optional[str]:
        with self._lock:
            if self.is_running and self.public_url:
                return self.public_url

            if not os.path.exists(self.binary_path):
                app_logger.error(f"[CloudflareTunnel] Binary not found at {self.binary_path}")
                return None

            try:
                cmd = [
                    self.binary_path,
                    "tunnel",
                    "--url", f"http://127.0.0.1:{port}",
                    "--no-autoupdate"
                ]
                app_logger.info(f"[CloudflareTunnel] Starting tunnel: {' '.join(cmd)}")
                
                # Cloudflare outputs the trycloudflare URL to stderr
                creationflags = 0x08000000 if sys.platform == "win32" else 0
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    creationflags=creationflags
                )
                
                # Monitor stderr for the public URL
                url_found = None
                start_t = time.time()
                
                while time.time() - start_t < timeout:
                    if self.process.poll() is not None:
                        err = self.process.stderr.read()
                        app_logger.error(f"[CloudflareTunnel] Process terminated early: {err}")
                        return None
                        
                    line = self.process.stderr.readline()
                    if line:
                        match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
                        if match:
                            url_found = match.group(0)
                            app_logger.info(f"[CloudflareTunnel] Tunnel established! Public URL: {url_found}")
                            break
                    time.sleep(0.1)

                if url_found:
                    self.public_url = url_found
                    self.is_running = True
                    self.started_at = time.time()
                    
                    # Keep reading stderr in background daemon thread to avoid buffer overflow
                    def _drain(proc):
                        try:
                            for _ in proc.stderr:
                                pass
                        except Exception:
                            pass
                    t = threading.Thread(target=_drain, args=(self.process,), daemon=True)
                    t.start()
                    
                    return self.public_url
                else:
                    app_logger.warning("[CloudflareTunnel] Timed out waiting for trycloudflare URL")
                    if self.process:
                        self.process.terminate()
                    return None

            except Exception as e:
                app_logger.error(f"[CloudflareTunnel] Error launching tunnel: {e}")
                return None

    def stop_tunnel(self) -> bool:
        with self._lock:
            if self.process:
                try:
                    self.process.terminate()
                    self.process.wait(timeout=3)
                except Exception:
                    self.process.kill()
            self.process = None
            self.is_running = False
            self.public_url = None
            self.started_at = None
            app_logger.info("[CloudflareTunnel] Tunnel stopped.")
            return True

tunnel_manager = CloudflareTunnelManager()

@router.get("/tunnel/status")
async def get_tunnel_status():
    return tunnel_manager.get_status()

@router.post("/tunnel/start")
async def start_tunnel_endpoint():
    url = tunnel_manager.start_tunnel()
    if url:
        return {"status": "SUCCESS", "public_url": url, "mobile_app_url": f"{url}/mobile"}
    return JSONResponse(status_code=500, content={"status": "ERROR", "message": "Failed to start tunnel or timeout."})

@router.post("/tunnel/stop")
async def stop_tunnel_endpoint():
    tunnel_manager.stop_tunnel()
    return {"status": "SUCCESS", "message": "Tunnel stopped."}


STATIC_MOBILE_HTML_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "static", "mobile.html"))

@router.get("/mobile", response_class=HTMLResponse)
async def get_mobile_hub():
    if os.path.exists(STATIC_MOBILE_HTML_PATH):
        with open(STATIC_MOBILE_HTML_PATH, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(status_code=404, content="<h1>Mobile hub template not found</h1>")
