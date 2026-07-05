import pytest
from backend.planner.schema import IntentType, RiskLevel
from backend.planner.engines import (
    MockLLMProvider, IntentDetector, GoalExtractor,
    RiskDetector, TaskDecomposer, DependencyResolver,
    ClarificationEngine
)
from backend.planner.core import PlannerCore

def test_intent_detection():
    llm = MockLLMProvider()
    detector = IntentDetector(llm)
    intent = detector.detect_intent("Open Brave browser")
    assert intent.primary_intent == IntentType.LAUNCH_APPLICATION
    assert intent.confidence >= 0.5

def test_goal_extraction():
    llm = MockLLMProvider()
    extractor = GoalExtractor(llm)
    detector = IntentDetector(llm)
    intent = detector.detect_intent("Open Brave browser")
    goal = extractor.extract_goal(intent)
    assert goal.priority == 1
    assert "Launch Application" in goal.primary_goal

def test_risk_detection():
    detector = RiskDetector()
    assert detector.assign_risk("delete c:\\") == RiskLevel.CRITICAL
    assert detector.assign_risk("send an email") == RiskLevel.MEDIUM
    assert detector.assign_risk("open brave") == RiskLevel.LOW

def test_planner_core_orchestration():
    llm = MockLLMProvider()
    risk_detector = RiskDetector()
    planner = PlannerCore(
        llm=llm,
        intent_detector=IntentDetector(llm),
        goal_extractor=GoalExtractor(llm),
        task_decomposer=TaskDecomposer(llm, risk_detector),
        dependency_resolver=DependencyResolver(),
        risk_detector=risk_detector,
        clarification_engine=ClarificationEngine(llm)
    )

    plan = planner.generate_plan("Open Brave, search AI news, summarize it and email me.")
    assert plan.intent.primary_intent in [IntentType.LAUNCH_APPLICATION, IntentType.INTERNET_SEARCH, IntentType.COMMUNICATION]
    assert len(plan.tasks) == 7
    assert plan.overall_risk == RiskLevel.MEDIUM
    assert plan.confirmation_required is True

def test_clarification_engine():
    llm = MockLLMProvider()
    risk_detector = RiskDetector()
    planner = PlannerCore(
        llm=llm,
        intent_detector=IntentDetector(llm),
        goal_extractor=GoalExtractor(llm),
        task_decomposer=TaskDecomposer(llm, risk_detector),
        dependency_resolver=DependencyResolver(),
        risk_detector=risk_detector,
        clarification_engine=ClarificationEngine(llm)
    )

    plan = planner.generate_plan("Do something ambiguous")
    # Confidence is 0.4 based on our mock heuristic for unknown queries
    assert len(plan.clarification_questions) > 0
    assert plan.confirmation_required is True
    assert len(plan.tasks) == 0

if __name__ == "__main__":
    test_intent_detection()
    test_goal_extraction()
    test_risk_detection()
    test_planner_core_orchestration()
    test_clarification_engine()
    print("ALL PLANNER TESTS PASSED")
