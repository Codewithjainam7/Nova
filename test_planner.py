"""
Test the Planner output for failing commands.
This shows what required_tools and description the Planner generates.
"""
import asyncio
import sys
sys.path.insert(0, "F:\\NOVA AI")

from backend.core.di import bootstrap_di

async def main():
    bootstrap_di()
    
    from backend.planner.core import PlannerCore
    from backend.core.di import di_container
    
    planner = di_container.resolve(PlannerCore)
    
    commands = [
        "Open Calculator",
        "Open Google",
        "Search Python on Google",
        "Take a screenshot",
        "Remember my favorite color is blue",
        "What is my favorite color",
        "Read text from my screen",
    ]
    
    for cmd in commands:
        print(f"\n{'='*60}")
        print(f"COMMAND: {cmd}")
        print(f"{'='*60}")
        try:
            plan = await planner.generate_plan(cmd)
            print(f"  Intent: {plan.intent.primary_intent}")
            print(f"  Plan required_tools: {plan.required_tools}")
            for i, task in enumerate(plan.tasks):
                print(f"  Task {i}: desc='{task.description}' tools={task.required_tools}")
        except Exception as e:
            print(f"  ERROR: {e}")

asyncio.run(main())
