import ctypes
import json
import os
import subprocess
import socket
import time
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

router = APIRouter()

# Windows User32 constants
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_HWHEEL = 0x1000

VK_LWIN = 0x5B
VK_TAB = 0x09
VK_D = 0x44
VK_MENU = 0x12  # Alt
VK_CONTROL = 0x11
VK_SHIFT = 0x10
KEYEVENTF_KEYUP = 0x0002

user32 = ctypes.windll.user32

# Global sub-pixel float accumulators to eliminate dead zone and lag
accum_dx = 0.0
accum_dy = 0.0
accum_scroll_y = 0.0
accum_scroll_x = 0.0

def move_mouse_accumulated(dx: float, dy: float, speed_mult: float = 1.0):
    global accum_dx, accum_dy
    raw_speed = (dx * dx + dy * dy) ** 0.5
    accel = 1.0 + min(2.5, raw_speed * 0.035)
    
    accum_dx += dx * speed_mult * accel
    accum_dy += dy * speed_mult * accel
    
    step_x = int(accum_dx)
    step_y = int(accum_dy)
    
    if step_x != 0 or step_y != 0:
        user32.mouse_event(MOUSEEVENTF_MOVE, step_x, step_y, 0, 0)
        accum_dx -= step_x
        accum_dy -= step_y

def left_click():
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.01)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def right_click():
    user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
    time.sleep(0.01)
    user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)

def middle_click():
    user32.mouse_event(MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
    time.sleep(0.01)
    user32.mouse_event(MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)

def scroll_mouse_accumulated(dy: float, dx: float = 0.0):
    global accum_scroll_y, accum_scroll_x
    # 1 scroll tick in Windows is 120 units
    accum_scroll_y += dy * 120.0
    accum_scroll_x += dx * 120.0
    
    step_y = int(accum_scroll_y)
    step_x = int(accum_scroll_x)
    
    if step_y != 0:
        user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, step_y, 0)
        accum_scroll_y -= step_y
    if step_x != 0:
        user32.mouse_event(MOUSEEVENTF_HWHEEL, 0, 0, step_x, 0)
        accum_scroll_x -= step_x

def zoom_mouse(delta: float):
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, int(delta * 120), 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

def execute_gesture(name: str):
    if name == "task_view":
        user32.keybd_event(VK_LWIN, 0, 0, 0)
        user32.keybd_event(VK_TAB, 0, 0, 0)
        time.sleep(0.035)
        user32.keybd_event(VK_TAB, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)
    elif name == "show_desktop":
        user32.keybd_event(VK_LWIN, 0, 0, 0)
        user32.keybd_event(VK_D, 0, 0, 0)
        time.sleep(0.035)
        user32.keybd_event(VK_D, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)
    elif name == "alt_tab":
        user32.keybd_event(VK_MENU, 0, 0, 0)
        user32.keybd_event(VK_TAB, 0, 0, 0)
        time.sleep(0.04)
        user32.keybd_event(VK_TAB, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)

