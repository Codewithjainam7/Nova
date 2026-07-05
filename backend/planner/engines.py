from typing import List, Dict, Any, Tuple
from backend.planner.schema import Intent, IntentType, Goal, RiskLevel, Task
from backend.core.logger import app_logger

class LLMProviderInterface:
    """Interface for dependency injection of an LLM provider."""
    def query(self, prompt: str) -> str:
        raise NotImplementedError

class MockLLMProvider(LLMProviderInterface):
    """Mock provider for testing."""
    def query(self, prompt: str) -> str:
        return "mock_response"

class IntentDetector:
    def __init__(self, llm: LLMProviderInterface):
        self.llm = llm

    def detect_intent(self, query: str) -> Intent:
        # A real implementation would parse the LLM output
        app_logger.debug(f"Detecting intent for query: {query}")
        
        # Simple heuristic for testing
        query_lower = query.lower()
        if "open" in query_lower or "launch" in query_lower:
            return Intent(primary_intent=IntentType.LAUNCH_APPLICATION, confidence=0.9, raw_query=query)
        elif "search" in query_lower:
            return Intent(primary_intent=IntentType.INTERNET_SEARCH, confidence=0.85, raw_query=query)
        elif "email" in query_lower:
            return Intent(primary_intent=IntentType.COMMUNICATION, confidence=0.95, raw_query=query)
        elif "summarize" in query_lower:
            return Intent(primary_intent=IntentType.DOCUMENT_ANALYSIS, confidence=0.9, raw_query=query)
        else:
            return Intent(primary_intent=IntentType.UNKNOWN, confidence=0.4, raw_query=query)

class GoalExtractor:
    def __init__(self, llm: LLMProviderInterface):
        self.llm = llm

    def extract_goal(self, intent: Intent) -> Goal:
        app_logger.debug(f"Extracting goal for intent: {intent.primary_intent}")
        return Goal(
            primary_goal=f"Execute {intent.primary_intent.value}",
            secondary_goals=["Ensure safe execution"],
            constraints=[],
            priority=1,
            risk_level=RiskLevel.LOW
        )

class RiskDetector:
    def assign_risk(self, description: str) -> RiskLevel:
        desc_lower = description.lower()
        if "delete" in desc_lower or "format" in desc_lower or "shutdown" in desc_lower:
            return RiskLevel.CRITICAL
        elif "email" in desc_lower or "send" in desc_lower:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

class TaskDecomposer:
    def __init__(self, llm: LLMProviderInterface, risk_detector: RiskDetector):
        self.llm = llm
        self.risk_detector = risk_detector

    def decompose(self, query: str, intent: Intent) -> List[Task]:
        app_logger.debug(f"Decomposing task for query: {query}")
        # In a real system, LLM returns JSON of tasks. We simulate it here.
        tasks = []
        if "open brave" in query.lower() and "email" in query.lower():
            tasks = [
                Task(task_id="t1", description="Launch Browser", risk=self.risk_detector.assign_risk("Launch Browser")),
                Task(task_id="t2", description="Navigate Search", risk=self.risk_detector.assign_risk("Navigate Search")),
                Task(task_id="t3", description="Collect Articles", risk=self.risk_detector.assign_risk("Collect Articles")),
                Task(task_id="t4", description="Summarize", risk=self.risk_detector.assign_risk("Summarize")),
                Task(task_id="t5", description="Draft Email", risk=self.risk_detector.assign_risk("Draft Email")),
                Task(task_id="t6", description="WAIT FOR USER CONFIRMATION", risk=self.risk_detector.assign_risk("WAIT FOR USER CONFIRMATION")),
                Task(task_id="t7", description="Send Email", risk=self.risk_detector.assign_risk("Send Email"))
            ]
        elif intent.primary_intent == IntentType.LAUNCH_APPLICATION:
            tasks.append(Task(task_id="t1", description="Launch Application", risk=self.risk_detector.assign_risk("Launch Application")))
        else:
            tasks.append(Task(task_id="t1", description="General Task Execution", risk=self.risk_detector.assign_risk("General Task Execution")))
        return tasks

class DependencyResolver:
    def resolve(self, tasks: List[Task]) -> Dict[str, List[str]]:
        # A real system uses LLM to map dependency graphs. Here we assume sequential.
        dependencies = {}
        for i, task in enumerate(tasks):
            if i > 0:
                task.dependencies = [tasks[i-1].task_id]
            dependencies[task.task_id] = task.dependencies
        return dependencies

class ClarificationEngine:
    def __init__(self, llm: LLMProviderInterface):
        self.llm = llm

    def generate_questions(self, intent: Intent) -> List[str]:
        app_logger.debug("Generating clarification questions due to low confidence")
        if intent.confidence < 0.5:
            return ["Can you please clarify what you want me to do?"]
        return []
