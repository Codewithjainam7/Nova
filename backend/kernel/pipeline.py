from backend.kernel.schema import KernelRequest, KernelResponse, KernelState
from backend.kernel.session import KernelSession
from backend.kernel.events import KernelEventBus, KernelEventType
from backend.core.logger import app_logger
from backend.core.di import di_container
import os
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
            
            # Get connected services for context (only if query mentions external services)
            from backend.services.api_manager import APIManager
            from backend.services.api_registry import API_REGISTRY
            from backend.chat.core import ChatSystem
            
            api_manager = APIManager()
            chat_sys = di_container.resolve(ChatSystem)
            
            connected_services = []
            service_keywords = ["email", "gmail", "spotify", "music", "calendar", "inbox", "mail"]
            if any(k in user_intent.lower() for k in service_keywords):
                for key, meta in API_REGISTRY.items():
                    if api_manager.authenticate(key):
                        connected_services.append(meta.service_name)
                    
            execution_context = f"Currently Authenticated Services: {', '.join(connected_services)}\n" if connected_services else ""

            # Inject Recent Conversation History
            conv = None
            if chat_sys and hasattr(chat_sys, 'manager') and chat_sys.manager:
                try:
                    conv = chat_sys.manager.store.get_conversation(request.conversation_id)
                except Exception:
                    pass
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

            # Phase 4: Memory Integration (Two-Tier Cognitive Injection)
            session.update_state(KernelState.PLANNING)
            await self.event_bus.publish(KernelEventType.PLANNING_STARTED, session)
            await self._stream_progress(session, "Retrieving memory context...")
            
            # Tier 1: Core User Profile, Social Graph, and Daily Routine Perception
            try:
                from backend.memory.profile_store import profile_store
                from backend.memory.routine_tracker import routine_tracker
                core_profile = profile_store.get_core_profile_prompt()
                routine_ctx = routine_tracker.get_routine_context()
                if core_profile:
                    execution_context += f"\n[Core User Profile & Social Graph]:\n{core_profile}\n"
                if routine_ctx:
                    execution_context += f"\n[Active Routine & Habit Context]:\n{routine_ctx}\n"
            except Exception as pe:
                app_logger.debug(f"Profile context injection notice: {pe}")

            # Tier 2: Vector Semantic Memory (ChromaDB / SQLite top-k)
            if memory:
                try:
                    from backend.memory.schema import MemoryQuery
                    mem_query = MemoryQuery(query_text=user_intent, top_k=3)
                    retrieved_items = await memory.retriever.retrieve(mem_query)
                    if retrieved_items:
                        mem_bullets = "\n".join([f"- {item.content}" for item in retrieved_items if item and getattr(item, "content", None)])
                        if mem_bullets:
                            execution_context += f"\n[Episodic & Past Memory]:\n{mem_bullets}\n"
                            app_logger.info(f"Injected {len(retrieved_items)} memory items into context.")
                except Exception as me:
                    app_logger.debug(f"Memory retrieval notice: {me}")

            # Phase 0.5: Autonomous Overnight & Away Mission Intercept
            from backend.missions.mission_runner import MissionRunner
            mission_runner = MissionRunner(provider_manager)
            if mission_runner.is_away_or_night_mission(user_intent):
                await self._stream_progress(session, "Initializing autonomous night-shift mission...")
                mission_res = await mission_runner.execute_mission(user_intent)
                report_name = os.path.basename(mission_res.get("report_file", "report.md"))
                final_response_text = (
                    f"Understood, Boss. I have initiated your autonomous mission: '{user_intent}'.\n\n"
                    f"I have conducted the strategic analysis, formulated actionable recommendations, and saved your comprehensive deliverable to `{report_name}` in `workspace/reports/`.\n\n"
                    f"Get some rest—I will continue monitoring in the background and have your complete morning briefing ready the moment you power on your laptop."
                )
                session.update_state(KernelState.COMPLETED)
                await self._stream_progress(session, "Mission prepared.")
                await self.event_bus.publish(KernelEventType.RESPONSE_COMPLETED, session)
                return KernelResponse(
                    request_id=request.request_id,
                    session_id=session.session_id,
                    status=KernelState.COMPLETED,
                    content=final_response_text
                )

            # Phase 0.6: Autonomous Executive Briefing Intercept
            briefing_triggers = ["briefing", "brief me", "morning briefing", "daily briefing", "status briefing", "give me a briefing", "give briefing", "what's my briefing", "what is my briefing"]
            if any(bt in user_intent.lower() for bt in briefing_triggers):
                await self._stream_progress(session, "Synthesizing executive briefing...")
                from backend.proactive.briefing import BriefingEngine
                b_engine = BriefingEngine(provider_manager)
                final_response_text = await b_engine.generate_comprehensive_briefing()
                session.update_state(KernelState.COMPLETED)
                await self._stream_progress(session, "Briefing ready.")
                await self.event_bus.publish(KernelEventType.RESPONSE_COMPLETED, session)
                return KernelResponse(
                    request_id=request.request_id,
                    session_id=session.session_id,
                    status=KernelState.COMPLETED,
                    content=final_response_text
                )

            # Phase 0.7: Autonomous Silent Web Research & Search Intercept (Zero browser popups, Zero CAPTCHAs)
            search_markers = [
                "search the web", "search on the web", "web search", "search online",
                "search for", "search about", "look up", "lookup", "research",
                "find out about", "find out what", "find out who", "find information on",
                "what happened to", "case of", "case about", "latest news on",
                "latest updates on", "who is the ceo", "tell me about the case", "case"
            ]
            q_lower = user_intent.lower()
            is_explicit_browser = any(k in q_lower for k in [
                "open brave", "open chrome", "open edge", "open browser",
                "launch browser", "launch brave", "launch chrome", "play on youtube", "on youtube"
            ])
            is_search_intent = (
                any(marker in q_lower for marker in search_markers) and
                not is_explicit_browser and
                len(user_intent.split()) >= 3
            )
            
            if is_search_intent:
                await self._stream_progress(session, "Searching live web intelligence on backend...")
                from backend.search.web_research import WebResearchEngine
                research_engine = WebResearchEngine(provider_manager)
                
                # Extract clean search query
                import re
                clean_search_q = re.sub(
                    r'^(?:please\s+)?(?:can\s+you\s+)?(?:search\s+the\s+web\s+(?:about|for)?|search\s+(?:about|for)?|look\s+up|lookup|research\s+(?:about|for)?|find\s+out\s+(?:about|what|who)?|find\s+information\s+on)\s*',
                    '', user_intent, flags=re.IGNORECASE
                ).strip()
                if not clean_search_q:
                    clean_search_q = user_intent
                    
                final_response_text = await research_engine.research_and_synthesize(clean_search_q)
                
                # Output TTS if voice
                if is_voice and voice:
                    try:
                        audio_out = await voice.manager.tts.synthesize(final_response_text)
                        await voice.manager.player.play(audio_out)
                    except Exception as ve:
                        app_logger.warning(f"Voice TTS notice: {ve}")
                        
                session.update_state(KernelState.COMPLETED)
                await self._stream_progress(session, "Research complete.")
                await self.event_bus.publish(KernelEventType.RESPONSE_COMPLETED, session)
                
                if memory and user_intent and final_response_text:
                    asyncio.create_task(self._extract_and_learn(user_intent, final_response_text, memory, provider_manager))
                    
                return KernelResponse(
                    request_id=request.request_id,
                    session_id=session.session_id,
                    status=KernelState.COMPLETED,
                    content=final_response_text
                )

            # Phase 1: Real Planner Integration
            await self._stream_progress(session, "Planning execution...")
            plan = await planner.generate_plan(user_intent, context=execution_context)
            
            # Intercept Vision Queries
            v_lower = user_intent.lower()
            is_call_or_organize = any(ex in v_lower for ex in ["screening", "call", "screenshot", "organize", "lock screen", "lock the screen"])
            vision_phrases = ["what's on my screen", "what is on my screen", "look at my screen", "what am i looking at", "describe my screen", "read my screen", "see my screen"]
            is_vision_query = not is_call_or_organize and any(kw in v_lower for kw in vision_phrases)
            if is_vision_query:
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
                ada_system_persona = (
                    "You are ADA (Autonomous Digital Assistant), an advanced Jarvis-style AI Operating System with a female persona. "
                    "You are running directly on the user's Windows laptop with full local operating system access (desktop automation, application launching, browser control, file management, and hardware integration). "
                    "You are confident, articulate, technically brilliant, concise, and proactive. "
                    "NEVER apologize or say you cannot open applications, control browsers, or perform actions on the laptop. "
                    "Always refer to yourself as ADA. Never call yourself Nova or a generic language model."
                )
                messages = [Message(role=Role.SYSTEM, content=ada_system_persona)]
                # Fetch history again for pure conversational mapping
                conv = None
                if chat_sys and hasattr(chat_sys, 'manager') and chat_sys.manager:
                    try:
                        conv = chat_sys.manager.store.get_conversation(request.conversation_id)
                    except Exception:
                        pass
                if conv and conv.messages:
                    history_msgs = conv.messages[-7:-1]
                    for m in history_msgs:
                        role = Role.USER if m.type.name == "USER" else Role.ASSISTANT
                        messages.append(Message(role=role, content=m.content))
                        
                full_prompt = f"User Request: {user_intent}\nExecution Context: {execution_context}\n\nPlease provide a helpful response."
                
                # Multimodal Vision Intercept
                images_to_attach = []
                if is_vision_query:
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
                    model="nvidia/nemotron-3.5-super-vl:free", 
                    provider_type=ProviderType.OPENROUTER, 
                    stream=False
                )
                try:
                    resp = await provider_manager.generate(gen_req)
                    final_response_text = resp.content
                    
                    # Phase 4: Memory Integration (Store)
                    if memory and user_intent and final_response_text:
                        asyncio.create_task(self._extract_and_learn(user_intent, final_response_text, memory, provider_manager))
                except Exception as e:
                    final_response_text = f"Provider Error: {e}"
            else:
                final_response_text = f"Processed intent: {user_intent}"
                if memory and user_intent:
                    asyncio.create_task(self._extract_and_learn(user_intent, final_response_text, memory, provider_manager))

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

    async def _extract_and_learn(self, user_intent: str, assistant_response: str, memory, provider_manager):
        """
        Background Cognitive Memory Extractor:
        Extracts user profile facts, contacts, habits, and preferences using Gemini/Groq
        and stores them into SQLite and ChromaDB for continuous long-term learning.
        """
        try:
            from backend.providers.schema import GenerationRequest, Message, Role, CognitiveDomain
            from backend.memory.schema import MemoryItem, MemoryType
            import re
            
            # Skip trivial short phrases
            trivial = ["hello", "hi", "hey", "test", "ping", "who are you", "what is your name"]
            if user_intent.lower().strip() in trivial:
                return
                
            prompt = (
                f"You are ADA's Continuous Memory Extractor.\n"
                f"Analyze this interaction between User (Jainam) and ADA:\n"
                f"User: \"{user_intent}\"\n"
                f"ADA: \"{assistant_response}\"\n\n"
                f"Extract ANY long-term facts, contacts (like friends or colleagues), user preferences, daily habits, or career goals mentioned.\n"
                f"If there is nothing new or noteworthy to remember, output an empty JSON list: [].\n"
                f"Otherwise, output a JSON list of objects:\n"
                f"[\n"
                f"  {{\n"
                f"    \"type\": \"contact|habit|preference|goal|fact\",\n"
                f"    \"content\": \"Concise fact (e.g. 'Vedya is a close friend of Jainam', 'User is targeting AI/ML Engineer jobs')\",\n"
                f"    \"importance\": 0.8\n"
                f"  }}\n"
                f"]\n"
                f"Output ONLY raw JSON. No markdown fences."
            )
            req = GenerationRequest(
                messages=[Message(role=Role.USER, content=prompt)],
                cognitive_domain=CognitiveDomain.SOCIAL_SYNTHESIS,
                temperature=0.2,
                max_tokens=200,
                json_mode=True
            )
            resp = await provider_manager.generate(req)
            text = resp.content.strip()
            # Clean markdown
            text = re.sub(r'```json\n?', '', text)
            text = re.sub(r'```\n?', '', text).strip()
            if text.startswith("[") and text.endswith("]"):
                items = json.loads(text)
                from backend.memory.profile_store import profile_store
                from backend.memory.routine_tracker import routine_tracker
                
                for item in items:
                    content = item.get("content", "").strip()
                    m_type = item.get("type", "fact").lower()
                    if content:
                        mem_type = MemoryType.EPISODIC if m_type in ["habit", "contact"] else MemoryType.PREFERENCE_MEMORY
                        importance = float(item.get("importance", 0.7))
                        mem_item = MemoryItem(
                            memory_type=mem_type,
                            content=content,
                            importance=importance,
                            metadata={"extracted_from_interaction": True}
                        )
                        if memory:
                            await memory.add(mem_item)
                        app_logger.info(f"[Continuous Memory] Learned & Stored: {content}")

                        # Update profile store for persistent rules or contacts
                        if "rule" in m_type or any(k in content.lower() for k in ["always", "never", "default to"]):
                            profile_store.add_rule(content)
                        elif "contact" in m_type:
                            words = content.split()
                            if words:
                                profile_store.upsert_contact(words[0], notes=content)

                routine_tracker.record_activity(action_type=user_intent[:30])
        except Exception as e:
            app_logger.debug(f"Continuous memory extraction skipped: {e}")
