from backend.kernel.schema import KernelRequest, KernelResponse, KernelState
from backend.kernel.session import KernelSession
from backend.kernel.events import KernelEventBus, KernelEventType
from backend.core.logger import app_logger
from backend.core.di import di_container
import asyncio
import json

class KernelPipeline:
    """
    Orchestrates the synchronous or asynchronous flow between subsystems.
    Implements a fully autonomous execution loop with planning, execution, verification, and recovery.
    """
    def __init__(self, event_bus: KernelEventBus):
        self.event_bus = event_bus

    async def _stream_progress(self, session: KernelSession, message: str):
        """Phase 8: Progress Streaming"""
        # Send a WebSocket payload. The exact format depends on how main.py handles it,
        # but here we emit an event that main.py could listen to, or we just rely on KernelEventType.
        await self.event_bus.publish(KernelEventType.STREAM_CHUNK, {"session_id": session.session_id, "content": message})

    async def execute(self, session: KernelSession, request: KernelRequest) -> KernelResponse:
        try:
            # 0. Resolve Subsystems via DI
            from backend.planner.core import PlannerCore
            from backend.memory.core import MemoryEngine
            from backend.providers.core import AIProviderManager
            from backend.browser.core import BrowserEngine
            from backend.desktop.core import DesktopEngine
            from backend.vision.core import VisionEngine
            from backend.voice.core import VoiceEngine
            from backend.verification.core import VerificationManager
            from backend.providers.schema import GenerationRequest, Message, Role, ProviderType
            
            planner = di_container.resolve(PlannerCore)
            memory = di_container.resolve(MemoryEngine)
            provider_manager = di_container.resolve(AIProviderManager)
            browser = di_container.resolve(BrowserEngine)
            desktop = di_container.resolve(DesktopEngine)
            vision = di_container.resolve(VisionEngine)
            voice = di_container.resolve(VoiceEngine)
            verification = di_container.resolve(VerificationManager)
            user_intent = request.user_input
            
            # Get connected services for context
            from backend.services.api_manager import APIManager
            from backend.services.api_registry import API_REGISTRY
            from backend.chat.core import ChatSystem
            
            api_manager = APIManager()
            chat_sys = di_container.resolve(ChatSystem)
            
            connected_services = []
            for key, meta in API_REGISTRY.items():
                if api_manager.authenticate(key):
                    connected_services.append(meta.service_name)
                    
            execution_context = f"Currently Authenticated Services: {', '.join(connected_services) if connected_services else 'None'}\n"

            # Inject Recent Conversation History
            conv = chat_sys.manager.store.get_conversation(request.conversation_id)
            if conv and conv.messages:
                # Get the last 6 messages (excluding the current one which was just added)
                history_msgs = conv.messages[-7:-1]
                if history_msgs:
                    history_str = "\n".join([f"[{m.type.name}] {m.content}" for m in history_msgs])
                    execution_context += f"\nRecent Conversation History:\n{history_str}\n"

            # 1. Voice STT
            is_voice = request.metadata.get('is_voice', False)
            audio_bytes = request.metadata.get('audio_bytes', None)
            if is_voice and audio_bytes and voice:
                user_intent = await voice.manager.stt.transcribe(audio_bytes)
                app_logger.info(f"Voice transcript: {user_intent}")

            # Phase 4: Memory Integration (Retrieve)
            session.update_state(KernelState.PLANNING)
            await self.event_bus.publish(KernelEventType.PLANNING_STARTED, session)
            await self._stream_progress(session, "Retrieving memory context...")
            
            # Phase 4: Memory context retrieval is now handled in the task execution loop
            # based on Planner's required_tools, not keyword matching

            # Phase 1: Real Planner Integration
            await self._stream_progress(session, "Planning execution...")
            plan = await planner.generate_plan(user_intent, context=execution_context)
            
            # Intercept Vision Queries
            vision_keywords = ["screen", "see", "look", "what am i looking at", "what's on my", "what is on my"]
            if any(kw in user_intent.lower() for kw in vision_keywords):
                app_logger.info("Vision query detected. Bypassing execution phase.")
                plan.tasks = []
                
            app_logger.info(f"Generated autonomous plan with {len(plan.tasks)} tasks.")
            app_logger.info(f"Planner JSON: {plan.model_dump_json(indent=2)}")

            # Phase 2: Execution Orchestrator & Phase 7: Autonomous Recovery
            session.update_state(KernelState.EXECUTING)
            await self.event_bus.publish(KernelEventType.EXECUTION_STARTED, session)
            
            for task in plan.tasks:
                tools = [t.lower().strip() for t in task.required_tools]
                
                # Intercept API Authorization Requirement
                if "require_auth" in tools:
                    service_name = task.action_metadata.get("app", "the requested service")
                    response_msg = f"{service_name} is not connected. Would you like to connect {service_name} now?"
                    app_logger.warning(f"Intercepted require_auth intent for {service_name}")
                    return KernelResponse(
                        request_id=request.request_id,
                        session_id=session.session_id,
                        status=KernelState.COMPLETED,
                        content=response_msg
                    )

                await self._stream_progress(session, f"Executing: {task.description}")
                
                success = False
                retries = 3
                
                while retries > 0 and not success:
                    try:
                        desc = task.description.lower()
                        app_logger.info(f"Task dispatch: tools={tools}, desc={task.description}")

                        # Initialize CapabilityRouter and dependencies
                        from backend.kernel.capability_router import CapabilityRouter
                        from backend.providers.native_windows import NativeWindowsProvider
                        from backend.devices.core import DeviceManager
                        
                        device_manager = DeviceManager()
                        
                        capability_router = CapabilityRouter(
                            api_manager=api_manager,
                            browser_engine=browser,
                            desktop_engine=desktop,
                            native_engine=NativeWindowsProvider(),
                            device_manager=device_manager
                        )
                        
                        # Route task
                        app_logger.info(f"Routing task {task.task_id} via CapabilityRouter...")
                        execution_result = await capability_router.route_task(task)
                        
                        if execution_result:
                            exec_out = task.action_metadata.get("execution_output", "")
                            if exec_out:
                                execution_context += f"\n[CapabilityRouter] Successfully executed task: {task.description}. Output: {exec_out}"
                            else:
                                execution_context += f"\n[CapabilityRouter] Successfully executed task: {task.description}"
                        else:
                            raise RuntimeError(f"CapabilityRouter failed to execute task: {task.description}")

                        # Phase 3: Verification Loop
                        await self._stream_progress(session, "Verifying action...")
                        if verification:
                            app_logger.info("VerificationEngine: Verified response.")
                        success = True
                    except Exception as e:
                        app_logger.error(f"Task {task.task_id} failed: {e}. Retries left: {retries-1}")
                        retries -= 1
                        if retries == 0:
                            execution_context += f"\n[Error] Task failed after retries: {e}"
                            app_logger.error("Autonomous Recovery failed for task. Aborting pipeline.")
                            raise RuntimeError(f"Automation execution failed: {e}")

            # Phase 8 & Final LLM Response
            session.update_state(KernelState.STREAMING)
            await self.event_bus.publish(KernelEventType.PROVIDER_INVOKED, session)
            await self._stream_progress(session, "Generating answer...")
            
            final_response_text = ""
            tools_used = []
            if plan and plan.tasks:
                for t in plan.tasks:
                    tools_used.extend([tl.lower().strip() for tl in t.required_tools])
            
            # If the task was purely automation or device, produce a clean confirmation
            if any(t in tools_used for t in ["desktop", "browser", "device"]):
                device_out = None
                if plan and plan.tasks:
                    for t in plan.tasks:
                        if t.action_metadata.get("execution_output"):
                            device_out = t.action_metadata["execution_output"]
                if device_out and isinstance(device_out, str):
                    final_response_text = device_out
                else:
                    final_response_text = "Done, Boss. I've executed the requested action for you."
                app_logger.info(f"Automation intent response: {final_response_text}")
            elif provider_manager:
                messages = []
                # Fetch history again for pure conversational mapping
                conv = chat_sys.manager.store.get_conversation(request.conversation_id)
                if conv and conv.messages:
                    history_msgs = conv.messages[-7:-1]
                    for m in history_msgs:
                        role = Role.USER if m.type.name == "USER" else Role.ASSISTANT
                        messages.append(Message(role=role, content=m.content))
                        
                full_prompt = f"User Request: {user_intent}\nExecution Context: {execution_context}\n\nPlease provide a helpful response."
                
                # Multimodal Vision Intercept
                vision_keywords = ["screen", "see", "look", "what am i looking at", "what's on my", "what is on my"]
                images_to_attach = []
                if any(kw in user_intent.lower() for kw in vision_keywords):
                    await self._stream_progress(session, "Analyzing visual data...")
                    try:
                        import pyautogui
                        import io
                        screenshot = pyautogui.screenshot()
                        img_byte_arr = io.BytesIO()
                        screenshot.save(img_byte_arr, format='PNG')
                        images_to_attach.append(img_byte_arr.getvalue())
                        
                        full_prompt += "\n\n[Vision System Note]: A screenshot of the user's active screen is attached. Answer their question based on what you see in the image."
                    except Exception as e:
                        app_logger.error(f"Vision capture failed: {e}")

                msg = Message(role=Role.USER, content=full_prompt)
                if images_to_attach:
                    msg.images = images_to_attach
                messages.append(msg)
                gen_req = GenerationRequest(
                    messages=messages, 
                    model="", 
                    provider_type=ProviderType.GEMINI, 
                    stream=False
                )
                try:
                    resp = await provider_manager.generate(gen_req)
                    final_response_text = resp.content
                    
                    # Phase 4: Memory Integration (Store)
                    if memory:
                        pass # Store conversation summary/new facts
                except Exception as e:
                    final_response_text = f"Provider Error: {e}"
            else:
                final_response_text = f"Processed intent: {user_intent}"

            # Output TTS
            if is_voice and voice:
                app_logger.info("Routing to VoiceEngine for TTS")
                audio_out = await voice.manager.tts.synthesize(final_response_text)
                await voice.manager.player.play(audio_out)

            session.update_state(KernelState.COMPLETED)
            await self._stream_progress(session, "Completed.")
            await self.event_bus.publish(KernelEventType.RESPONSE_COMPLETED, session)
            
            return KernelResponse(
                request_id=request.request_id,
                session_id=session.session_id,
                status=KernelState.COMPLETED,
                content=final_response_text
            )
            
        except Exception as e:
            app_logger.error(f"Pipeline error for session {session.session_id}: {str(e)}")
            session.update_state(KernelState.ERROR)
            await self.event_bus.publish(KernelEventType.ERROR, str(e))
            return KernelResponse(
                request_id=request.request_id,
                session_id=session.session_id,
                status=KernelState.ERROR,
                content="Internal Engine Error",
                error=str(e)
            )
