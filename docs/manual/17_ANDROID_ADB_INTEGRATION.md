# Chapter 17: Wireless Android ADB Subsystem

## 1. Architectural Overview

ADA Mark VII integrates directly with physical Android hardware over the local Wi-Fi subnet using the Android Debug Bridge (ADB). This allows ADA to perceive mobile device states (real-time battery, screen power, foreground packages) and perform autonomous UI interactions without requiring third-party cloud bridges or companion APK installations.

```
                      +------------------------------------------+
                      |             Nova Kernel                  |
                      +--------------------+---------------------+
                                           | execute_action(intent, entity)
                                           v
                      +--------------------+---------------------+
                      |           DeviceManager                  |
                      |      (backend/devices/core.py)           |
                      +--------------------+---------------------+
                                           | Wi-Fi TCP/IP Socket (Port 5555)
                                           v
                      +--------------------+---------------------+
                      |        Physical Android Device           |
                      |        (e.g., 192.168.0.101:5555)        |
                      +--------------------+---------------------+
                         /                 |                 \
                        v                  v                  v
               +-----------------+ +----------------+ +----------------+
               | dumpsys battery | | uiautomator    | | am start       |
               | (Real Battery %) | | dump (UI Tree) | | (App Launch)   |
               +-----------------+ +----------------+ +----------------+
```

---

## 2. Auto-Discovery & Zero-Config Reconnection

The device manager maintains continuous awareness of connected Android devices:
1. **Background Polling Loop**: The daemon executes `adb devices` every 2 seconds.
2. **State-Preserving Connect**: When a paired IP device (e.g., `192.168.0.101:5555`) enters `offline` or disconnected state, ADA invokes `adb connect <target>` to automatically re-establish the socket.
3. **Primary Device Assignment**: The first active device reported by ADB is dynamically mapped as the primary target for all executive directives.

---

## 3. Real-Time Telemetry Perception (`get_battery`)

Mocked or static data is strictly forbidden across ADA. Android battery telemetry is parsed directly from the hardware power management subsystem:

```bash
adb -s 192.168.0.101:5555 shell dumpsys battery
```

ADA extracts the true percentage:
```python
def get_battery_level(self, device_id: str) -> str:
    res = subprocess.run([self.adb_path, "-s", device_id, "shell", "dumpsys", "battery"], capture_output=True, text=True)
    for line in res.stdout.splitlines():
        if "level:" in line:
            return f"{line.split(':')[1].strip()}%"
    return "Unknown"
```
This metric powers both the **Phone Bridge HUD widget** and verbal voice responses (e.g., *"Your phone battery is currently at 88%."*).

---

## 4. State-Aware Self-Healing App Navigation

Standard mobile automation scripts fail when an application is in an unexpected state (such as viewing an old conversation or a search overlay). ADA implements a **State-Aware Self-Healing Navigator** that inspects the live Accessibility hierarchy (`uiautomator dump /sdcard/window_dump.xml`) before dispatching touch events.

### 4.1 WhatsApp Navigation Protocol (`_open_whatsapp_chat`)
When sending a WhatsApp message:
1. **Focus Verification**: Ensures `com.whatsapp` is in the foreground. If not, launches the application with `am start`.
2. **State 1 (Already in Target Chat)**: Inspects `com.whatsapp:id/conversation_contact_name`. If the contact name matches the target, enters typing phase immediately.
3. **State 2 (In Wrong Chat)**: If the screen is inside another contact's thread, issues a hardware `BACK` keyevent (`input keyevent 4`) to safely return to the conversation list.
4. **State 3 (Home Chat List)**: Checks if the contact is already visible in the conversation rows. If visible, taps directly on the row's center coordinates. If not visible, activates the search bar (`com.whatsapp:id/search_bar_inner_layout`), types the sanitized contact name, and taps the top matching result.
5. **Message Injection**: Focuses the input field (`com.whatsapp:id/entry`), injects text via sanitized ADB input, dismisses the soft keyboard, and taps the send button (`com.whatsapp:id/send`).

---

## 5. Messaging Safety Interlocks & Anti-Misdirection Guards

> [!IMPORTANT]
> **Strict Recipient Validation Guard**
> ADA enforces strict validation on all outbound messaging intents to prevent misdirected messages:

```python
if intent == "send_message":
    contact = (entity or "").strip()
    if not contact:
        app_logger.warning("[DeviceManager] Send message rejected: No recipient contact specified.")
        return "Cannot send message: No recipient contact specified."
```

### 5.1 Empty-String Search Prevention
In earlier iterations, searching for an empty contact string `""` caused `"" in node_text` to evaluate to `True`, triggering a tap on the first visible conversation on screen (e.g., Manav / Vedya). 

The navigation engine strictly guarantees:
```python
contact_clean = (contact or "").strip()
if not contact_clean:
    return False

# Node matching requires non-empty contact string
if contact_clean.lower() in node_text:
    found_contact_node = node
```
If a command lacks an explicit recipient, the action is aborted immediately with a clear warning logged to `backend_daemon.log`.

---

## 6. Remote Media & App Control Matrix

ADA natively controls applications using official Android intent categories:

| Target App | Package Name | Action Performed |
| :--- | :--- | :--- |
| **Spotify** | `com.spotify.music` | Opens app, activates media query intent to play track/playlist. |
| **YouTube** | `com.google.android.youtube` | Dispatches search intent `android.intent.action.SEARCH`. |
| **Chrome** | `com.android.chrome` | Opens URL or executes web search intent. |
| **Device Screen** | Native Power Manager | Wakes display (`input keyevent 224`) and dismisses lockscreen. |