@router.websocket("/ws/touchpad")
async def touchpad_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            action = msg.get("action")
            
            if action == "move":
                dx = float(msg.get("dx", 0))
                dy = float(msg.get("dy", 0))
                speed = float(msg.get("speed", 1.0))
                move_mouse_accumulated(dx, dy, speed)
                
            elif action == "click":
                btn = msg.get("button", "left")
                if btn == "left":
                    left_click()
                elif btn == "right":
                    right_click()
                elif btn == "middle":
                    middle_click()
                    
            elif action == "scroll":
                dy = float(msg.get("dy", 0))
                dx = float(msg.get("dx", 0))
                scroll_mouse_accumulated(dy, dx)

            elif action == "zoom":
                delta = float(msg.get("delta", 0))
                zoom_mouse(delta)

            elif action == "gesture":
                name = msg.get("name", "")
                execute_gesture(name)
                
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
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <title>ADA Ultra Precision Touchpad</title>
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
      background: #07080c;
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
      padding: 8px 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      background: rgba(13, 15, 21, 0.9);
      backdrop-filter: blur(20px);
      z-index: 10;
    }
    .header .title {
      font-size: 13px;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 7px;
      letter-spacing: 0.5px;
      color: #f1f5f9;
    }
    .header .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #22d3ee;
      box-shadow: 0 0 10px #22d3ee;
    }
    .header .status {
      font-size: 11px;
      color: #94a3b8;
      font-family: ui-monospace, monospace;
      font-weight: 600;
    }

    /* Controls Bar: Speed & Scroll Direction Toggle */
    .controls-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 6px 14px;
      background: rgba(255, 255, 255, 0.025);
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      font-size: 11px;
    }
    .speed-presets {
      display: flex;
      gap: 5px;
      align-items: center;
    }
    .btn-toggle {
      padding: 3px 8px;
      border-radius: 6px;
      background: rgba(255, 255, 255, 0.07);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: #cbd5e1;
      font-size: 10px;
      font-weight: 700;
      cursor: pointer;
    }
    .btn-toggle.active {
      background: rgba(34, 211, 238, 0.22);
      border-color: #22d3ee;
      color: #22d3ee;
    }

    /* 3-Finger Quick Action Shortcuts Bar */
    .shortcuts-bar {
      display: flex;
      gap: 6px;
      padding: 6px 14px;
      background: rgba(0, 0, 0, 0.4);
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    .shortcut-pill {
      flex: 1;
      padding: 5px 0;
      text-align: center;
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.5px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 8px;
      color: #94a3b8;
      cursor: pointer;
      transition: all 0.1s;
    }
    .shortcut-pill:active {
      background: rgba(34, 211, 238, 0.2);
      color: #22d3ee;
      border-color: #22d3ee;
    }

    /* Main Touch Area */
    .touch-area {
      flex: 1;
      position: relative;
      background: radial-gradient(circle at center, rgba(34, 211, 238, 0.04) 0%, transparent 70%);
      display: flex;
      align-items: center;
      justify-content: center;
      touch-action: none;
    }
    .gesture-hint {
      color: rgba(255, 255, 255, 0.2);
      font-size: 11px;
      text-align: center;
      line-height: 1.7;
      pointer-events: none;
      font-weight: 500;
    }

    /* Bottom Buttons */
    .button-bar {
      height: 64px;
      display: flex;
      gap: 1px;
      background: rgba(255, 255, 255, 0.08);
      border-top: 1px solid rgba(255, 255, 255, 0.1);
    }
    .btn {
      flex: 1;
      background: #0a0c12;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 1.5px;
      color: #94a3b8;
      cursor: pointer;
      transition: all 0.1s;
    }
    .btn:active {
      background: rgba(34, 211, 238, 0.15);
      color: #22d3ee;
    }

    /* Floating Toast Feedback */
    .toast {
      position: absolute;
      top: 100px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(15, 23, 42, 0.95);
      border: 1px solid #22d3ee;
      box-shadow: 0 0 15px rgba(34, 211, 238, 0.3);
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 700;
      color: #22d3ee;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.2s ease;
      z-index: 100;
    }
    .toast.show {
      opacity: 1;
    }
  </style>
</head>
<body>
  <div class="header">
    <div class="title">
      <div class="dot" id="statusDot"></div>
      ADA TOUCHPAD
    </div>
    <div class="status" id="statusText">CONNECTING...</div>
  </div>

  <div class="controls-bar">
    <div class="speed-presets">
      <div class="btn-toggle" onclick="setSpeed(1.0)">1.0x</div>
      <div class="btn-toggle active" onclick="setSpeed(1.5)">1.5x</div>
      <div class="btn-toggle" onclick="setSpeed(2.0)">2.0x</div>
      <div class="btn-toggle" onclick="setSpeed(2.8)">2.8x</div>
    </div>
    <div class="btn-toggle active" id="scrollDirBtn" onclick="toggleScrollDir()">SCROLL: NATURAL</div>
  </div>

  <div class="shortcuts-bar">
    <div class="shortcut-pill" onclick="triggerGesture('show_desktop', 'Desktop (Win+D)')">🖥️ DESKTOP</div>
    <div class="shortcut-pill" onclick="triggerGesture('task_view', 'Task View (Win+Tab)')">📑 TASKS</div>
    <div class="shortcut-pill" onclick="triggerGesture('alt_tab', 'Switch App (Alt+Tab)')">⇄ ALT+TAB</div>
  </div>

  <div class="toast" id="toast"></div>

  <div class="touch-area" id="touchArea">
    <div class="gesture-hint">
      <b>1-Finger Move:</b> Fluid Cursor • <b>Tap:</b> Left Click<br>
      <b>2-Finger Drag:</b> Smooth Scroll • <b>2-Finger Tap:</b> Right Click<br>
      <b>3-Finger Swipe:</b> Up = Tasks, Down = Desktop, Left/Right = Alt-Tab
    </div>
  </div>

  <div class="button-bar">
    <div class="btn" id="leftBtn">LEFT CLICK</div>
    <div class="btn" id="rightBtn">RIGHT CLICK</div>
  </div>

  <script>
    let ws = null;
    let speedMultiplier = 1.5;
    let scrollMultiplier = 1; // 1 = Natural, -1 = Inverted
    const toast = document.getElementById('toast');

    function showToast(text) {
      toast.textContent = text;
      toast.classList.add('show');
      setTimeout(() => toast.classList.remove('show'), 900);
    }

    function setSpeed(val) {
      speedMultiplier = val;
      document.querySelectorAll('.speed-presets .btn-toggle').forEach(btn => {
        btn.classList.toggle('active', btn.textContent === (val.toFixed(1) + 'x') || btn.textContent === (val + 'x'));
      });
      showToast('Speed: ' + val + 'x');
    }

    function toggleScrollDir() {
      scrollMultiplier = scrollMultiplier === 1 ? -1 : 1;
      const btn = document.getElementById('scrollDirBtn');
      btn.textContent = scrollMultiplier === 1 ? 'SCROLL: NATURAL' : 'SCROLL: REVERSE';
      showToast(btn.textContent);
    }

    const host = window.location.host;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    
    function connect() {
      ws = new WebSocket(`${protocol}//${host}/ws/touchpad`);
      const statusText = document.getElementById('statusText');
      const statusDot = document.getElementById('statusDot');

      ws.onopen = () => {
        statusText.textContent = "CONNECTED (0ms USB)";
        statusText.style.color = "#4ade80";
        statusDot.style.background = "#4ade80";
        statusDot.style.boxShadow = "0 0 10px #4ade80";
      };

      ws.onclose = () => {
        statusText.textContent = "RECONNECTING...";
        statusText.style.color = "#f87171";
        statusDot.style.background = "#f87171";
        statusDot.style.boxShadow = "0 0 10px #f87171";
        setTimeout(connect, 1200);
      };
    }
    connect();

    function send(data) {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(data));
      }
    }

    function vibrate(ms) {
      if (navigator.vibrate) navigator.vibrate(ms);
    }

    function triggerGesture(name, label) {
      vibrate(30);
      showToast(label);
      send({ action: 'gesture', name });
    }

    // Touch gesture engine with 60fps RAF batching
    const touchArea = document.getElementById('touchArea');
    
    let touchStartTime = 0;
    let initialFingerCount = 0;
    let lastX = 0;
    let lastY = 0;
    let pendingMoveX = 0;
    let pendingMoveY = 0;
    let moveRafId = null;

    let twoFingerLastMid = { x: 0, y: 0 };
    let twoFingerMoved = false;
    let twoFingerTapCandidate = false;

    let threeFingerStartX = 0;
    let threeFingerStartY = 0;
    let threeFingerTriggered = false;

    function flushMove() {
      if (pendingMoveX !== 0 || pendingMoveY !== 0) {
        send({ action: 'move', dx: pendingMoveX, dy: pendingMoveY, speed: speedMultiplier });
        pendingMoveX = 0;
        pendingMoveY = 0;
      }
      moveRafId = null;
    }

    touchArea.addEventListener('touchstart', (e) => {
      e.preventDefault();
      touchStartTime = Date.now();
      const count = e.touches.length;

      if (count === 1) {
        initialFingerCount = 1;
        lastX = e.touches[0].clientX;
        lastY = e.touches[0].clientY;
      } else if (count === 2) {
        initialFingerCount = 2;
        twoFingerMoved = false;
        twoFingerTapCandidate = true;
        twoFingerLastMid = {
          x: (e.touches[0].clientX + e.touches[1].clientX) / 2,
          y: (e.touches[0].clientY + e.touches[1].clientY) / 2
        };
      } else if (count >= 3) {
        initialFingerCount = 3;
        threeFingerTriggered = false;
        threeFingerStartX = (e.touches[0].clientX + e.touches[1].clientX + e.touches[2].clientX) / 3;
        threeFingerStartY = (e.touches[0].clientY + e.touches[1].clientY + e.touches[2].clientY) / 3;
      }
    }, { passive: false });

    touchArea.addEventListener('touchmove', (e) => {
      e.preventDefault();
      const count = e.touches.length;

      // 1 FINGER: SMOOTH CURSOR (RAF BATCHED)
      if (count === 1) {
        const dx = e.touches[0].clientX - lastX;
        const dy = e.touches[0].clientY - lastY;
        pendingMoveX += dx;
        pendingMoveY += dy;
        lastX = e.touches[0].clientX;
        lastY = e.touches[0].clientY;

        if (moveRafId === null) {
          moveRafId = requestAnimationFrame(flushMove);
        }
      }
      // 2 FINGERS: NATURAL/REVERSE SCROLLING
      else if (count === 2) {
        twoFingerMoved = true;
        twoFingerTapCandidate = false;
        const midX = (e.touches[0].clientX + e.touches[1].clientX) / 2;
        const midY = (e.touches[0].clientY + e.touches[1].clientY) / 2;
        const dy = midY - twoFingerLastMid.y;
        const dx = midX - twoFingerLastMid.x;

        // Invert by scrollMultiplier
        if (Math.abs(dy) > 1.2 || Math.abs(dx) > 1.2) {
          send({
            action: 'scroll',
            dy: dy * 0.4 * scrollMultiplier,
            dx: -dx * 0.35 * scrollMultiplier
          });
        }
        twoFingerLastMid = { x: midX, y: midY };
      }
      // 3 FINGERS: MULTITASKING SWIPES
      else if (count >= 3 && !threeFingerTriggered) {
        const midX = (e.touches[0].clientX + e.touches[1].clientX + e.touches[2].clientX) / 3;
        const midY = (e.touches[0].clientY + e.touches[1].clientY + e.touches[2].clientY) / 3;
        const deltaX = midX - threeFingerStartX;
        const deltaY = midY - threeFingerStartY;

        if (deltaY < -32) {
          threeFingerTriggered = true;
          triggerGesture('task_view', 'Task View (Win+Tab)');
        } else if (deltaY > 32) {
          threeFingerTriggered = true;
          triggerGesture('show_desktop', 'Desktop (Win+D)');
        } else if (Math.abs(deltaX) > 38) {
          threeFingerTriggered = true;
          triggerGesture('alt_tab', 'Switch App (Alt+Tab)');
        }
      }
    }, { passive: false });

    touchArea.addEventListener('touchend', (e) => {
      e.preventDefault();
      const elapsed = Date.now() - touchStartTime;

      // 1-Finger Tap -> Left Click
      if (initialFingerCount === 1 && elapsed < 220 && Math.abs(pendingMoveX) < 10 && Math.abs(pendingMoveY) < 10) {
        vibrate(15);
        send({ action: 'click', button: 'left' });
      }
      // 2-Finger Tap -> Right Click
      else if (initialFingerCount === 2 && twoFingerTapCandidate && !twoFingerMoved && elapsed < 260) {
        vibrate(25);
        showToast('Right Click');
        send({ action: 'click', button: 'right' });
        twoFingerTapCandidate = false;
      }
    });

    // Hardware buttons
    document.getElementById('leftBtn').addEventListener('click', () => {
      vibrate(20);
      send({ action: 'click', button: 'left' });
    });
    document.getElementById('rightBtn').addEventListener('click', () => {
      vibrate(25);
      send({ action: 'click', button: 'right' });
    });
  </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)

