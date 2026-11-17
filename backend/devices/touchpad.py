import ctypes
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import subprocess
import os

router = APIRouter()

# Windows User32 mouse event flags
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_WHEEL = 0x0800

def move_mouse(dx: int, dy: int):
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE, int(dx), int(dy), 0, 0)

def left_click():
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def right_click():
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)

def scroll_mouse(delta_y: int):
    # Wheel delta (positive = up, negative = down)
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, int(delta_y * 120), 0)

@router.websocket("/ws/touchpad")
async def touchpad_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            action = msg.get("action")
            
            if action == "move":
                dx = msg.get("dx", 0)
                dy = msg.get("dy", 0)
                # Apply smooth velocity curve
                speed = (dx * dx + dy * dy) ** 0.5
                accel = 1.0 + min(2.5, speed * 0.08)
                move_mouse(int(dx * accel), int(dy * accel))
                
            elif action == "click":
                btn = msg.get("button", "left")
                if btn == "left":
                    left_click()
                elif btn == "right":
                    right_click()
                    
            elif action == "scroll":
                dy = msg.get("dy", 0)
                scroll_mouse(-int(dy))
                
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

@router.get("/touchpad", response_class=HTMLResponse)
async def get_touchpad_page():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>ADA Wireless Touchpad</title>
  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      user-select: none;
      -webkit-user-select: none;
      -webkit-touch-callout: none;
    }
    body {
      background: #090a0f;
      color: #fff;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      overflow: hidden;
      height: 100vh;
      width: 100vw;
      display: flex;
      flex-direction: column;
      touch-action: none;
    }
    /* Header */
    .header {
      padding: 12px 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      background: rgba(20, 20, 28, 0.7);
      backdrop-filter: blur(16px);
      z-index: 10;
    }
    .header .title {
      font-size: 13px;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 6px;
      letter-spacing: 0.5px;
    }
    .header .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #22d3ee;
      box-shadow: 0 0 8px #22d3ee;
    }
    .header .status {
      font-size: 11px;
      color: #94a3b8;
      font-family: monospace;
    }
    /* Main Touchpad Canvas */
    .touch-area {
      flex: 1;
      position: relative;
      background: radial-gradient(circle at center, rgba(34, 211, 238, 0.03) 0%, transparent 70%);
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .touch-hint {
      color: rgba(255, 255, 255, 0.2);
      font-size: 12px;
      letter-spacing: 1px;
      text-transform: uppercase;
      pointer-events: none;
      font-weight: 500;
    }
    /* Dedicated Right Scroll Strip */
    .scroll-strip {
      position: absolute;
      right: 0;
      top: 0;
      bottom: 0;
      width: 48px;
      border-left: 1px dashed rgba(255, 255, 255, 0.08);
      background: rgba(255, 255, 255, 0.02);
      display: flex;
      align-items: center;
      justify-content: center;
      color: rgba(255, 255, 255, 0.3);
      font-size: 10px;
      writing-mode: vertical-rl;
      letter-spacing: 2px;
    }
    /* Bottom Mouse Buttons */
    .button-bar {
      height: 70px;
      display: flex;
      gap: 1px;
      background: rgba(255, 255, 255, 0.06);
      border-top: 1px solid rgba(255, 255, 255, 0.08);
    }
    .btn {
      flex: 1;
      background: #10121a;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 13px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.7);
      transition: background 0.1s;
    }
    .btn:active {
      background: #22d3ee;
      color: #000;
    }
  </style>
</head>
<body>
  <div class="header">
    <div class="title">
      <div class="dot" id="statusDot"></div>
      ADA WIRELESS TRACKPAD
    </div>
    <div class="status" id="statusText">CONNECTING...</div>
  </div>

  <div class="touch-area" id="touchArea">
    <div class="touch-hint">Slide finger to move • Tap to click</div>
    <div class="scroll-strip" id="scrollStrip">SCROLL</div>
  </div>

  <div class="button-bar">
    <div class="btn" id="leftBtn">LEFT CLICK</div>
    <div class="btn" id="rightBtn">RIGHT CLICK</div>
  </div>

  <script>
    let ws = null;
    const host = window.location.host;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    
    function connect() {
      ws = new WebSocket(`${protocol}//${host}/ws/touchpad`);
      const statusText = document.getElementById('statusText');
      const statusDot = document.getElementById('statusDot');

      ws.onopen = () => {
        statusText.textContent = "CONNECTED (0ms)";
        statusText.style.color = "#4ade80";
        statusDot.style.background = "#4ade80";
        statusDot.style.boxShadow = "0 0 8px #4ade80";
      };

      ws.onclose = () => {
        statusText.textContent = "DISCONNECTED";
        statusText.style.color = "#f87171";
        statusDot.style.background = "#f87171";
        statusDot.style.boxShadow = "0 0 8px #f87171";
        setTimeout(connect, 2000);
      };
    }
    connect();

    // Touchpad Gestures
    const touchArea = document.getElementById('touchArea');
    const scrollStrip = document.getElementById('scrollStrip');
    
    let lastX = 0;
    let lastY = 0;
    let touchStartTime = 0;
    let hasMoved = false;

    touchArea.addEventListener('touchstart', (e) => {
      if (e.target === scrollStrip) return;
      const touch = e.touches[0];
      lastX = touch.clientX;
      lastY = touch.clientY;
      touchStartTime = Date.now();
      hasMoved = false;
    }, { passive: false });

    touchArea.addEventListener('touchmove', (e) => {
      if (e.target === scrollStrip) return;
      e.preventDefault();
      const touch = e.touches[0];
      const dx = touch.clientX - lastX;
      const dy = touch.clientY - lastY;

      if (Math.abs(dx) > 1 || Math.abs(dy) > 1) {
        hasMoved = true;
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ action: 'move', dx: dx * 1.8, dy: dy * 1.8 }));
        }
      }
      lastX = touch.clientX;
      lastY = touch.clientY;
    }, { passive: false });

    touchArea.addEventListener('touchend', (e) => {
      if (e.target === scrollStrip) return;
      const touchDuration = Date.now() - touchStartTime;
      // Tap detection (under 220ms without substantial move = Click)
      if (!hasMoved && touchDuration < 220) {
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ action: 'click', button: 'left' }));
          if (navigator.vibrate) navigator.vibrate(15);
        }
      }
    });

    // Scroll Strip
    let lastScrollY = 0;
    scrollStrip.addEventListener('touchstart', (e) => {
      lastScrollY = e.touches[0].clientY;
    }, { passive: false });

    scrollStrip.addEventListener('touchmove', (e) => {
      e.preventDefault();
      const currentY = e.touches[0].clientY;
      const deltaY = currentY - lastScrollY;
      if (Math.abs(deltaY) > 3) {
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ action: 'scroll', dy: deltaY > 0 ? -1 : 1 }));
        }
        lastScrollY = currentY;
      }
    }, { passive: false });

    // Hardware Mouse Buttons
    document.getElementById('leftBtn').addEventListener('click', () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'click', button: 'left' }));
        if (navigator.vibrate) navigator.vibrate(20);
      }
    });

    document.getElementById('rightBtn').addEventListener('click', () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'click', button: 'right' }));
        if (navigator.vibrate) navigator.vibrate(25);
      }
    });
  </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)

@router.post("/api/devices/touchpad/launch")
async def launch_touchpad_on_phone():
    """Wakes phone and launches full-screen wireless touchpad via ADB."""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    adb_path = os.path.join(project_root, "platform-tools", "adb.exe")
    target = "192.168.0.101:5555"
    laptop_ip = "192.168.0.104"
    touchpad_url = f"http://{laptop_ip}:8000/touchpad"

    try:
        # Wake screen
        subprocess.run([adb_path, "-s", target, "shell", "input", "keyevent", "224"], timeout=2)
        # Launch browser to touchpad URL
        subprocess.run([
            adb_path, "-s", target, "shell", "am", "start",
            "-a", "android.intent.action.VIEW",
            "-d", touchpad_url
        ], timeout=3)
        return {"status": "SUCCESS", "url": touchpad_url}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}
