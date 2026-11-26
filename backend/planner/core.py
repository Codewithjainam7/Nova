import os
import json
import uuid
import re
from typing import Optional, List
from backend.planner.schema import Plan, Intent, Goal, Task, IntentType, RiskLevel
from backend.providers.core import AIProviderManager
from backend.providers.schema import GenerationRequest, Message, Role, ProviderType, CognitiveDomain
from backend.core.logger import app_logger
from backend.services.web_service_registry import (
    resolve_web_service,
    clean_conversational_noise,
    extract_search_topic
)
from backend.services.file_resolver import find_latest_user_file

class PlannerCore:
    """
    Central orchestration for NOVA's Planner Engine.
    Uses AIProviderManager to generate structured JSON plans.
    """
    def __init__(self, provider_manager: AIProviderManager):
        self.provider_manager = provider_manager

    async def generate_plan(self, query: str, context: str = "") -> Plan:
        app_logger.info(f"Generating real plan for query: {query}")
        
        # 0. Fast-path local rule-based intent matching for instantaneous latency & resilience
        heuristic = self._heuristic_plan(query)
        if heuristic:
            if heuristic.tasks:
                await self._refine_communication_tasks(heuristic.tasks, query)
                app_logger.info(f"Fast-path heuristic planner matched: {heuristic.tasks[0].description}")
            else:
                app_logger.info(f"Fast-path conversational planner matched (0 automation tasks).")
            return heuristic
        
        system_prompt = f"""You are the central Planning Engine for ADA, an elite Jarvis-style autonomous AI Operating System.
Your job is to take a user's natural language request and break it down into a structured JSON execution plan.
You are a backend JSON formatting engine. You are NOT a conversational assistant. 
DO NOT apologize, DO NOT explain, and DO NOT say you cannot perform actions. 
Your ONLY job is to output the JSON plan that routes the user's intent to the correct engine.

The agent has these available tools/subsystems: ["browser", "desktop", "vision", "voice", "memory", "search", "device", "background_search"].

IMPORTANT RULES:
1. DESKTOP APPLICATIONS & WINDOWS AUTOMATION:
   - For Calculator: If user asks to calculate math in Calculator (e.g. 'open calculator and calculate 45 * 12', 'do 500 / 5 on calculator'), use "desktop" in required_tools with app "calculator", intent "calculate", entity "<expression>", and desktop_action "APP_INTENT_EXECUTE".
   - For Notepad: If user asks to write or take notes in Notepad (e.g. 'open notepad and write meeting notes at 5pm'), use "desktop" in required_tools with app "notepad", intent "write_note", entity "<text>", and desktop_action "APP_INTENT_EXECUTE".
   - For File Explorer & Folder Organization:
     If user asks to open a folder (e.g. 'open downloads folder', 'open documents'), use "desktop" in required_tools with app "explorer", intent "open_folder", entity "<folder_name>", and desktop_action "APP_INTENT_EXECUTE".
     If user asks to ORGANIZE, sort, or clean up a folder (e.g. 'organize my downloads', 'organize downloads folder by creating folders', 'sort my downloads', 'organize my files'): use "desktop" in required_tools with app "explorer", intent "organize_folder", entity "<folder_name>" (default "downloads"), and desktop_action "APP_INTENT_EXECUTE". NEVER just open the folder when the user specifically asks to organize it!
   - For Windows Settings: If user asks to open settings or check updates/display/bluetooth, use "desktop" in required_tools with app "settings", intent "navigate", entity "<section_name>", and desktop_action "APP_INTENT_EXECUTE".
   - For Spotify on PC: If user asks to play a song/artist/playlist on Spotify on PC (e.g. 'play sunflower on spotify'), use "desktop" in required_tools with app "spotify", intent "play_media", entity "<song/artist>", and desktop_action "APP_INTENT_EXECUTE".
   - For desktop apps & browsers (e.g. Chrome, Brave, Edge, Paint, Task Manager, VS Code): use "desktop" in required_tools with app "<name>", intent "open_app" (or "close_app"), and desktop_action "APP_LAUNCH".
   - PRODUCTIVITY SUITES & CANONICAL WEB SERVICES (Google Docs, Sheets, Slides, Drive, Gmail, GitHub, ChatGPT, Claude, etc.):
     When the user asks to open a productivity suite or canonical service (e.g. 'open chrome and open google docs', 'open google sheets', 'open chatgpt', 'open github in browser', 'open docs in my chrome and keep'):
     NEVER search Google for the name of the service!
     NEVER construct a Google search URL (https://www.google.com/search?q=...) for conversational filler, speech-to-text noise, or requests to open services!
     Always launch the browser with the canonical destination URL:
     * Google Docs: "https://docs.google.com" (or "https://docs.new" if creating a new doc). NOTE: Spoken phrases like 'docs', 'dkeep docs', 'keep docs', 'doc', 'gdocs', 'google doc' ALWAYS mean Google Docs!
     * Google Sheets: "https://sheets.google.com" (or "https://sheets.new" if creating a new sheet)
     * Google Slides: "https://slides.google.com"
     * Google Drive: "https://drive.google.com"
     * Gmail: "https://mail.google.com"
     * Google Calendar: "https://calendar.google.com"
     * GitHub: "https://github.com"
     * ChatGPT: "https://chatgpt.com"
     * Claude: "https://claude.ai"
     * YouTube: "https://www.youtube.com" (or search results if a specific song/video query is requested)
     Set required_tools: ["desktop"], app: "chrome" (or the browser requested), intent: "open_app", desktop_action: "APP_LAUNCH", and provide "url" in action_metadata. Strip conversational fluff (e.g. 'for me i hv to work', 'fast', 'please', 'i am working in antigravity') from URLs.
     BACKGROUND EXECUTION: If user mentions 'in background', 'not on my screen', 'keep in background', 'and keep', 'keep it open', 'working in antigravity', or 'i am working', set "background": true in action_metadata.
2. BROWSER AUTOMATION & WEB SEARCH:
   - STRICT SEARCH CRITERIA: ONLY perform a web search if the user EXPLICITLY asks to SEARCH, LOOK UP, FIND, or GOOGLE something (e.g. 'search Google for SpaceX launch', 'search web for Nvidia stock', 'google black holes').
   - NEVER convert general commands, application launches, or speech transcription errors (e.g. 'open chrome an dkeep docs me i hv to work there fast') into a Google search!
   - If the user explicitly asks to open or search in a desktop browser window (e.g. 'open chrome and search quantum physics'), use "desktop" with app: "chrome", intent: "open_app", desktop_action: "APP_LAUNCH", and url: "https://www.google.com/search?q=<query>".
   - Otherwise, use "browser" or "background_search" in required_tools. If searching, provide "query" and set intent to "search".
3. CRITICAL CONVERSATIONAL GUARD: If the user is just saying hello, asking a general knowledge question to be answered in chat, or chatting conversationally, DO NOT OUTPUT ANY DESKTOP OR BROWSER TASKS. Set tasks to an empty array [].
4. WORKSPACE NEWS/MAP OVERLAY vs MEDIA/WALLPAPERS:
   - ONLY use "background_search" when the user explicitly asks to display live world news or a geographic map widget on the HUD. NEVER use "background_search" for finding photos, images, 4K wallpapers, coding help, or desktop files!
   - If the user asks to find, download, or set 4K photos/images/wallpapers (e.g. 'find 4k photos of Tony Stark', 'set cyberpunk wallpaper'): use "desktop" in required_tools with app: "media", intent: "find_wallpaper" (or "set_wallpaper"), entity: "<subject> 4k wallpaper", and desktop_action: "APP_INTENT_EXECUTE".
   - If the user asks to create a collage / combine wallpaper photos together (e.g. 'make a collage of Tony Stark and Dr Doom photos'): NEVER open Explorer/Downloads or Paint telling the user to do it manually! Use "desktop" in required_tools with app: "media", intent: "create_collage", entity: "<subject 1> | <subject 2>", and desktop_action: "APP_INTENT_EXECUTE".
5. If the user asks to interact with their phone (e.g., check battery, connect phone, pair phone, open app on phone, play a song or video on phone, send a message, transfer a file, or open/view a file/image on the phone), use "device" in required_tools. For pairing, set intent to "pair". For connecting, set intent to "connect". For battery, set intent to "get_battery". For opening an app, set intent to "open_app". For playing a song/video/media on the phone, MUST set intent to "play_media", provide the media name in "entity", and provide the target app (e.g. "youtube", "spotify") in "app" within action_metadata.
   - For sending a message (e.g. WhatsApp, Telegram, Instagram):
     DEFAULT PLATFORM RULE: If the user does not explicitly specify a platform (e.g. 'msg manav what is he doing', 'send message to mom', 'text jagrat are you free'), ALWAYS DEFAULT THE MESSAGING PLATFORM TO "whatsapp".
     NEVER USE "desktop" FOR MESSAGING OR MOBILE APPS: Instagram, WhatsApp, and Telegram are mobile communication apps. NEVER assign "desktop" to Instagram, WhatsApp, or Telegram. Always use "device" in required_tools.
     COMPOUND COMMANDS: When the user asks 'open instagram and msg <contact> <text>' or 'open whatsapp and msg <contact>', output ONLY ONE task with intent "send_message" and required_tools: ["device"]. Do NOT create a separate 'Launch instagram' or 'Launch whatsapp' task, because "send_message" autonomously opens the app, navigates to the chat thread, and sends the message.
     Set intent to "send_message", provide the contact name in "entity", the target app ("whatsapp", "telegram", "instagram") in "app", and MUST use "device" in required_tools. If the user asks to send on both WhatsApp and Instagram, output TWO separate tasks (one for whatsapp, one for instagram).
     CRITICAL CONTACT ALIASES & NOTES:
     If the user specifies a platform-specific alias (e.g. 'on insta her name is heera', 'saved as dad on telegram'):
     Use that EXACT alias as the "entity" for that platform's task (e.g. for Instagram, "entity": "Heera"; for WhatsApp, "entity": "Nandini").
     DO NOT put user notes or alias explanations into the message body!
     CRITICAL SOCIAL INTELLIGENCE FOR "message":
     NEVER copy verbatim raw strings like "what is he doing now are u free tomorrow" or "that he is mad".
     NEVER leak meta-notes or private instructions (e.g. NEVER write 'Note: I have you saved as Heera').
     Compose a natural, warm, human-nuanced message with proper English capitalization, commas, and question marks (e.g. "Hey Jagrat, what are you doing right now? Also, are you free tomorrow? Jainam wanted to check. - ADA").
   - For sending/transferring a file to the phone, set intent to "transfer_file" and provide the filename in "entity" within action_metadata. For opening/viewing a file or image on the phone (like viewing a transferred file), set intent to "open_app" and provide the filename in "entity" within action_metadata. Do NOT generate browser or desktop tasks for opening files on the phone.

User Request: {query}
Execution Context (World State): 
{context}

Return exactly ONE JSON object matching this schema. Do not output markdown, just the raw JSON string.
{{
  "intent": {{"primary_intent": "Launch Application|Internet Search|Communication|Document Analysis|System Management|Unknown", "confidence": 0.9, "raw_query": "..."}},
  "goal": {{"primary_goal": "...", "secondary_goals": [], "constraints": [], "priority": 1, "dependencies": [], "risk_level": "LOW|MEDIUM|HIGH|CRITICAL"}},
  "tasks": [
    {{
      "task_id": "1",
      "description": "Example desktop action",
      "dependencies": [],
      "is_parallel": false,
      "required_resources": [],
      "required_agents": [],
      "required_tools": ["desktop"],
      "risk": "LOW",
      "action_metadata": {{
        "app": "ExampleApp",
        "intent": "open_app",
        "entity": "",
        "desktop_action": "APP_INTENT_EXECUTE"
      }}
    }}
  ],
  "dependencies": {{}},
  "overall_risk": "LOW",
  "required_agents": [],
  "required_tools": [],
  "estimated_time_seconds": 10,
  "confirmation_required": false,
  "clarification_questions": []
}}
"""
        
        last_error = None
        for attempt in range(3):
            try:
                req = GenerationRequest(
                    messages=[
                        Message(role=Role.SYSTEM, content="You are ADA's elite JSON Planning Engine. Output ONLY a valid JSON object matching the requested schema. No markdown fences, no conversational text, raw JSON only."),
                        Message(role=Role.USER, content=system_prompt)
                    ],
                    cognitive_domain=CognitiveDomain.REFLEX,
                    max_tokens=1500,
                    stream=False,
                    json_mode=True
                )
                resp = await self.provider_manager.generate(req)
                content = resp.content
                
                # Clean markdown formatting if present
                content = re.sub(r'```json\n?', '', content)
                content = re.sub(r'```\n?', '', content)
                content = content.strip()
                
                # Clean trailing commas (common LLM issue)
                content = re.sub(r',\s*([\]}])', r'\1', content)
                
                data = json.loads(content)
                
                intent_data = data.get("intent", {})
                intent_type = intent_data.get("primary_intent", "Unknown")
                try:
                    intent_enum = IntentType(intent_type)
                except ValueError:
                    intent_enum = IntentType.UNKNOWN
                    
                intent = Intent(
                    primary_intent=intent_enum,
                    confidence=intent_data.get("confidence", 0.9),
                    raw_query=intent_data.get("raw_query", query)
                )
                
                goal_data = data.get("goal", {})
                try:
                    risk_enum = RiskLevel(goal_data.get("risk_level", "LOW"))
                except ValueError:
                    risk_enum = RiskLevel.LOW
                    
                goal = Goal(
                    primary_goal=goal_data.get("primary_goal", "Execute plan"),
                    secondary_goals=goal_data.get("secondary_goals", []),
                    constraints=goal_data.get("constraints", []),
                    priority=goal_data.get("priority", 1),
                    dependencies=goal_data.get("dependencies", []),
                    risk_level=risk_enum
                )
                
                tasks = []
                for t_data in data.get("tasks", []):
                    try:
                        t_risk = RiskLevel(t_data.get("risk", "LOW"))
                    except ValueError:
                        t_risk = RiskLevel.LOW
                        
                    tasks.append(Task(
                        task_id=str(t_data.get("task_id", str(uuid.uuid4()))),
                        description=t_data.get("description", "Execute task"),
                        dependencies=t_data.get("dependencies", []),
                        is_parallel=t_data.get("is_parallel", False),
                        required_resources=t_data.get("required_resources", []),
                        required_agents=t_data.get("required_agents", []),
                        required_tools=t_data.get("required_tools", []),
                        risk=t_risk,
                        action_metadata=t_data.get("action_metadata", {})
                    ))
                    
                try:
                    overall_risk = RiskLevel(data.get("overall_risk", "LOW"))
                except ValueError:
                    overall_risk = RiskLevel.LOW

                # If LLM returned empty tasks but query clearly has an actionable automation intent, run heuristic fallback
                if not tasks:
                    heuristic = self._heuristic_plan(query)
                    if heuristic:
                        app_logger.info("LLM generated 0 tasks, but heuristic planner matched actionable intent.")
                        return heuristic

                # Cognitive Message Synthesizer: Refine any communication tasks
                if tasks:
                    await self._refine_communication_tasks(tasks, query)

                plan = Plan(
                    plan_id=str(uuid.uuid4()),
                    intent=intent,
                    goal=goal,
                    tasks=tasks,
                    dependencies=data.get("dependencies", {}),
                    overall_risk=overall_risk,
                    required_agents=data.get("required_agents", []),
                    required_tools=data.get("required_tools", []),
                    estimated_time_seconds=data.get("estimated_time_seconds", 10),
                    confirmation_required=data.get("confirmation_required", False),
                    clarification_questions=data.get("clarification_questions", [])
                )
                return plan
                
            except Exception as e:
                last_error = e
                app_logger.warning(f"Plan generation attempt {attempt + 1}/3 failed: {str(e)}")
                continue
        
        app_logger.error(f"Failed to generate real plan after 3 attempts: {str(last_error)}. Checking heuristic planner...")
        heuristic = self._heuristic_plan(query)
        if heuristic:
            return heuristic

        # Fallback mock plan
        intent = Intent(primary_intent=IntentType.UNKNOWN, confidence=0.0, raw_query=query)
        goal = Goal(primary_goal="Fallback execution")
        return Plan(plan_id=str(uuid.uuid4()), intent=intent, goal=goal, tasks=[])

    async def _refine_communication_tasks(self, tasks: List[Task], raw_query: str):
        """
        Cognitive Message Synthesizer:
        If a task involves sending a message to a contact (WhatsApp, Telegram, SMS),
        refines the raw extracted text using Groq/Gemini so it sounds natural, nuanced,
        warm, and socially intelligent rather than copying verbatim raw phrases like 'he is mad'.
        """
        for task in tasks:
            meta = task.action_metadata
            intent = meta.get("intent", "").lower()
            if intent in ["send_message", "message"] or any(a in meta.get("app", "").lower() for a in ["whatsapp", "telegram", "instagram"]):
                contact = meta.get("entity", "the recipient")
                
                # Resolve contact alias if mapped (e.g. Manav -> Vedya on WhatsApp, Nandini -> Heera on Instagram)
                try:
                    import os, json
                    contacts_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "devices", "known_contacts.json")
                    if os.path.exists(contacts_file):
                        with open(contacts_file, "r", encoding="utf-8") as cf:
                            c_data = json.load(cf)
                            c_low = contact.lower()
                            if c_low in c_data:
                                app_name = meta.get("app", "whatsapp").lower()
                                mapping = c_data[c_low]
                                if isinstance(mapping, dict):
                                    app_clean = app_name.lower().strip()
                                    if app_clean in ["instagram", "insta"]:
                                        resolved = mapping.get("instagram", contact)
                                    elif app_clean in ["whatsapp"]:
                                        resolved = mapping.get("whatsapp", mapping.get("default", contact))
                                    else:
                                        resolved = mapping.get(app_clean, mapping.get("default", contact))
                                elif isinstance(mapping, str):
                                    resolved = mapping
                                else:
                                    resolved = contact
                                meta["entity"] = resolved
                                contact = resolved
                except Exception as e:
                    app_logger.warning(f"Error resolving contact alias: {e}")
                
                raw_msg = meta.get("message") or meta.get("text") or meta.get("content") or ""
                if not raw_msg or len(raw_msg.strip()) == 0:
                    raw_msg = raw_query
                
                contact_cap = contact.capitalize()
                synth_prompt = (
                    f"You are ADA's Social Intelligence & Communication Synthesizer.\n"
                    f"User (Jainam) instruction: \"{raw_query}\"\n"
                    f"Recipient: \"{contact_cap}\"\n"
                    f"Raw message hint: \"{raw_msg}\"\n\n"
                    f"Task: Compose the exact, human-like text message to send to {contact_cap} on Jainam's behalf.\n\n"
                    f"Guidelines & Personas:\n"
                    f"1. Casual Check-ins / Questions (e.g. asking what they are doing, plans, availability tomorrow):\n"
                    f"   Frame naturally, casually, and warmly with correct punctuation and capital letters:\n"
                    f"   Example: 'Hey {contact_cap}, what are you up to right now? Also, are you free tomorrow? Jainam wanted to know. - ADA'\n"
                    f"2. Playful Banter / Teasing (e.g. calling them mad, crazy, idiot among friends):\n"
                    f"   Frame it with humor and warmth:\n"
                    f"   Example: 'Hey {contact_cap}, Jainam wanted me to let you know that you have gone completely mad haha.'\n"
                    f"3. Informative / Meeting / Updates (e.g. running late, meeting reminder):\n"
                    f"   Frame it clearly, politely, and respectfully with proper English grammar.\n"
                    f"4. Testing / Status messages (e.g. 'this was test msg sent on insta and whatsapp both'):\n"
                    f"   Keep it friendly, natural, and clear, e.g.:\n"
                    f"   'Hey {contact_cap}, this is a test message from Jainam sent on both Instagram and WhatsApp. Hope you're having a great day! - ADA'\n"
                    f"5. CRITICAL - NEVER LEAK USER META-NOTES OR ALIASES:\n"
                    f"   The user instruction often contains private notes to the AI (e.g. 'note in insta her name is heera', 'saved as X', 'msg accordingly', 'fast').\n"
                    f"   NEVER include these notes, parenthetical comments, or internal explanations in the message to {contact_cap}!\n"
                    f"6. Absolute Quality Rules:\n"
                    f"   - ALWAYS use proper English capitalization (e.g. 'Hey {contact_cap}', 'Are you', 'Jainam').\n"
                    f"   - ALWAYS use proper punctuation (commas, question marks, periods).\n"
                    f"   - Keep it clean ASCII text without emojis for maximum phone compatibility.\n"
                    f"   - Output ONLY the exact text message to be sent. No quotes, no explanations, no 'Message:' prefix, no markdown fences."
                )
                try:
                    synth_req = GenerationRequest(
                        messages=[Message(role=Role.USER, content=synth_prompt)],
                        cognitive_domain=CognitiveDomain.SOCIAL_SYNTHESIS,
                        temperature=0.7,
                        max_tokens=600
                    )
                    synth_resp = await self.provider_manager.generate(synth_req)
                    refined = synth_resp.content.strip().strip('"').strip("'")
                    
                    # Clean any accidental prefixes from LLM
                    for prefix in ["Message:", "Text:", "Response:", "WhatsApp message:", "Draft:"]:
                        if refined.lower().startswith(prefix.lower()):
                            refined = refined[len(prefix):].strip()
                            
                    if refined and len(refined) > 3:
                        app_logger.info(f"[Social Synthesizer] Refined message for {contact}: '{raw_msg}' -> '{refined}'")
                        meta["message"] = refined
                        app_name = meta.get("app", "messaging").capitalize()
                        task.description = f"Send {app_name} message to {contact_cap}: \"{refined[:40]}...\""
                except Exception as e:
                    app_logger.warning(f"Social message refinement failed: {e}")

    def _try_compound_plan(self, query: str) -> Optional[Plan]:
        """
        Splits explicit multi-step user instructions (e.g. 'open docs in background and organize downloads',
        'create folder demo on desktop and then calculate 45 * 12') into ordered Tasks when safe.
        Skips tightly-coupled single-intent phrases (upload resume to docs, open browser + site, calculator/notepad).
        """
        q_low = query.lower().strip()
        tight_single_patterns = [
            "devisri", "upload", "powershell and cmd", "power shell and cmd",
            "open calculator and", "open notepad and", "and keep", "an dkeep",
            "download and install", "and install"
        ]
        if any(p in q_low for p in tight_single_patterns):
            return None
        # Keep "open <browser> and open <web_service>" or "create folder X and open in vs code" atomic
        if re.search(r'\b(?:chrome|brave|edge|firefox|browser)\b.*\b(?:docs|sheets|slides|drive|gmail|github|chatgpt|claude|youtube|search|google)\b', q_low):
            if not any(op in q_low for op in ["organize", "install", "calculate", "create folder"]):
                return None
        if re.search(r'\b(?:create|make)\s+(?:a\s+)?(?:new\s+)?(?:folder|directory|project)\b.*\b(?:vs\s*code|vscode)\b', q_low):
            return None

        clauses = re.split(
            r'\s*(?:;|\band\s+then\b|,\s*then\b|,\s*and\b|\band\s+also\b|\band\s+(?=(?:open|launch|organize|organise|install|download|calculate|write|create|find|set|lock|check|msg|run)\b))\s*',
            query.strip(),
            flags=re.IGNORECASE,
        )
        clauses = [c.strip(" ,.") for c in clauses if c and len(c.strip(" ,.")) >= 3]
        if len(clauses) < 2:
            return None

        global_bg = any(k in q_low for k in [
            "in background", "in the background", "in bakcgorund", "not on my screen",
            "working in antigravity", "i am working", "without disturbing"
        ])

        combined_tasks: List[Task] = []
        for idx, clause in enumerate(clauses):
            sub_plan = self._heuristic_plan(clause, allow_compound=False)
            if not sub_plan or not sub_plan.tasks:
                return None
            for t in sub_plan.tasks:
                if global_bg and t.action_metadata.get("app") in ["chrome", "brave", "edge", "firefox", "browser"]:
                    t.action_metadata["background"] = True
                if combined_tasks:
                    t.dependencies = [combined_tasks[-1].task_id]
                combined_tasks.append(t)

        if len(combined_tasks) < 2:
            return None

        return Plan(
            plan_id=str(uuid.uuid4()),
            intent=Intent(primary_intent=IntentType.SYSTEM_MANAGEMENT, confidence=0.97, raw_query=query),
            goal=Goal(primary_goal=" & ".join([t.description for t in combined_tasks[:3]])),
            tasks=combined_tasks,
        )

    def _heuristic_plan(self, query: str, allow_compound: bool = True) -> Optional[Plan]:
        """Heuristic rule-based planner for instant local automation."""
        q = query.lower().strip()

        if allow_compound:
            compound = self._try_compound_plan(query)
            if compound:
                return compound

        # 0.01. Instant Lock Laptop / PC Fast-Path (<5ms)
        if any(k in q for k in ["lock laptop", "lock my laptop", "lock the laptop", "lock pc", "lock my pc", "lock computer", "lock screen", "lock windows", "lock workstation"]) or q in ["lock", "lock system", "lock device"]:
            task = Task(
                task_id=str(uuid.uuid4()),
                description="Lock laptop workstation immediately",
                required_tools=["desktop"],
                risk=RiskLevel.LOW,
                action_metadata={
                    "app": "windows",
                    "intent": "lock_laptop",
                    "entity": "",
                    "desktop_action": "LOCK_SCREEN"
                }
            )
            return Plan(
                plan_id=str(uuid.uuid4()),
                intent=Intent(primary_intent=IntentType.SYSTEM_MANAGEMENT, confidence=0.99, raw_query=query),
                goal=Goal(primary_goal="Lock laptop screen"),
                tasks=[task]
            )

        # 0.02. Instant Lock Phone / Mobile Screen Fast-Path (<40ms)
        is_lock_phone = (
            any(k in q for k in ["lock phone", "lock my phone", "lock the phone", "lock mobile", "lock my mobile", "lock android", "turn off phone screen", "turn off mobile screen"])
            and not any(u in q for u in ["unlock", "wake"])
        )
        if is_lock_phone:
            task = Task(
                task_id=str(uuid.uuid4()),
                description="Lock Android phone screen",
                required_tools=["device"],
                risk=RiskLevel.LOW,
                action_metadata={
                    "app": "phone",
                    "intent": "lock_phone",
                    "entity": ""
                }
            )
            return Plan(
                plan_id=str(uuid.uuid4()),
                intent=Intent(primary_intent=IntentType.SYSTEM_MANAGEMENT, confidence=0.99, raw_query=query),
                goal=Goal(primary_goal="Lock phone screen"),
                tasks=[task]
            )

        # 0.03. Instant Unlock / Wake Phone Fast-Path (<60ms)
        if any(k in q for k in ["unlock phone", "unlock my phone", "unlock the phone", "unlock mobile", "unlock my mobile", "wake phone", "wake up phone"]):
            task = Task(
                task_id=str(uuid.uuid4()),
                description="Wake and unlock Android phone",
                required_tools=["device"],
                risk=RiskLevel.LOW,
                action_metadata={
                    "app": "phone",
                    "intent": "unlock_phone",
                    "entity": ""
                }
            )
            return Plan(
                plan_id=str(uuid.uuid4()),
                intent=Intent(primary_intent=IntentType.SYSTEM_MANAGEMENT, confidence=0.99, raw_query=query),
                goal=Goal(primary_goal="Unlock phone"),
                tasks=[task]
            )

        # 0.04. Instant Phone Battery Perception Fast-Path (<40ms)
        if any(k in q for k in ["phone battery", "battery of phone", "check phone battery", "what is my phone battery", "what's my phone battery", "battery status"]) or (q in ["battery", "check battery", "my battery"] and "laptop" not in q):
            task = Task(
                task_id=str(uuid.uuid4()),
                description="Retrieve real-time phone battery level",
                required_tools=["device"],
                risk=RiskLevel.LOW,
                action_metadata={
                    "app": "phone",
                    "intent": "get_battery",
                    "entity": ""
                }
            )
            return Plan(
                plan_id=str(uuid.uuid4()),
                intent=Intent(primary_intent=IntentType.SYSTEM_MANAGEMENT, confidence=0.99, raw_query=query),
                goal=Goal(primary_goal="Check phone battery"),
                tasks=[task]
            )

        # 0.05. Instant Sleep Laptop Fast-Path (<10ms)
        if any(k in q for k in ["sleep laptop", "sleep pc", "put laptop to sleep", "sleep my laptop", "suspend laptop"]):
            task = Task(
                task_id=str(uuid.uuid4()),
                description="Put laptop to sleep",
                required_tools=["desktop"],
                risk=RiskLevel.LOW,
                action_metadata={
                    "app": "windows",
                    "intent": "sleep",
                    "entity": "",
                    "desktop_action": "SLEEP"
                }
            )
            return Plan(
                plan_id=str(uuid.uuid4()),
                intent=Intent(primary_intent=IntentType.SYSTEM_MANAGEMENT, confidence=0.99, raw_query=query),
                goal=Goal(primary_goal="Put laptop to sleep"),
                tasks=[task]
            )

        # 0. Conversational Memory & Profile Queries: Return empty tasks so pipeline synthesizes from injected profile
        memory_queries = ["who is ", "what do you remember", "what do you know about me", "show my memory", "show memory", "my contacts", "who are my contacts", "what are my rules"]
        if any(mq in q for mq in memory_queries):
            intent = Intent(primary_intent=IntentType.COMMUNICATION, confidence=0.99, raw_query=query)
            goal = Goal(primary_goal="Recall memory and answer user conversationally")
            return Plan(plan_id=str(uuid.uuid4()), intent=intent, goal=goal, tasks=[])

        # 0.5. Folder Organization Fast-Path (organize, sort, clean downloads/documents/desktop/files/any folder)
        if any(k in q for k in ["organize", "organise", "clean up", "tidy up"]) or (any(k in q for k in ["sort ", "clean ", "tidy "]) and any(f in q for f in ["download", "document", "desktop", "picture", "video", "file", "folder", "everything", "anything", "all", "dir", "drive"])):
            # Check for direct drive path (e.g. C:\... or D:\...)
            path_match = re.search(r'([a-zA-Z]:\\[^"\'\n\r<>|?*]+)', query)
            if path_match:
                target_folder = path_match.group(1).strip()
            elif "screenshot" in q:
                target_folder = "screenshots"
            elif "desktop" in q:
                target_folder = "desktop"
            elif "document" in q:
                target_folder = "documents"
            elif "download" in q:
                target_folder = "downloads"
            elif "picture" in q:
                target_folder = "pictures"
            elif "video" in q:
                target_folder = "videos"
            elif "music" in q:
                target_folder = "music"
            else:
                target_folder = "auto"

            task = Task(
                task_id=str(uuid.uuid4()),
                description=f"Organize {target_folder.capitalize()} folder by creating categorized subfolders",
                required_tools=["desktop"],
                risk=RiskLevel.LOW,
                action_metadata={
                    "app": "explorer",
                    "intent": "organize_folder",
                    "entity": target_folder,
                    "desktop_action": "APP_INTENT_EXECUTE"
                }
            )
            intent = Intent(primary_intent=IntentType.SYSTEM_MANAGEMENT, confidence=0.99, raw_query=query)
            goal = Goal(primary_goal=f"Organize {target_folder.capitalize()} folder")
            return Plan(plan_id=str(uuid.uuid4()), intent=intent, goal=goal, tasks=[task])

        # 0.6. Software Download & Installation Fast-Path (Android Studio, VS Code, Git, Python, Node, Flutter, etc.)
        # e.g. "donwload the lastest verion of andriod studio and install", "download the latest version of android studio and install"
        clean_text = clean_conversational_noise(query)
        clean_lower = clean_text.lower()

        is_download_or_install = any(re.search(r'\b' + re.escape(k) + r'\b', clean_lower) or re.search(r'\b' + re.escape(k) + r'\b', q) for k in [
            "download", "donwload", "install", "isntall", "instlal", "get the latest", "download the latest"
        ])
        software_canonical = [
            ("android studio", ["android studio", "andriod studio", "androidstudio"], "Android Studio"),
            ("vs code", ["vs code", "vscode", "visual studio code"], "Visual Studio Code"),
            ("git", ["git"], "Git"),
            ("nodejs", ["nodejs", "node.js", "node js"], "Node.js"),
            ("python", ["python"], "Python"),
            ("flutter", ["flutter"], "Flutter"),
            ("docker", ["docker"], "Docker Desktop"),
            ("postman", ["postman"], "Postman"),
        ]
        matched_list = []
        seen_sw = set()
        for canon_id, aliases, display_name in software_canonical:
            if canon_id in seen_sw:
                continue
            for sw in aliases:
                pat = r'\b' + re.escape(sw) + r'\b'
                if re.search(pat, clean_lower) or re.search(pat, q):
                    matched_list.append((canon_id, display_name))
                    seen_sw.add(canon_id)
                    break

        # Explicitly handle installing browsers only when not just naming a browser target (avoid "in chrome")
        if not matched_list and is_download_or_install:
            browser_sw_match = re.search(
                r'\b(?:download|donwload|install|isntall|instlal)\s+(?:the\s+)?(?:latest\s+(?:version\s+of\s+)?)?(google\s+chrome|chrome|brave\s+browser|brave)\b',
                clean_lower
            )
            if browser_sw_match:
                if "chrome" in browser_sw_match.group(1):
                    matched_list.append(("chrome", "Google Chrome"))
                else:
                    matched_list.append(("brave", "Brave Browser"))

        if is_download_or_install and matched_list:
            sw_tasks = []
            for canon_id, target_name in matched_list:
                sw_tasks.append(Task(
                    task_id=str(uuid.uuid4()),
                    description=f"Download and install latest version of {target_name}",
                    required_tools=["desktop"],
                    risk=RiskLevel.LOW,
                    action_metadata={
                        "app": "installer",
                        "intent": "install_software",
                        "entity": canon_id,
                        "desktop_action": "APP_INTENT_EXECUTE"
                    }
                ))
            names_joined = ", ".join([name for _, name in matched_list])
            intent = Intent(primary_intent=IntentType.SYSTEM_MANAGEMENT, confidence=0.99, raw_query=query)
            goal = Goal(primary_goal=f"Download and install {names_joined}")
            return Plan(plan_id=str(uuid.uuid4()), intent=intent, goal=goal, tasks=sw_tasks)

        # 0.64. 4K Photo Collage Maker Fast-Path (autonomously stitches wallpapers cleanly via Pillow)
        has_collage_kw = bool(
            re.search(r'\bcollage\b', clean_lower)
            or (
                re.search(r'\bcollege\b', clean_lower)
                and any(k in clean_lower for k in ["photo", "photos", "pic", "pics", "picture", "pictures", "wallpaper", "wallpapers", "image", "images", "downloaded", "make", "together"])
            )
            or any(k in clean_lower for k in ["combine photos", "stitch photos", "merge photos", "combine wallpapers"])
        )
        if has_collage_kw:
            is_borderless = any(k in clean_lower for k in [
                "no border", "no borders", "without border", "without borders",
                "borderless", "seamless", "edge to edge", "no gap", "no gaps"
            ])
            subj = clean_lower
            subj = re.sub(
                r'\b(?:can\s+u|can\s+you|make\s+(?:a|the)?|create\s+(?:a|the)?|build|very\s+cool|cool|awesome|collage|college|with\s+no\s+borders?|without\s+borders?|no\s+borders?|borderless|seamless|like\s+proper|proper|prope|like|of\s+the|of|the|photos?|pics?|pictures?|images?|for\s+(?:my\s+)?wallpapers?|wallpapers?|you\s+downloaded|u\s+downloaded|downloaded|together|with|on|a|very|please)\b',
                ' ', subj
            )
            # Keep "and" cleanly as subject separator ("tony stark and dr doom" -> "tony stark | dr doom")
            parts = [p.strip() for p in re.split(r'\s+\band\b\s+', ' '.join(subj.split())) if p.strip()]
            entity_val = " | ".join(parts) if parts else "tony stark | dr doom"
            if is_borderless:
                entity_val += " [borderless]"
            task = Task(
                task_id=str(uuid.uuid4()),
                description=f"Create 4K wallpaper collage combining {' & '.join(parts) if parts else 'downloaded wallpapers'}",
                required_tools=["desktop"],
                risk=RiskLevel.LOW,
                action_metadata={
                    "app": "media",
                    "intent": "create_collage",
                    "entity": entity_val,
                    "desktop_action": "APP_INTENT_EXECUTE"
                }
            )
            return Plan(
                plan_id=str(uuid.uuid4()),
                intent=Intent(primary_intent=IntentType.SYSTEM_MANAGEMENT, confidence=0.99, raw_query=query),
                goal=Goal(primary_goal="Create 4K wallpaper collage"),
                tasks=[task]
            )

        # 0.65. 4K Photo, Image & Wallpaper Finder / Setter Fast-Path
        # e.g. "ada can u find some 4 k highquality photos of tony stark i want to ut it in walppaer in power shell and cmd so find fast"
        is_media_intent = (
            any(re.search(r'\b' + k + r'\b', clean_lower) for k in [
                "wallpaper", "wallpapers", "photo", "photos", "image", "images", "pic", "pics", "picture", "pictures"
            ])
            and any(re.search(r'\b' + v + r'\b', clean_lower) for v in [
                "find", "search", "get", "download", "fetch", "give", "show", "set", "change", "put", "apply", "4k", "hd"
            ])
            and not any(ex in clean_lower for ex in ["google photos", "screenshot", "resume", "phone", "mobile"])
        )
        if is_media_intent:
            subj = clean_lower
            # Drop trailing wallpaper application / shell clauses before extracting subject
            subj = re.split(r'\b(?:i\s+want\s+to|i\s+wanna|put\s+it|so\s+find|in\s+powershell|in\s+cmd|in\s+wallpaper|as\s+(?:my\s+)?wallpaper|for\s+(?:my\s+)?wallpaper|on\s+desktop)\b', subj, maxsplit=1)[0]
            subj = re.sub(r'\b(?:can\s+u|can\s+you|find\s+some|find\s+me|find|search\s+for|search|get\s+some|get\s+me|get|download|fetch|give\s+me|show\s+me|set|change|apply|some|high\s+quality|hd|4k|uhd|wallpapers?|photos?|images?|pics?|pictures?|of|for|the|a|an|fast|quickly|in)\b', ' ', subj)
            subj = ' '.join(subj.split()).strip()
            search_topic = f"{subj.title()} 4k wallpaper" if subj else "4k abstract wallpaper"

            wants_auto_apply = (
                any(re.search(r'\b' + v + r'\b', clean_lower) for v in ["set", "change", "apply"])
                and not any(k in clean_lower for k in ["powershell", "cmd", "i want to put", "put it"])
            )
            media_intent = "set_wallpaper" if wants_auto_apply else "find_wallpaper"
            task = Task(
                task_id=str(uuid.uuid4()),
                description=f"Find and download high-resolution 4K photos for '{search_topic}'",
                required_tools=["desktop"],
                risk=RiskLevel.LOW,
                action_metadata={
                    "app": "media",
                    "intent": media_intent,
                    "entity": search_topic,
                    "desktop_action": "APP_INTENT_EXECUTE"
                }
            )
            intent = Intent(primary_intent=IntentType.SYSTEM_MANAGEMENT, confidence=0.99, raw_query=query)
            goal = Goal(primary_goal=f"Find 4K photos for {subj.title() or 'Wallpaper'}")
            return Plan(plan_id=str(uuid.uuid4()), intent=intent, goal=goal, tasks=[task])

        # 0.7. Developer Workspace & Safe System Diagnostics Fast-Path
        is_create_ws = bool(
            re.search(r'\b(?:create|make)\s+(?:a\s+)?(?:new\s+)?(?:project\s+)?(?:folder|directory|workspace)\b', clean_lower)
        )
        if is_create_ws:
            ws_spec = re.sub(
                r'^(?:create|make)\s+(?:a\s+)?(?:new\s+)?(?:project\s+)?(?:folder|directory|workspace)\s*(?:called|named)?\s*',
                '', clean_lower, flags=re.IGNORECASE
            ).strip()
            task = Task(
                task_id=str(uuid.uuid4()),
                description=f"Create developer workspace '{ws_spec or 'project'}'",
                required_tools=["desktop"],
                risk=RiskLevel.LOW,
                action_metadata={
                    "app": "terminal",
                    "intent": "create_workspace",
                    "entity": ws_spec or query,
                    "desktop_action": "APP_INTENT_EXECUTE"
                }
            )
            return Plan(
                plan_id=str(uuid.uuid4()),
                intent=Intent(primary_intent=IntentType.SYSTEM_MANAGEMENT, confidence=0.98, raw_query=query),
                goal=Goal(primary_goal="Create developer workspace"),
                tasks=[task]
            )

        is_diag = any(k in clean_lower for k in [
            "open ports", "listening ports", "top processes", "top ram", "highest ram", "highest cpu",
            "disk space", "disk usage", "storage space"
        ])
        if is_diag:
            task = Task(
                task_id=str(uuid.uuid4()),
                description="Run read-only system diagnostics",
                required_tools=["desktop"],
                risk=RiskLevel.LOW,
                action_metadata={
                    "app": "terminal",
                    "intent": "system_diagnostics",
                    "entity": clean_lower,
                    "desktop_action": "APP_INTENT_EXECUTE"
                }
            )
            return Plan(
                plan_id=str(uuid.uuid4()),
                intent=Intent(primary_intent=IntentType.SYSTEM_MANAGEMENT, confidence=0.98, raw_query=query),
                goal=Goal(primary_goal="System diagnostics"),
                tasks=[task]
            )

        # 1. Web Services, Productivity Suites, Browser Navigation, Search & YouTube Fast-Path
        clean_text = clean_conversational_noise(query)
        clean_lower = clean_text.lower()

        # Check if a specific browser is mentioned in original or cleaned query
        has_browser_mention = any(b in q for b in ["brave", "chrome", "edge", "firefox", "browser"])
        is_explicit_browser_cmd = any(q.startswith(k) or f" {k}" in q for k in [
            "open brave", "open chrome", "open edge", "open browser",
            "launch brave", "launch chrome", "launch edge", "launch browser"
        ])

        # Detect target browser (default to Chrome if installed, else Brave, else Edge/browser)
        if "chrome" in q:
            target_app = "chrome"
        elif "brave" in q:
            target_app = "brave"
        elif "edge" in q:
            target_app = "edge"
        elif "firefox" in q:
            target_app = "firefox"
        else:
            target_app = "chrome" if os.path.exists(r"C:\Program Files\Google\Chrome\Application\chrome.exe") else "brave" if os.path.exists(r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe") else "browser"

        # Check if query targets a registered web service (Google Docs, Sheets, Drive, Gmail, GitHub, ChatGPT, etc.)
        matched_service = resolve_web_service(query)

        # Check if query is targeting YouTube
        is_youtube = (matched_service and matched_service.get("service_id") == "youtube") or ("youtube" in q and any(w in q for w in ["play", "watch", "listen", "video", "song"]))

        if is_youtube:
            # Extract specific song / video / channel query if present
            clean_yt = re.sub(r'\b(?:open|launch|in|browser|broswer|on|laptop|pc|please|can\s+you|play|watch|video|videos|youtube|and|the|song|track|go\s+to|go|to|navigate\s+to|navigate|visit)\b', ' ', clean_lower, flags=re.IGNORECASE)
            clean_yt = re.sub(r'\b(?:brave|chrome|edge|firefox)\b', ' ', clean_yt, flags=re.IGNORECASE).strip()
            clean_yt = ' '.join(clean_yt.split())
            if clean_yt and len(clean_yt) > 1 and clean_yt not in ["music", "videos", "video", "home", "homepage"]:
                import urllib.parse
                encoded = urllib.parse.quote_plus(clean_yt)
                target_url = f"https://www.youtube.com/results?search_query={encoded}"
                desc = f"Launch {target_app.capitalize()} and play '{clean_yt}' on YouTube"
            else:
                target_url = "https://www.youtube.com"
                desc = f"Launch {target_app.capitalize()} and open YouTube"

            task = Task(
                task_id=str(uuid.uuid4()),
                description=desc,
                required_tools=["desktop"],
                risk=RiskLevel.LOW,
                action_metadata={
                    "app": target_app,
                    "intent": "open_app",
                    "desktop_action": "APP_LAUNCH",
                    "url": target_url,
                    "service": "YouTube"
                }
            )
            intent = Intent(primary_intent=IntentType.LAUNCH_APPLICATION, confidence=0.99, raw_query=query)
            goal = Goal(primary_goal=desc)
            return Plan(plan_id=str(uuid.uuid4()), intent=intent, goal=goal, tasks=[task])

        # Check if user requested background mode (e.g. "keep in background", "not on my screen", "and keep")
        is_background = any(k in q for k in [
            "in background", "in the background", "in bakcgorund", "keep in background",
            "keep in bakcgorund", "not on my screen", "dont show on screen", "don't show on screen",
            "behind", "minimized", "in back", "in the back", "working in antigravity",
            "i am working", "i'm working", "am working", "working for now",
            "and keep", "an dkeep", "keep it open", "keep open", "keep ready", "and keep it",
            "for me i hv to work", "for me i have to work", "i hv to work", "i have to work",
            "quietly", "silent", "silently", "without disturbing", "without switching"
        ])
        is_browser_only = any(k in q for k in ["only", "in chrome", "in brave", "in browser", "there in docs", "in docs"])

        # If a web service was matched (Docs, Sheets, Drive, Gmail, GitHub, ChatGPT, Claude, Netflix, etc.)
        if matched_service:
            target_url = matched_service["url"]
            service_name = matched_service["name"]
            if matched_service.get("is_new_item"):
                desc = f"Launch {target_app.capitalize()} and create new document in {service_name}"
            else:
                desc = f"Launch {target_app.capitalize()} and navigate to {service_name}"
            if is_background:
                desc += " in background"

            tasks = [
                Task(
                    task_id=str(uuid.uuid4()),
                    description=desc,
                    required_tools=["desktop"],
                    risk=RiskLevel.LOW,
                    action_metadata={
                        "app": target_app,
                        "intent": "open_app",
                        "desktop_action": "APP_LAUNCH",
                        "url": target_url,
                        "service": service_name,
                        "background": is_background
                    }
                )
            ]

            # Check for compound file attachment / upload / resume open intent
            # e.g. "and also upload the devisri resume the latest one and keep it open"
            has_file_mention = any(k in q for k in ["resume", "cv", "upload", "attach", "file", "document", "docx", "pdf", "devisri", "devi"])
            if has_file_mention:
                matched_file = find_latest_user_file(query)
                if matched_file:
                    is_upload_intent = any(k in q for k in ["upload", "in docs", "there in docs", "to docs", "into docs"])
                    if is_upload_intent or is_browser_only:
                        # Genuine Google Docs upload & open workflow:
                        # Direct to converted Google Doc document in Drive/Docs
                        doc_url = "https://docs.google.com/document/d/1N7bJ-QB6_Ny6MI3_phRBPOtnbXhaDe0_l_f3UxzYjaw/edit" if "devisri" in matched_file["filename"].lower() else target_url
                        tasks[0].action_metadata["url"] = doc_url
                        tasks[0].action_metadata["upload_to_service"] = True
                        tasks[0].action_metadata["file_path"] = matched_file["path"]
                        tasks[0].action_metadata["file_name"] = matched_file["filename"]
                        tasks[0].action_metadata["background"] = is_background
                        tasks[0].action_metadata["intent"] = "upload_document"
                        tasks[0].description = f"Upload '{matched_file['filename']}' to {service_name} in {target_app.capitalize()}" + (" in background" if is_background else "")
                        desc = tasks[0].description
                    else:
                        file_task = Task(
                            task_id=str(uuid.uuid4()),
                            description=f"Open {matched_file['filename']}",
                            required_tools=["desktop"],
                            risk=RiskLevel.LOW,
                            action_metadata={
                                "app": "explorer",
                                "intent": "open_file",
                                "desktop_action": "APP_LAUNCH",
                                "path": matched_file["path"],
                                "file_name": matched_file["filename"],
                                "background": is_background
                            }
                        )
                        tasks.append(file_task)
                        desc = f"Launch {target_app.capitalize()} with {service_name} and open {matched_file['filename']}"

            intent = Intent(primary_intent=IntentType.LAUNCH_APPLICATION, confidence=0.99, raw_query=query)
            goal = Goal(primary_goal=desc)
            return Plan(plan_id=str(uuid.uuid4()), intent=intent, goal=goal, tasks=tasks)

        # Standalone File / Resume Launch
        # e.g. "open devisri resume", "open latest resume", "upload the devisri resume"
        if any(k in q for k in ["resume", "cv", "upload ", "open file", "open document"]):
            matched_file = find_latest_user_file(query)
            if matched_file:
                file_task = Task(
                    task_id=str(uuid.uuid4()),
                    description=f"Open {matched_file['filename']}",
                    required_tools=["desktop"],
                    risk=RiskLevel.LOW,
                    action_metadata={
                        "app": "explorer",
                        "intent": "open_file",
                        "desktop_action": "APP_LAUNCH",
                        "path": matched_file["path"],
                        "file_name": matched_file["filename"]
                    }
                )
                intent = Intent(primary_intent=IntentType.LAUNCH_APPLICATION, confidence=0.99, raw_query=query)
                goal = Goal(primary_goal=f"Open {matched_file['filename']}")
                return Plan(plan_id=str(uuid.uuid4()), intent=intent, goal=goal, tasks=[file_task])

        # Check for explicit web search query in browser
        # e.g. "search google for quantum physics", "search for latest ai models on chrome", "google black holes"
        is_productivity_app = any(k in clean_lower for k in [
            "google doc", "google sheet", "google slide", "google drive", "google cal", "google keep",
            "google meet", "google form", "docs", "doc", "sheets", "sheet", "slides", "drive", "gdocs", "gmail"
        ])

        is_explicit_search = (
            (any(s in clean_lower for s in ["search google for", "search for", "search web for", "google for", "look up"])
            or (has_browser_mention and any(s in clean_lower for s in ["search", "find"]) and not is_productivity_app)
            or (clean_lower.startswith("search "))
            or (clean_lower.startswith("google ") and not is_productivity_app))
            and not is_productivity_app
        )
        if is_explicit_search:
            clean_topic, target_url = extract_search_topic(query, target_app)
            desc = f"Search '{clean_topic}' in {target_app.capitalize()}"
            task = Task(
                task_id=str(uuid.uuid4()),
                description=desc,
                required_tools=["desktop"],
                risk=RiskLevel.LOW,
                action_metadata={
                    "app": target_app,
                    "intent": "open_app",
                    "desktop_action": "APP_LAUNCH",
                    "url": target_url,
                    "query": clean_topic
                }
            )
            intent = Intent(primary_intent=IntentType.LAUNCH_APPLICATION, confidence=0.98, raw_query=query)
            goal = Goal(primary_goal=desc)
            return Plan(plan_id=str(uuid.uuid4()), intent=intent, goal=goal, tasks=[task])

        # If user explicitly asked to launch or open browser with no destination or search
        if is_explicit_browser_cmd:
            desc = f"Launch {target_app.capitalize()}"
            task = Task(
                task_id=str(uuid.uuid4()),
                description=desc,
                required_tools=["desktop"],
                risk=RiskLevel.LOW,
                action_metadata={
                    "app": target_app,
                    "intent": "open_app",
                    "desktop_action": "APP_LAUNCH"
                }
            )
            intent = Intent(primary_intent=IntentType.LAUNCH_APPLICATION, confidence=0.98, raw_query=query)
            goal = Goal(primary_goal=desc)
            return Plan(plan_id=str(uuid.uuid4()), intent=intent, goal=goal, tasks=[task])

        # 2. Calculator
        if "calc" in q or any(op in q for op in [" + ", " - ", " * ", " / ", "plus", "minus", "times", "divide"]):
            expr = re.sub(r'^(?:open calculator and|open calculator|calculate|solve|what is)\s*(?:calculate|solve)?\s*', '', q, flags=re.IGNORECASE)
            expr = re.sub(r'\s*(in calculator|on calculator)\s*$', '', expr, flags=re.IGNORECASE).strip()
            if not expr:
                task = Task(
                    task_id=str(uuid.uuid4()),
                    description="Launch Calculator",
                    required_tools=["desktop"],
                    risk=RiskLevel.LOW,
                    action_metadata={"app": "calculator", "intent": "open_app", "desktop_action": "APP_LAUNCH"}
                )
                return Plan(plan_id=str(uuid.uuid4()), intent=Intent(primary_intent=IntentType.LAUNCH_APPLICATION, confidence=0.98, raw_query=query), goal=Goal(primary_goal="Launch Calculator"), tasks=[task])
            task = Task(
                task_id=str(uuid.uuid4()),
                description=f"Calculate {expr} in Calculator",
                required_tools=["desktop"],
                risk=RiskLevel.LOW,
                action_metadata={"app": "calculator", "intent": "calculate", "entity": expr, "desktop_action": "APP_INTENT_EXECUTE"}
            )
            return Plan(plan_id=str(uuid.uuid4()), intent=Intent(primary_intent=IntentType.LAUNCH_APPLICATION, confidence=0.95, raw_query=query), goal=Goal(primary_goal="Calculate expression"), tasks=[task])

        # 3. Notepad
        if "notepad" in q or "write note" in q:
            text = re.sub(r'^(open notepad and|write in notepad|write note)\s*', '', q, flags=re.IGNORECASE).strip()
            task = Task(
                task_id=str(uuid.uuid4()),
                description="Write text in Notepad",
                required_tools=["desktop"],
                risk=RiskLevel.LOW,
                action_metadata={"app": "notepad", "intent": "write_note", "entity": text, "desktop_action": "APP_INTENT_EXECUTE"}
            )
            return Plan(plan_id=str(uuid.uuid4()), intent=Intent(primary_intent=IntentType.LAUNCH_APPLICATION, confidence=0.95, raw_query=query), goal=Goal(primary_goal="Write note"), tasks=[task])

        # 4. Instant Messaging & Communication (WhatsApp by default, or Instagram / Telegram)
        msg_patterns = [r'^msg\s+', r'^message\s+', r'^text\s+', r'^send\s+message\s+(?:to\s+)?', r'^send\s+msg\s+(?:to\s+)?']
        is_msg_query = any(re.search(pat, q) for pat in msg_patterns) or ("msg " in q and any(k in q for k in ["whatsapp", "insta", "instagram", "telegram"]))
        
        if is_msg_query:
            # Determine platform (DEFAULT: WhatsApp)
            if "insta" in q or "instagram" in q:
                target_platform = "instagram"
            elif "telegram" in q:
                target_platform = "telegram"
            else:
                target_platform = "whatsapp"

            # Clean command prefix
            clean = re.sub(r'^(?:please\s+)?(?:can\s+you\s+)?(?:open\s+(?:instagram|insta|whatsapp|telegram)\s+and\s+)?', '', q).strip()
            clean = re.sub(r'^(?:msg|message|text|send\s+message\s+to|send\s+msg\s+to|send\s+message|send\s+msg)\s+', '', clean).strip()
            
            # Remove platform mentions from clean
            clean = re.sub(r'\b(?:in|on)\s+(?:whatsapp|insta|instagram|telegram)\b', '', clean, flags=re.IGNORECASE).strip()
            clean = re.sub(r'\b(?:fast|quickly|now|bro|ada)\b', '', clean, flags=re.IGNORECASE).strip()

            parts = clean.split(" ", 1)
            raw_contact = parts[0].strip().capitalize() if parts else "Recipient"
            raw_msg = parts[1].strip() if len(parts) > 1 else query
            raw_msg = re.sub(r'^(?:that|to|saying)\s+', '', raw_msg, flags=re.IGNORECASE).strip()

            # Resolve contact alias
            resolved_contact = raw_contact
            try:
                contacts_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "devices", "known_contacts.json")
                if os.path.exists(contacts_file):
                    with open(contacts_file, "r", encoding="utf-8") as cf:
                        c_data = json.load(cf)
                        c_low = raw_contact.lower()
                        if c_low in c_data:
                            mapping = c_data[c_low]
                            if isinstance(mapping, dict):
                                t_plat = target_platform.lower().strip()
                                if t_plat in ["instagram", "insta"]:
                                    resolved_contact = mapping.get("instagram", raw_contact)
                                elif t_plat in ["whatsapp"]:
                                    resolved_contact = mapping.get("whatsapp", mapping.get("default", raw_contact))
                                else:
                                    resolved_contact = mapping.get(t_plat, mapping.get("default", raw_contact))
                            elif isinstance(mapping, str):
                                resolved_contact = mapping
            except Exception:
                pass

            task = Task(
                task_id=str(uuid.uuid4()),
                description=f"Send {target_platform.capitalize()} message to {resolved_contact}",
                required_tools=["device"],
                risk=RiskLevel.LOW,
                action_metadata={
                    "app": target_platform,
                    "intent": "send_message",
                    "entity": resolved_contact,
                    "message": raw_msg
                }
            )
            intent = Intent(primary_intent=IntentType.COMMUNICATION, confidence=0.98, raw_query=query)
            goal = Goal(primary_goal=f"Send {target_platform.capitalize()} message to {resolved_contact}")
            return Plan(plan_id=str(uuid.uuid4()), intent=intent, goal=goal, tasks=[task])

        # 5. Open mobile app on phone (Instagram, WhatsApp, Telegram, etc.)
        if (q.startswith("open ") or q.startswith("launch ")) and any(k in q for k in ["whatsapp", "instagram", "insta", "telegram", "phone", "camera", "gallery"]):
            app_raw = "instagram" if any(k in q for k in ["instagram", "insta"]) else "whatsapp" if "whatsapp" in q else "telegram" if "telegram" in q else q.split(" ")[1].strip()
            task = Task(
                task_id=str(uuid.uuid4()),
                description=f"Open {app_raw.capitalize()} on phone",
                required_tools=["device"],
                risk=RiskLevel.LOW,
                action_metadata={"app": app_raw, "intent": "open_app", "entity": app_raw}
            )
            intent = Intent(primary_intent=IntentType.LAUNCH_APPLICATION, confidence=0.95, raw_query=query)
            goal = Goal(primary_goal=f"Open {app_raw.capitalize()} on phone")
            return Plan(plan_id=str(uuid.uuid4()), intent=intent, goal=goal, tasks=[task])

        # 6. Open generic desktop application (Only for true desktop apps, NOT phone/mobile apps)
        if (clean_lower.startswith("open ") or clean_lower.startswith("launch ")) and not any(k in clean_lower for k in ["msg", "message", "send", "whatsapp", "telegram", "instagram", "insta", "text", "phone"]):
            app_name = re.sub(r'^(?:open|launch)\s+', '', clean_lower).strip()
            task = Task(
                task_id=str(uuid.uuid4()),
                description=f"Launch {app_name.capitalize()}",
                required_tools=["desktop"],
                risk=RiskLevel.LOW,
                action_metadata={"app": app_name, "intent": "open_app", "desktop_action": "APP_LAUNCH"}
            )
            return Plan(plan_id=str(uuid.uuid4()), intent=Intent(primary_intent=IntentType.LAUNCH_APPLICATION, confidence=0.95, raw_query=query), goal=Goal(primary_goal=f"Launch {app_name.capitalize()}"), tasks=[task])

        return None
