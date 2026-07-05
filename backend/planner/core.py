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
        
        system_prompt = f"""You are the Planner Engine for the NOVA autonomous agent.
Analyze the user request and generate a structured Execution Plan in JSON format.
The agent has these available tools/subsystems: ["browser", "desktop", "vision", "voice", "memory", "search"].

User Request: {query}
Context: {context}

Return exactly ONE JSON object matching this schema. Do not output markdown, just the JSON string.
{{
  "intent": {{"primary_intent": "Launch Application|Internet Search|Communication|Document Analysis|System Management|Unknown", "confidence": 0.9, "raw_query": "..."}},
  "goal": {{"primary_goal": "...", "secondary_goals": [], "constraints": [], "priority": 1, "dependencies": [], "risk_level": "LOW|MEDIUM|HIGH|CRITICAL"}},
  "tasks": [
    {{
      "task_id": "1",
      "description": "...",
      "dependencies": [],
      "is_parallel": false,
      "required_resources": [],
      "required_agents": [],
      "required_tools": ["browser"], 
      "risk": "LOW|MEDIUM|HIGH|CRITICAL"
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
        try:
            req = GenerationRequest(
                messages=[Message(role=Role.USER, content=system_prompt)],
                provider_type=ProviderType.GEMINI,
                model="",
                stream=False
            )
            resp = await self.provider_manager.generate(req)
            content = resp.content
            
            # Clean markdown formatting if present
            content = re.sub(r'```json\n?', '', content)
            content = re.sub(r'```\n?', '', content)
            
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
                    risk=t_risk
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
            app_logger.error(f"Failed to generate real plan: {str(e)}")
            # Fallback mock plan
            intent = Intent(primary_intent=IntentType.UNKNOWN, confidence=0.0, raw_query=query)
            goal = Goal(primary_goal="Fallback execution")
            t = Task(task_id="t1", description="General fallback execution", required_tools=[])
            return Plan(plan_id=str(uuid.uuid4()), intent=intent, goal=goal, tasks=[t])
