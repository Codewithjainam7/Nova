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
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
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


@router.get("/mobile", response_class=HTMLResponse)
async def get_mobile_hub():
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <meta name="theme-color" content="#07080c">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <title>ADA Mobile OS</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
    body {
      background: #07080c;
      color: #f1f5f9;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      height: 100vh;
      width: 100vw;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    header {
      padding: 12px 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: #0d0f17;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      flex-shrink: 0;
    }
    .logo {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 700;
      font-size: 15px;
      letter-spacing: 0.5px;
    }
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #10b981;
      box-shadow: 0 0 8px #10b981;
      transition: all 0.3s;
    }
    .views-container {
      flex: 1;
      overflow: hidden;
      position: relative;
    }
    .view {
      position: absolute;
      top: 0; left: 0; width: 100%; height: 100%;
      display: none;
      flex-direction: column;
    }
    .view.active { display: flex; }
    
    /* Chat View */
    .chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      -webkit-overflow-scrolling: touch;
    }
    .msg {
      max-width: 85%;
      padding: 10px 14px;
      border-radius: 16px;
      font-size: 14px;
      line-height: 1.45;
      word-wrap: break-word;
    }
    .msg.user {
      align-self: flex-end;
      background: #2563eb;
      color: #fff;
      border-bottom-right-radius: 4px;
    }
    .msg.ada {
      align-self: flex-start;
      background: #151824;
      color: #e2e8f0;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-bottom-left-radius: 4px;
    }
    .chips-bar {
      display: flex;
      gap: 8px;
      overflow-x: auto;
      padding: 6px 12px;
      background: #090a10;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
      flex-shrink: 0;
      scrollbar-width: none;
    }
    .chips-bar::-webkit-scrollbar { display: none; }
    .chip {
      white-space: nowrap;
      padding: 6px 12px;
      background: rgba(255, 255, 255, 0.07);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 20px;
      font-size: 12px;
      color: #cbd5e1;
      cursor: pointer;
    }
    .chat-input-bar {
      padding: 8px 12px calc(8px + env(safe-area-inset-bottom, 0px));
      background: #0d0f17;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }
    .chat-input {
      flex: 1;
      padding: 10px 14px;
      background: #171a26;
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 24px;
      color: #fff;
      font-size: 14px;
      outline: none;
    }
    .chat-btn {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: #22d3ee;
      border: none;
      color: #000;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-weight: bold;
      flex-shrink: 0;
    }

    /* Controls HUD View */
    .controls-view {
      padding: 16px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .card {
      background: #111420;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 16px;
      padding: 16px;
    }
    .card-title {
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.5px;
      color: #94a3b8;
      margin-bottom: 12px;
      text-transform: uppercase;
    }
    .grid-stats {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }
    .stat-item {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.06);
      border-radius: 12px;
      padding: 10px;
    }
    .stat-label { font-size: 11px; color: #64748b; margin-bottom: 4px; }
    .stat-val { font-size: 18px; font-weight: 700; font-family: monospace; color: #38bdf8; }
    
    .slider-container { display: flex; align-items: center; gap: 12px; }
    .slider {
      flex: 1;
      accent-color: #22d3ee;
      height: 6px;
    }
    .btn-action {
      width: 100%;
      padding: 12px;
      border-radius: 12px;
      border: 1px solid rgba(255, 255, 255, 0.1);
      background: rgba(255, 255, 255, 0.06);
      color: #fff;
      font-weight: 600;
      font-size: 14px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }
    .btn-action:active { background: rgba(255, 255, 255, 0.15); }
    .btn-lock { background: rgba(239, 68, 68, 0.15); border-color: rgba(239, 68, 68, 0.3); color: #f87171; }

    /* Touchpad View iframe */
    .tp-frame {
      width: 100%;
      height: 100%;
      border: none;
    }

    /* Bottom Navigation Bar */
    nav {
      height: 56px;
      background: #090a10;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      display: flex;
      align-items: center;
      justify-content: space-around;
      flex-shrink: 0;
      padding-bottom: env(safe-area-inset-bottom, 0px);
    }
    .nav-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 3px;
      font-size: 11px;
      color: #64748b;
      cursor: pointer;
      background: none;
      border: none;
      padding: 6px 16px;
    }
    .nav-item.active { color: #22d3ee; }
    .nav-icon { width: 20px; height: 20px; fill: currentColor; }
  </style>
</head>
<body>
  <header>
    <div class="logo">
      <span class="status-dot"></span>
      <span>ADA MOBILE OS</span>
    </div>
    <div style="display: flex; align-items: center; gap: 8px;">
      <button id="voice-toggle-btn" onclick="toggleVoice()" style="background: rgba(34, 211, 238, 0.15); border: 1px solid rgba(34, 211, 238, 0.3); color: #22d3ee; font-size: 11px; font-weight: 600; padding: 4px 8px; border-radius: 12px; cursor: pointer;">
        🔊 Voice ON
      </button>
      <div style="font-size: 12px; color: #64748b; font-family: monospace;" id="time-display">--:--</div>
    </div>
  </header>

  <div class="views-container">
    <!-- VIEW 1: CHAT -->
    <div class="view active" id="view-chat">
      <div class="chat-messages" id="chat-msgs">
        <div class="msg ada">
          <div>Hello Boss! ADA is online on your phone via Cloudflare encrypted tunnel. Tap "Speak" or chat anytime!</div>
          <div style="margin-top: 6px;">
            <button onclick="playAdaVoice('Hello Boss! ADA is online on your phone via Cloudflare encrypted tunnel.')" style="background: rgba(34, 211, 238, 0.12); border: 1px solid rgba(34, 211, 238, 0.25); color: #22d3ee; border-radius: 8px; font-size: 11px; padding: 2px 8px; cursor: pointer;">
              🔊 Speak
            </button>
          </div>
        </div>
      </div>
      <div class="chips-bar">
        <div class="chip" onclick="quickSend('give me my morning briefing')">🌅 Briefing</div>
        <div class="chip" onclick="quickSend('lock my laptop')">🔒 Lock PC</div>
        <div class="chip" onclick="quickSend('what media is playing?')">🎵 Media</div>
        <div class="chip" onclick="quickSend('system telemetry status')">📊 Telemetry</div>
      </div>
      <div class="chat-input-bar">
        <button id="mic-btn" onclick="toggleMic()" style="width: 40px; height: 40px; border-radius: 50%; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.12); color: #cbd5e1; font-size: 18px; display: flex; align-items: center; justify-content: center; cursor: pointer; flex-shrink: 0;" title="Voice Input">
          🎙️
        </button>
        <input type="text" class="chat-input" id="chat-input" placeholder="Speak or type to ADA..." onkeydown="if(event.key==='Enter') sendMsg()">
        <button class="chat-btn" onclick="sendMsg()">➤</button>
      </div>
    </div>

    <!-- VIEW 2: TOUCHPAD -->
    <div class="view" id="view-touchpad">
      <iframe src="/touchpad" class="tp-frame" id="touchpad-iframe"></iframe>
    </div>

    <!-- VIEW 3: CONTROLS & TELEMETRY -->
    <div class="view" id="view-controls">
      <div class="controls-view">
        <div class="card">
          <div class="card-title">Windows Master Volume</div>
          <div class="slider-container">
            <span style="font-size: 16px;">🔊</span>
            <input type="range" class="slider" id="vol-slider" min="0" max="100" value="50" oninput="changeVol(this.value)">
            <span id="vol-label" style="font-family: monospace; width: 36px; text-align: right;">50%</span>
          </div>
        </div>

        <div class="card">
          <div class="card-title">Live Laptop Telemetry</div>
          <div class="grid-stats">
            <div class="stat-item"><div class="stat-label">CPU LOAD</div><div class="stat-val" id="stat-cpu">--%</div></div>
            <div class="stat-item"><div class="stat-label">RTX 3050 GPU</div><div class="stat-val" id="stat-gpu">--%</div></div>
            <div class="stat-item"><div class="stat-label">RAM USAGE</div><div class="stat-val" id="stat-ram">--%</div></div>
            <div class="stat-item"><div class="stat-label">BATTERY</div><div class="stat-val" id="stat-bat">--%</div></div>
          </div>
        </div>

        <div class="card">
          <div class="card-title">Quick Security Actions</div>
          <div style="display: flex; flex-direction: column; gap: 8px;">
            <button class="btn-action btn-lock" onclick="quickSend('lock my laptop')">🔒 Lock Laptop Immediately</button>
            <button class="btn-action" onclick="quickSend('organize my downloads folder')">📂 Tidy Downloads Folder</button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <nav>
    <button class="nav-item active" onclick="switchTab('chat')">
      <svg class="nav-icon" viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>
      <span>Chat</span>
    </button>
    <button class="nav-item" onclick="switchTab('touchpad')">
      <svg class="nav-icon" viewBox="0 0 24 24"><path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 14H4V6h16v12z"/></svg>
      <span>Touchpad</span>
    </button>
    <button class="nav-item" onclick="switchTab('controls')">
      <svg class="nav-icon" viewBox="0 0 24 24"><path d="M3 17v2h6v-2H3zM3 5v2h10V5H3zm10 16v-2h8v-2h-8v-2h-2v6h2zM7 9v2H3v2h4v2h2V9H7zm14 4v-2H11v2h10zm-6-4h2V7h4V5h-4V3h-2v6z"/></svg>
      <span>Laptop HUD</span>
    </button>
  </nav>

  <script>
    let isVoiceEnabled = true;
    let currentAudio = null;

    // Mobile audio policy unlock on first user tap
    window.addEventListener('touchstart', function unlockAudio() {
      const silent = new Audio('data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA');
      silent.play().catch(() => {});
      window.removeEventListener('touchstart', unlockAudio);
    }, { once: true });

    function updateClock() {
      const now = new Date();
      document.getElementById('time-display').innerText = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    setInterval(updateClock, 1000);
    updateClock();

    function switchTab(tab) {
      document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
      document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
      
      document.getElementById('view-' + tab).classList.add('active');
      const idx = tab === 'chat' ? 0 : tab === 'touchpad' ? 1 : 2;
      document.querySelectorAll('.nav-item')[idx].classList.add('active');
    }

    function toggleVoice() {
      isVoiceEnabled = !isVoiceEnabled;
      const btn = document.getElementById('voice-toggle-btn');
      btn.innerText = isVoiceEnabled ? '🔊 Voice ON' : '🔇 Muted';
      btn.style.color = isVoiceEnabled ? '#22d3ee' : '#64748b';
      btn.style.background = isVoiceEnabled ? 'rgba(34, 211, 238, 0.15)' : 'rgba(255, 255, 255, 0.05)';
      if (!isVoiceEnabled && currentAudio) {
        currentAudio.pause();
        currentAudio = null;
      }
    }

    function playAdaVoice(text) {
      if (!isVoiceEnabled || !text) return;
      try {
        if (currentAudio) {
          currentAudio.pause();
          currentAudio = null;
        }
        let clean = text;
        try { clean = decodeURIComponent(text); } catch {}
        clean = clean.replace(/[*#`_~]/g, '').replace(/\[(.*?)\]\(.*?\)/g, '$1').trim();
        if (!clean) return;

        const snippet = clean.length > 350 ? clean.slice(0, 350) : clean;
        const audioUrl = '/api/tts?text=' + encodeURIComponent(snippet);
        currentAudio = new Audio(audioUrl);

        const dot = document.querySelector('.status-dot');
        if (dot) {
          dot.style.background = '#22d3ee';
          dot.style.boxShadow = '0 0 14px #22d3ee';
        }

        currentAudio.onended = () => {
          if (dot) {
            dot.style.background = '#10b981';
            dot.style.boxShadow = '0 0 8px #10b981';
          }
          currentAudio = null;
        };
        currentAudio.onerror = (e) => {
          if (dot) {
            dot.style.background = '#10b981';
            dot.style.boxShadow = '0 0 8px #10b981';
          }
          currentAudio = null;
        };

        currentAudio.play().catch(e => console.log('Audio autoplay prevented:', e));
      } catch (err) {
        console.error('playAdaVoice exception:', err);
      }
    }

    // Speech-to-Text Recognition
    let recognition = null;
    let isListening = false;
    function toggleMic() {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) {
        alert('Voice input is not supported in this mobile browser. Please open in Google Chrome on Android.');
        return;
      }
      const micBtn = document.getElementById('mic-btn');

      if (isListening) {
        if (recognition) recognition.stop();
        isListening = false;
        micBtn.style.background = 'rgba(255, 255, 255, 0.08)';
        micBtn.style.color = '#cbd5e1';
        return;
      }

      recognition = new SpeechRecognition();
      recognition.lang = 'en-US';
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      recognition.onstart = () => {
        isListening = true;
        micBtn.style.background = '#ef4444';
        micBtn.style.color = '#fff';
      };

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        document.getElementById('chat-input').value = transcript;
        sendMsg();
      };

      recognition.onerror = () => {
        isListening = false;
        micBtn.style.background = 'rgba(255, 255, 255, 0.08)';
        micBtn.style.color = '#cbd5e1';
      };

      recognition.onend = () => {
        isListening = false;
        micBtn.style.background = 'rgba(255, 255, 255, 0.08)';
        micBtn.style.color = '#cbd5e1';
      };

      recognition.start();
    }

    async function sendMsg() {
      const input = document.getElementById('chat-input');
      const text = input.value.trim();
      if (!text) return;
      input.value = '';

      const msgs = document.getElementById('chat-msgs');
      const uDiv = document.createElement('div');
      uDiv.className = 'msg user';
      uDiv.innerText = text;
      msgs.appendChild(uDiv);

      const aDiv = document.createElement('div');
      aDiv.className = 'msg ada';
      aDiv.innerText = 'Thinking...';
      msgs.appendChild(aDiv);
      msgs.scrollTop = msgs.scrollHeight;

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text })
        });
        const data = await res.json();
        const reply = data.response || 'Task executed.';
        
        aDiv.innerHTML = `
          <div>${reply.replace(/\n/g, '<br>')}</div>
          <div style="margin-top: 6px;">
            <button onclick="playAdaVoice(this.getAttribute('data-text'))" data-text="${encodeURIComponent(reply)}" style="background: rgba(34, 211, 238, 0.12); border: 1px solid rgba(34, 211, 238, 0.25); color: #22d3ee; border-radius: 8px; font-size: 11px; padding: 2px 8px; cursor: pointer;">
              🔊 Speak
            </button>
          </div>
        `;
        playAdaVoice(reply);
      } catch (err) {
        aDiv.innerText = 'Connection error: ' + err.message;
      }
      msgs.scrollTop = msgs.scrollHeight;
    }

    function quickSend(cmd) {
      switchTab('chat');
      document.getElementById('chat-input').value = cmd;
      sendMsg();
    }

    async function changeVol(val) {
      document.getElementById('vol-label').innerText = val + '%';
      try {
        await fetch('/api/system/volume', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ level: parseInt(val) })
        });
      } catch {}
    }

    async function pollTelemetry() {
      try {
        const res = await fetch('/api/system/telemetry');
        if (res.ok) {
          const t = await res.json();
          if (t.cpu) document.getElementById('stat-cpu').innerText = Math.round(t.cpu.percent) + '%';
          if (t.gpu) document.getElementById('stat-gpu').innerText = Math.round(t.gpu.usage || t.gpu.percent || 0) + '%';
          if (t.ram) document.getElementById('stat-ram').innerText = Math.round(t.ram.percent) + '%';
          if (t.battery) document.getElementById('stat-bat').innerText = Math.round(t.battery.percent) + '%';
        }
      } catch {}
    }
    setInterval(pollTelemetry, 3000);
    pollTelemetry();
  </script>
</body>
</html>
"""