def _get_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

@router.post("/api/devices/touchpad/launch")
async def launch_touchpad_on_phone():
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    adb_path = os.path.join(project_root, "platform-tools", "adb.exe")

    target = None
    try:
        res = subprocess.run([adb_path, "devices"], capture_output=True, text=True, timeout=3)
        for line in res.stdout.splitlines():
            if "	device" in line:
                target = line.split("	")[0]
                break
    except Exception as e:
        return {"status": "ERROR", "message": f"ADB error: {e}"}

    if not target:
        return {"status": "ERROR", "message": "No phone connected via ADB."}

    tunnel_success = False
    try:
        rev_res = subprocess.run([adb_path, "-s", target, "reverse", "tcp:8000", "tcp:8000"], capture_output=True, text=True, timeout=3)
        if rev_res.returncode == 0:
            tunnel_success = True
    except Exception:
        pass

    lan_ip = _get_lan_ip()
    touchpad_url = "http://localhost:8000/touchpad" if tunnel_success else f"http://{lan_ip}:8000/touchpad"

    try:
        subprocess.run([adb_path, "-s", target, "shell", "input", "keyevent", "224"], timeout=2)
        subprocess.run([
            adb_path, "-s", target, "shell", "am", "start",
            "-a", "android.intent.action.VIEW",
            "-d", touchpad_url
        ], timeout=4)
        return {"status": "SUCCESS", "device": target, "url": touchpad_url, "tunneled": tunnel_success}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}
