from typing import List, Dict, Any
from backend.core.logger import app_logger
from backend.services.api_registry import get_integration, ExecutionEngine
from backend.planner.schema import Task
from backend.desktop.schema import DesktopAction, DesktopActionType

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
        
        tools = [t.lower().strip() for t in task.required_tools]
        
        # 0. Background Search & Workspace Render
        if "background_search" in tools:
            app_logger.info(f"Routing {task.task_id} to Background Search / Workspace")
            try:
                from backend.main import events_ws_manager
                import json
                # Mock a search response for the UI
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

        # Device/Phone Management
        if "device" in tools and self.device_manager:
            app_logger.info(f"Routing {task.task_id} to Device Manager")
            intent = task.action_metadata.get("intent", "")
            entity = task.action_metadata.get("entity", "")
            ip_port = task.action_metadata.get("ip_port")
            
            if intent == "connect" and ip_port:
                return self.device_manager.connect(ip_port)
            elif intent == "pair" and ip_port:
                code = task.action_metadata.get("entity", "")
                return self.device_manager.pair(ip_port, code)
            else:
                kwargs = {k: v for k, v in task.action_metadata.items() if k not in ("intent", "entity")}
                result = self.device_manager.execute_action(intent, entity, **kwargs)
                app_logger.info(f"Device Manager output: {result}")
                # We can store result in task metadata for the LLM to see, but returning True is enough
                task.action_metadata["execution_output"] = result
                return True

        # Desktop Automation direct routing
        if "desktop" in tools or not app:
            return await self._execute_desktop(task)

        # Browser Automation direct routing
        if "browser" in tools:
            if self.browser_engine:
                url = task.action_metadata.get("url", "")
                if not url:
                    query = task.action_metadata.get("query", task.description)
                    url = f"https://www.google.com/search?q={query}"
                app_logger.info(f"Routing {task.task_id} to Browser Engine: {url}")
                try:
                    await self.browser_engine.navigate(url)
                    return True
                except Exception as be:
                    app_logger.error(f"Browser navigation failed: {be}")
            # Fallback to desktop browser launch
            return await self._execute_desktop(task)

        meta = get_integration(app)
        
        # 1. Official API
        if meta and meta.preferred_engine == ExecutionEngine.API:
            auth_context = self.api_manager.authenticate(app)
            if auth_context:
                try:
                    app_logger.info(f"Routing {task.task_id} to API Manager for {app}")
                    return True
                except Exception as e:
                    app_logger.error(f"API execution failed for {app}: {e}. Falling back...")
            else:
                app_logger.info(f"No API auth for {app}. Routing to Desktop automation directly...")
        
        # 2. Desktop Automation Fallback
        if self.desktop_engine:
            app_logger.info(f"Routing {task.task_id} to Desktop Engine")
            return await self._execute_desktop(task)
            
        app_logger.error(f"No execution engine available for task {task.task_id}")
        return False

    async def _execute_desktop(self, task: Task) -> bool:
        app_logger.info(f"Executing Desktop fallback for {task.description}")
        
        if not self.desktop_engine:
            app_logger.error("No Desktop Engine available.")
            return False

        # Extract metadata
        app_name = task.action_metadata.get("app", "")
        intent = task.action_metadata.get("intent", "")
        entity = task.action_metadata.get("entity", "")
        desktop_action_str = task.action_metadata.get("desktop_action", "")

        try:
            # Determine Action Type
            action_type = None
            payload = {}

            if desktop_action_str == "APP_INTENT_EXECUTE":
                action_type = DesktopActionType.APP_INTENT_EXECUTE
                payload = {"app": app_name, "intent": intent, "entity": entity}
            elif intent == "open_app":
                action_type = DesktopActionType.APP_LAUNCH
                payload = {"name": app_name}
            elif intent == "close_app":
                action_type = DesktopActionType.APP_CLOSE
                payload = {"name": app_name}
            else:
                # Default to APP_LAUNCH if unspecified
                app_logger.warning(f"Unknown intent '{intent}', defaulting to APP_LAUNCH")
                action_type = DesktopActionType.APP_LAUNCH
                payload = {"name": app_name}

            if not action_type:
                return False

            action = DesktopAction(action_type=action_type, payload=payload)
            await self.desktop_engine.perform_action(action)
            return True
        except Exception as e:
            app_logger.error(f"Desktop execution failed: {e}")
            return False
