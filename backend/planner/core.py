import json
import uuid
import re
from typing import Optional
from backend.planner.schema import Plan, Intent, Goal, Task, IntentType, RiskLevel
from backend.providers.core import AIProviderManager
from backend.providers.schema import GenerationRequest, Message, Role, ProviderType
from backend.core.logger import app_logger

class PlannerCore:
    """
    Central orchestration for NOVA's Planner Engine.
    Uses AIProviderManager to generate structured JSON plans.
    """
    def __init__(self, provider_manager: AIProviderManager):
        self.provider_manager = provider_manager

    async def generate_plan(self, query: str, context: str = "") -> Plan:
        app_logger.info(f"Generating real plan for query: {query}")
        
        system_prompt = f"""You are the central Planning Engine for ADA, an elite Jarvis-style autonomous AI Operating System.
Your job is to take a user's natural language request and break it down into a structured JSON execution plan.
You are a backend JSON formatting engine. You are NOT a conversational assistant. 
DO NOT apologize, DO NOT explain, and DO NOT say you cannot perform actions. 
Your ONLY job is to output the JSON plan that routes the user's intent to the correct engine.

The agent has these available tools/subsystems: ["browser", "desktop", "vision", "voice", "memory", "search", "device", "background_search"].

IMPORTANT RULES:
1. If the user asks to perform an action in a LOCAL desktop application (e.g. Settings, Calculator, Notepad, Spotify, VS Code, File Explorer), use "desktop" in required_tools with desktop_action "APP_INTENT_EXECUTE". Provide "app", "intent", and "entity".
2. MUSIC & SPOTIFY ON PC: If the user asks to play a song/artist/playlist on Spotify on their computer (e.g. 'play sunflower on spotify'), use "desktop" in required_tools with desktop_action "APP_INTENT_EXECUTE", app "spotify", intent "play_media", and provide the song/artist query in "entity".
3. If the user asks to do something on a WEBSITE or open web services (e.g. Gmail, YouTube, Google), use "browser" in required_tools with browser_action "NAVIGATE" and provide the url in action_metadata.
4. CRITICAL: If the user is just saying hello, asking a general question, or chatting conversationally, DO NOT OUTPUT ANY DESKTOP OR BROWSER TASKS. Set tasks to an empty array [].
5. If the user asks to search for news, maps, or background information to be displayed on screen, use "background_search" in required_tools and provide "query" in action_metadata. Do NOT use "browser" for this.
6. If the user asks to interact with their phone (e.g., check battery, connect phone, pair phone, open app on phone, play a song or video on phone, send a message, transfer a file, or open/view a file/image on the phone), use "device" in required_tools. For pairing, set intent to "pair". For connecting, set intent to "connect". For battery, set intent to "get_battery". For opening an app, set intent to "open_app". For playing a song/video/media on the phone, MUST set intent to "play_media", provide the media name in "entity", and provide the target app (e.g. "youtube", "spotify") in "app" within action_metadata. For sending a message (e.g. WhatsApp, Telegram), set intent to "send_message", provide the contact name in "entity", the message body in "message", and the target app (e.g. "whatsapp", "telegram") in "app" within action_metadata. For sending/transferring a file to the phone, set intent to "transfer_file" and provide the filename in "entity" within action_metadata. For opening/viewing a file or image on the phone (like viewing a transferred file), set intent to "open_app" and provide the filename (e.g. "sign2.png") in "entity" within action_metadata. Do NOT generate browser or desktop tasks for opening files on the phone.

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
                    messages=[Message(role=Role.USER, content=system_prompt)],
                    provider_type=ProviderType.GEMINI,
                    model="",
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
        
        app_logger.error(f"Failed to generate real plan after 3 attempts: {str(last_error)}")
        # Fallback mock plan
        intent = Intent(primary_intent=IntentType.UNKNOWN, confidence=0.0, raw_query=query)
        goal = Goal(primary_goal="Fallback execution")
        return Plan(plan_id=str(uuid.uuid4()), intent=intent, goal=goal, tasks=[])
