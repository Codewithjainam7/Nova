import uuid
from typing import Optional
from backend.planner.schema import Plan, IntentType, RiskLevel
from backend.planner.engines import (
    IntentDetector, GoalExtractor, TaskDecomposer,
    DependencyResolver, RiskDetector, ClarificationEngine,
    LLMProviderInterface
)
from backend.core.logger import app_logger
from backend.core.config import config_manager

class PlannerCore:
    """
    Central orchestration for NOVA's Planner Engine.
    Coordinates intent detection, goal extraction, task decomposition, and risk assessment.
    """
    def __init__(
        self,
        llm: LLMProviderInterface,
        intent_detector: IntentDetector,
        goal_extractor: GoalExtractor,
        task_decomposer: TaskDecomposer,
        dependency_resolver: DependencyResolver,
        risk_detector: RiskDetector,
        clarification_engine: ClarificationEngine
    ):
        self.llm = llm
        self.intent_detector = intent_detector
        self.goal_extractor = goal_extractor
        self.task_decomposer = task_decomposer
        self.dependency_resolver = dependency_resolver
        self.risk_detector = risk_detector
        self.clarification_engine = clarification_engine
        # Conf threshold could be loaded from config
        self.confidence_threshold = 0.6

    def generate_plan(self, query: str) -> Plan:
        app_logger.info(f"Generating plan for query: {query}")
        
        # 1. Intent Detection
        intent = self.intent_detector.detect_intent(query)
        
        # 6. Clarification Engine Check
        clarification_questions = []
        if intent.confidence < self.confidence_threshold:
            clarification_questions = self.clarification_engine.generate_questions(intent)
            # Short-circuit task decomposition if we need clarification
            return Plan(
                plan_id=str(uuid.uuid4()),
                intent=intent,
                goal=self.goal_extractor.extract_goal(intent),
                tasks=[],
                clarification_questions=clarification_questions,
                confirmation_required=True
            )
            
        # 2. Goal Extraction
        goal = self.goal_extractor.extract_goal(intent)
        
        # 3. Task Decomposition & 5. Risk Detection (done within decompose)
        tasks = self.task_decomposer.decompose(query, intent)
        
        # 4. Dependency Resolution
        dependencies = self.dependency_resolver.resolve(tasks)
        
        # Calculate overall risk
        overall_risk = RiskLevel.LOW
        confirmation_required = False
        for t in tasks:
            if t.risk == RiskLevel.CRITICAL:
                overall_risk = RiskLevel.CRITICAL
                confirmation_required = True
                break
            elif t.risk == RiskLevel.HIGH and overall_risk != RiskLevel.CRITICAL:
                overall_risk = RiskLevel.HIGH
                confirmation_required = True
            elif t.risk == RiskLevel.MEDIUM and overall_risk not in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
                overall_risk = RiskLevel.MEDIUM
            
            if "WAIT FOR USER CONFIRMATION" in t.description:
                confirmation_required = True

        plan = Plan(
            plan_id=str(uuid.uuid4()),
            intent=intent,
            goal=goal,
            tasks=tasks,
            dependencies=dependencies,
            overall_risk=overall_risk,
            confirmation_required=confirmation_required,
            clarification_questions=[]
        )
        
        app_logger.info(f"Generated Plan {plan.plan_id} with {len(tasks)} tasks and overall risk {overall_risk.value}")
        return plan
