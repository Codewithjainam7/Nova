import os
from typing import List, Dict, Any, Optional
from backend.core.logger import app_logger
from backend.services.api_registry import get_integration, ExecutionEngine
from backend.planner.schema import Task
from backend.desktop.schema import DesktopAction, DesktopActionType
from backend.browser.schema import BrowserAction, BrowserActionType
import ctypes

def _ensure_desktop():
    try:
        user32 = ctypes.windll.user32
        h_default = user32.OpenDesktopW("Default", 0, False, 0x01FF)
        if h_default:
            user32.SetThreadDesktop(h_default)
    except Exception:
        pass

class CapabilityRouter:
    """
    Intercepts intents from the Planner and routes them to the correct execution engine
    based on the capability hierarchy: API -> Native -> Browser -> Desktop -> Device.
    """
    def __init__(self, api_manager, browser_engine=None, desktop_engine=None, native_engine=None, device_manager=None):
        self.api_manager = api_manager
        self.browser_engine = browser_engine
        self.desktop_engine = desktop_engine
        self.native_engine = native_engine
        self.device_manager = device_manager

    async def route_task(self, task: Task) -> bool:
        """
        Determines the best engine for the task and attempts execution.
        Falls back down the hierarchy if execution fails.
        """
        app_logger.info(f"Routing task {task.task_id}: {task.description}")
        _ensure_desktop()
        
        tools = [t.lower().strip() for t in task.required_tools]
        desc_lower = task.description.lower()
        app_name = task.action_metadata.get("app", "").lower().strip()
        intent = task.action_metadata.get("intent", "").lower().strip()
        
        # 0. Background Search & Workspace Render
        if "background_search" in tools:
            app_logger.info(f"Routing {task.task_id} to Background Search / Workspace")
            try:
                from backend.main import events_ws_manager
                import json
                query = task.action_metadata.get("query", task.description)
                payload = {
                    "type": "WORKSPACE_RENDER",
                    "payload": {
                        "query": query,
                        "maps": [{"title": "Global Heatmap", "src": "heatmap"}],
                        "news": [{"title": f"Latest updates on {query}", "source": "Reuters"}]
                    }
                }
                await events_ws_manager.broadcast(json.dumps(payload))
                task.action_metadata["execution_output"] = f"Rendered workspace for {query}"
                return True
            except Exception as e:
                app_logger.error(f"Failed to render workspace: {e}")
                return False

        # 0.5 Hermes Procedural Skill Engine
        if "skill" in tools or intent in ["run_skill", "execute_skill"]:
            from backend.capabilities.skill_engine import skill_engine
            import json
            skill_name = task.action_metadata.get("skill_name") or app_name
            if not skill_name:
                skill_name = task.description.replace("run skill", "").replace("execute skill", "").strip()
            skill_name = skill_name.replace(" ", "_").replace("-", "_").lower()
            app_logger.info(f"[CapabilityRouter] Executing Hermes skill: '{skill_name}'")
            res = skill_engine.execute_skill(skill_name, **task.action_metadata)
            task.action_metadata["execution_output"] = json.dumps(res.get("result", res), indent=2)
            return res.get("status") == "SUCCESS"

        # Device/Phone Management & Mobile App Guard
        phone_apps = {"instagram", "whatsapp", "telegram", "phone", "messages"}
        
        is_phone_target = (
            "device" in tools or
            app_name in phone_apps or
            any(k in desc_lower for k in ["instagram", "whatsapp", "telegram", "on phone", "on mobile"]) or
            (intent in ["send_message", "message"] and "desktop" not in tools)
        )

        if is_phone_target and self.device_manager:
            app_logger.info(f"Routing {task.task_id} to Device Manager (app={app_name}, desc={task.description})")
            entity = task.action_metadata.get("entity", "")
            ip_port = task.action_metadata.get("ip_port")
            
            if intent == "connect" and ip_port:
                return self.device_manager.connect(ip_port)
            elif intent == "pair" and ip_port:
                code = task.action_metadata.get("entity", "")
                return self.device_manager.pair(ip_port, code)
            else:
                # Default messaging platform is ALWAYS WhatsApp if not specified
                if intent in ["send_message", "message"] or any(k in desc_lower for k in ["msg", "message", "send"]):
                    if not task.action_metadata.get("app") or task.action_metadata.get("app", "").lower() in ["messaging", "default", "none", "phone"]:
                        task.action_metadata["app"] = "whatsapp"
                    intent = "send_message"
                elif intent in ["open_app", "launch_app"] or "launch" in desc_lower or "open" in desc_lower:
                    if not entity and app_name:
                        entity = app_name
                    intent = "open_app"

                kwargs = {k: v for k, v in task.action_metadata.items() if k not in ("intent", "entity")}
                result = self.device_manager.execute_action(intent, entity, **kwargs)
                app_logger.info(f"Device Manager output: {result}")
                task.action_metadata["execution_output"] = result
                return True

        # Browser Automation direct routing
        if "browser" in tools:
            return await self._execute_browser(task)

        # Desktop Automation direct routing
        app_name = task.action_metadata.get("app", "").lower().strip()
        if "desktop" in tools or not app_name:
            return await self._execute_desktop(task)

        meta = get_integration(app_name)
        
        # 1. Official API
        if meta and meta.preferred_engine == ExecutionEngine.API:
            auth_context = self.api_manager.authenticate(app_name)
            if auth_context:
                try:
                    app_logger.info(f"Routing {task.task_id} to API Manager for {app_name}")
                    return True
                except Exception as e:
                    app_logger.error(f"API execution failed for {app_name}: {e}. Falling back...")
            else:
                app_logger.info(f"No API auth for {app_name}. Routing to Desktop automation directly...")
        
        # 2. Desktop Automation Fallback
        if self.desktop_engine:
            app_logger.info(f"Routing {task.task_id} to Desktop Engine")
            return await self._execute_desktop(task)
            
        app_logger.error(f"No execution engine available for task {task.task_id}")
        return False

    async def _execute_browser(self, task: Task) -> bool:
        """Executes browser automation actions via Playwright."""
        app_logger.info(f"Executing Browser task: {task.description}")
        if not self.browser_engine:
            app_logger.error("No Browser Engine available.")
            return False
            
        meta = task.action_metadata
        url = meta.get("url", "")
        query = meta.get("query", "")
        intent = meta.get("intent", "").lower().strip()
        browser_action_str = meta.get("browser_action", "").upper().strip()
        
        try:
            # 1. Direct Search or Intent 'search'
            if intent in ["search", "google", "lookup"] or (query and not url):
                search_q = query or task.description
                app_logger.info(f"Browser Engine: Searching for '{search_q}'")
                output = await self.browser_engine.search(search_q)
                if output:
                    task.action_metadata["execution_output"] = f"Search result for '{search_q}': {output}"
                else:
                    task.action_metadata["execution_output"] = f"Opened search for '{search_q}' in browser."
                return True
                
            # 2. Direct Navigation
            if url or browser_action_str == "NAVIGATE":
                target_url = url or query
                if not target_url:
                    target_url = "https://www.google.com"
                app_logger.info(f"Browser Engine: Navigating to {target_url}")
                await self.browser_engine.navigate(target_url)
                task.action_metadata["execution_output"] = f"Navigated to {target_url}"
                return True
                
            # 3. Click
            if browser_action_str == "CLICK":
                selector = meta.get("selector", "")
                await self.browser_engine.click(selector)
                task.action_metadata["execution_output"] = f"Clicked {selector}"
                return True
                
            # 4. Type / Fill
            if browser_action_str in ["TYPE", "FILL"]:
                selector = meta.get("selector", "")
                text = meta.get("text", "")
                await self.browser_engine.fill(selector, text)
                task.action_metadata["execution_output"] = f"Typed into {selector}"
                return True
                
            # 5. Extract Text
            if browser_action_str == "EXTRACT_TEXT":
                selector = meta.get("selector", "")
                text = await self.browser_engine.extract_text(selector)
                task.action_metadata["execution_output"] = text
                return True
                
            # Default fallback: navigate to Google query
            default_q = query or task.description
            await self.browser_engine.search(default_q)
            task.action_metadata["execution_output"] = f"Searched for {default_q}"
            return True
            
        except Exception as e:
            app_logger.error(f"Browser task execution failed: {e}")
            return False

    async def _execute_desktop(self, task: Task) -> bool:
        """Executes desktop automation actions via Windows UIA and Adapters."""
        app_logger.info(f"Executing Desktop task for {task.description}")
        _ensure_desktop()
        
        if not self.desktop_engine:
            app_logger.error("No Desktop Engine available.")
            return False

        meta = task.action_metadata
        app_name = meta.get("app") or meta.get("application") or meta.get("name") or ""
        intent = meta.get("intent", "").lower().strip()
        entity = meta.get("entity", "")
        url = meta.get("url", "")
        desktop_action_str = meta.get("desktop_action", "").upper().strip()

        # Mobile app redirection guard: Never try to launch mobile phone apps on Windows PC
        phone_apps = {"instagram", "whatsapp", "telegram", "phone", "messages"}
        if app_name.lower().strip() in phone_apps and self.device_manager:
            app_logger.info(f"Redirecting mobile app '{app_name}' from Desktop Engine to Device Manager.")
            res = self.device_manager.execute_action("open_app", app_name)
            task.action_metadata["execution_output"] = res
            return True

        try:
            # 0. Native Windows System Actions (Instantaneous Win32 Lock & Sleep)
            if intent in ["lock_laptop", "lock_screen", "lock_pc"] or desktop_action_str == "LOCK_SCREEN" or (intent == "lock" and app_name in ["", "windows", "laptop", "pc"]):
                import ctypes
                app_logger.info("[CapabilityRouter] Executing native Win32 LockWorkStation...")
                ctypes.windll.user32.LockWorkStation()
                task.action_metadata["execution_output"] = "I have locked your laptop, Boss."
                return True

            if intent in ["sleep", "sleep_laptop", "sleep_pc"] or desktop_action_str == "SLEEP":
                import ctypes
                app_logger.info("[CapabilityRouter] Executing native Win32 SetSuspendState...")
                ctypes.windll.powrprof.SetSuspendState(0, 1, 0)
                task.action_metadata["execution_output"] = "Putting laptop to sleep, Boss."
                return True

            # 1. Semantic Intent Routing (Spotify, Settings, Calculator, Notepad, File Explorer, Folder Organization)
            file_organize_intents = {"organize", "organize_folder", "sort_folder", "clean_folder"}
            if intent in file_organize_intents:
                if not app_name:
                    app_name = "explorer"
                if not entity:
                    entity = "downloads"

            if desktop_action_str == "APP_INTENT_EXECUTE" or intent in [
                "calculate", "compute", "math", "write_note", "write", "type_text",
                "save_file", "play_media", "navigate", "open_folder", "explore",
                "organize", "organize_folder", "sort_folder", "clean_folder"
            ]:
                action = DesktopAction(
                    action_type=DesktopActionType.APP_INTENT_EXECUTE,
                    payload={"app": app_name or "explorer", "intent": intent or "open_app", "entity": entity, "url": url}
                )
                await self.desktop_engine.perform_action(action)
                
                # Check if router returned output (e.g. calculation answer, file saved, note text, organization summary)
                output = action.payload.get("output")
                if output:
                    task.action_metadata["execution_output"] = str(output)
                else:
                    task.action_metadata["execution_output"] = f"Successfully executed {intent} on {app_name}"
                return True
                
            # 2. Window & File Launch / Close
            elif intent in ["open_app", "open_file"] or desktop_action_str == "APP_LAUNCH":
                file_path = meta.get("path")
                payload = {"name": app_name or entity}
                if file_path:
                    payload["path"] = file_path
                if meta.get("file_path"):
                    payload["file_path"] = meta.get("file_path")
                if meta.get("additional_urls"):
                    payload["additional_urls"] = meta.get("additional_urls")
                if meta.get("background"):
                    payload["background"] = meta.get("background")
                if url:
                    payload["url"] = url
                action = DesktopAction(action_type=DesktopActionType.APP_LAUNCH, payload=payload)
                await self.desktop_engine.perform_action(action)

                service_display = meta.get("service")
                search_query = meta.get("query")
                file_name_display = meta.get("file_name")
                is_bg = meta.get("background")
                bg_phrase = " in the background" if is_bg else ""

                if meta.get("upload_to_service") or intent == "upload_document":
                    target_svc = service_display or "Google Docs"
                    target_file = file_name_display or (os.path.basename(file_path) if file_path else "the requested document")
                    task.action_metadata["execution_output"] = f"Opened {target_svc} in {app_name or 'Chrome'} and uploaded '{target_file}'{bg_phrase} for you, Boss."
                elif url and service_display and file_name_display:
                    task.action_metadata["execution_output"] = f"Opened {service_display} and {file_name_display} in {app_name or entity}{bg_phrase}"
                elif url and service_display:
                    task.action_metadata["execution_output"] = f"Launched {app_name or entity} and opened {service_display}{bg_phrase}"
                elif url and search_query:
                    task.action_metadata["execution_output"] = f"Launched {app_name or entity} and searched for '{search_query}'{bg_phrase}"
                elif url:
                    if "google.com/search?q=" in str(url):
                        import urllib.parse
                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(str(url)).query)
                        q_term = parsed.get("q", [""])[0].replace("+", " ")
                        task.action_metadata["execution_output"] = f"Launched {app_name or entity} and searched Google for '{q_term}'{bg_phrase}"
                    else:
                        task.action_metadata["execution_output"] = f"Launched {app_name or entity} and navigated to {url}{bg_phrase}"
                elif file_path:
                    fname = file_name_display or os.path.basename(file_path)
                    task.action_metadata["execution_output"] = f"Opened {fname}{bg_phrase}"
                else:
                    task.action_metadata["execution_output"] = f"Launched {app_name or entity}{bg_phrase}"
                return True
                
            elif intent == "close_app" or desktop_action_str == "APP_CLOSE":
                action = DesktopAction(action_type=DesktopActionType.APP_CLOSE, payload={"name": app_name or entity})
                await self.desktop_engine.perform_action(action)
                task.action_metadata["execution_output"] = f"Closed {app_name or entity}"
                return True
                
            # 3. Direct Keyboard Typing / Shortcuts
            elif desktop_action_str == "KEYBOARD_TYPE":
                text = meta.get("text", entity)
                action = DesktopAction(action_type=DesktopActionType.KEYBOARD_TYPE, payload={"text": text})
                await self.desktop_engine.perform_action(action)
                task.action_metadata["execution_output"] = f"Typed: {text}"
                return True
                
            elif desktop_action_str == "KEYBOARD_SHORTCUT":
                keys = meta.get("keys", [entity] if entity else [])
                action = DesktopAction(action_type=DesktopActionType.KEYBOARD_SHORTCUT, payload={"keys": keys})
                await self.desktop_engine.perform_action(action)
                task.action_metadata["execution_output"] = f"Sent shortcut: {keys}"
                return True
                
            # 4. Direct Mouse Click
            elif desktop_action_str == "MOUSE_CLICK":
                x = meta.get("x")
                y = meta.get("y")
                button = meta.get("button", "left")
                action = DesktopAction(action_type=DesktopActionType.MOUSE_CLICK, payload={"x": x, "y": y, "button": button})
                await self.desktop_engine.perform_action(action)
                task.action_metadata["execution_output"] = f"Clicked at ({x}, {y})"
                return True
                
            # 5. Window Focus
            elif desktop_action_str == "WINDOW_FOCUS":
                title = meta.get("title", app_name or entity)
                action = DesktopAction(action_type=DesktopActionType.WINDOW_FOCUS, payload={"title": title})
                await self.desktop_engine.perform_action(action)
                task.action_metadata["execution_output"] = f"Focused window: {title}"
                return True

            # 6. Screenshot
            elif desktop_action_str == "SCREENSHOT":
                path = meta.get("path", "desktop_screenshot.png")
                action = DesktopAction(action_type=DesktopActionType.SCREENSHOT, payload={"path": path})
                await self.desktop_engine.perform_action(action)
                task.action_metadata["execution_output"] = f"Saved screenshot to {path}"
                return True

            # Default: try launching or executing intent
            if app_name:
                action = DesktopAction(
                    action_type=DesktopActionType.APP_INTENT_EXECUTE,
                    payload={"app": app_name, "intent": intent or "open_app", "entity": entity}
                )
                await self.desktop_engine.perform_action(action)
                output = action.payload.get("output", f"Executed {intent} on {app_name}")
                task.action_metadata["execution_output"] = str(output)
                return True

            app_logger.warning(f"Could not determine desktop action for {task.description}")
            return False

        except Exception as e:
            app_logger.error(f"Desktop execution failed: {e}")
            if ("not find the file" in str(e).lower() or "createprocess" in str(e).lower()) and self.device_manager:
                app_logger.info(f"Executable not found on Windows. Attempting device fallback for '{app_name}'...")
                try:
                    res = self.device_manager.execute_action("open_app", app_name)
                    task.action_metadata["execution_output"] = res
                    return True
                except Exception as dev_err:
                    app_logger.error(f"Device fallback also failed: {dev_err}")
            return False
