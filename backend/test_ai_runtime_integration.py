import asyncio
import pytest
from backend.planner.schema import Intent, IntentType, Goal
from backend.planner.core import PlannerCore
from backend.planner.engines import (
    IntentDetector, GoalExtractor, TaskDecomposer, RiskDetector,
    DependencyResolver, ClarificationEngine, MockLLMProvider
)
from backend.execution.core import ExecutionManager, TaskExecutorInterface
from backend.execution.engines import RetryEngine, TimeoutManager
from backend.execution.schema import ExecutionState

from backend.agents.router.core import AgentRouter
from backend.agents.router.registry import AgentRegistry, DEFAULT_AGENTS
from backend.agents.router.policy import AgentSelectionPolicy
from backend.agents.router.health import AgentHealthMonitor, AgentAvailabilityTracker
from backend.agents.router.schema import AgentDescriptor, AgentHealthStatus, RoutingContext

from backend.capabilities.core import CapabilityResolver
from backend.capabilities.registry import CapabilityRegistry
from backend.capabilities.default_capabilities import DEFAULT_CAPABILITIES
from backend.capabilities.schema import CapabilityContext

from backend.tools.core import ToolRegistryManager
from backend.tools.schema import ToolDescriptor, ToolMetadata, ToolCategory, ToolHealthStatus

class IntegrationMockTaskExecutor(TaskExecutorInterface):
    def __init__(self, agent_router: AgentRouter, capability_resolver: CapabilityResolver, tool_registry_manager: ToolRegistryManager):
        self.agent_router = agent_router
        self.capability_resolver = capability_resolver
        self.tool_registry_manager = tool_registry_manager

    async def execute_task(self, task):
        # 1. Capability Resolution
        cap_context = CapabilityContext(
            task_id=task.task_id,
            task_description=task.description
        )
        resolutions = self.capability_resolver.resolve(cap_context)
        
        req_agents = []
        for r in resolutions:
            if r.preferred_agent:
                req_agents.append(r.preferred_agent)
                
        # 2. Agent Routing
        route_context = RoutingContext(
            task_id=task.task_id,
            task_description=task.description,
            required_agents=req_agents
        )
        route_result = self.agent_router.route_task(route_context)
        
        # 3. Tool Discovery (Mocking Tool Execution for now)
        tools = self.tool_registry_manager.cache.get_by_category(ToolCategory.UTILITY.value)
        
        return f"Executed task {task.task_id} via agent {route_result.agent_name} with {len(tools)} tools available."

@pytest.mark.asyncio
async def test_full_pipeline_integration():
    # Setup Tool Registry
    tool_manager = ToolRegistryManager()
    tool_manager.register_tool(ToolDescriptor(
        tool_id="t1", name="Tool 1", description="desc", category=ToolCategory.UTILITY,
        metadata=ToolMetadata(version="1.0", author="test")
    ))
    
    # Setup Agent Router
    agent_reg = AgentRegistry()
    for name in DEFAULT_AGENTS:
        agent_reg.register(AgentDescriptor(
            agent_id=name.lower(), name=name, description="desc",
            health_status=AgentHealthStatus.HEALTHY, is_available=True
        ))
    router = AgentRouter(agent_reg, AgentSelectionPolicy(agent_reg), AgentHealthMonitor(agent_reg), AgentAvailabilityTracker(agent_reg))
    
    # Setup Capability Resolver
    cap_reg = CapabilityRegistry()
    for cap in DEFAULT_CAPABILITIES:
        cap_reg.register_capability(cap)
    cap_resolver = CapabilityResolver(cap_reg, agent_reg)
    
    # Setup Execution Engine
    executor = IntegrationMockTaskExecutor(router, cap_resolver, tool_manager)
    execution_manager = ExecutionManager(executor, RetryEngine(max_retries=1), TimeoutManager(default_timeout=5.0))
    
    # Setup Planner Engine
    llm = MockLLMProvider()
    planner = PlannerCore(
        llm, IntentDetector(llm), GoalExtractor(llm), TaskDecomposer(llm, RiskDetector()),
        DependencyResolver(), RiskDetector(), ClarificationEngine(llm)
    )
    
    # Run the Pipeline
    plan = planner.generate_plan("Open brave browser")
    report = await execution_manager.execute_plan(plan)
    
    assert report.state == ExecutionState.COMPLETED
    assert len(report.failed_tasks) == 0

if __name__ == "__main__":
    asyncio.run(test_full_pipeline_integration())
    print("ALL INTEGRATION TESTS PASSED")
