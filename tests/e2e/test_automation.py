import asyncio
import sys
from backend.desktop.core import DesktopManager, DesktopExecutor
from backend.desktop.schema import DesktopAction, DesktopActionType, DesktopPermissionLevel, DesktopMetrics
from backend.kernel.action_sequencer import StatefulActionSequencer

async def run_e2e_tests():
    manager = DesktopManager(DesktopPermissionLevel.AUTOMATION)
    metrics = DesktopMetrics()
    executor = DesktopExecutor(manager, metrics)
    
    print("=== Running End-to-End Automation Tests ===")
    
    intents = [
        ("notepad", "write", "Hello this is a test from the new pipeline!"),
        ("spotify", "play_media", "safar"),
        ("chrome", "search", "https://github.com")
    ]
    
    for app, intent, entity in intents:
        print(f"\n--- Testing {intent} on {app} ---")
        sequence = StatefulActionSequencer.decompose_intent(app, intent, entity)
        
        for step in sequence:
            try:
                action = DesktopAction(
                    action_type=DesktopActionType(step.action_type),
                    payload=step.payload
                )
                await executor.execute(action)
            except Exception as e:
                print(f"Failed at step {step.action_type}: {e}")
                break
                
    print("\n=== E2E Tests Completed ===")

if __name__ == "__main__":
    asyncio.run(run_e2e_tests())
