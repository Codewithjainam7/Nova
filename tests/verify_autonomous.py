import asyncio
import os
import sys
from backend.core.environment import load_environment
load_environment()

from backend.core.di import di_container, bootstrap_di
from backend.kernel.core import NovaKernel
from backend.kernel.schema import KernelRequest, KernelState
from backend.core.logger import app_logger

async def run_autonomous_verification():
    print("=== Phase 9: Real End-to-End Autonomous Tests ===\n")
    bootstrap_di()
    
    from backend.providers.core import AIProviderManager
    provider_manager = di_container.resolve(AIProviderManager)
    provider_manager.bootstrap()

    kernel = NovaKernel()
    await kernel.startup()

    workflows = [
        "Open Google, search OpenAI, take a screenshot, extract text, and summarize.",
        "Open Notepad, type 'Hello Jainam', and save the file.",
        "My favourite language is Python.",
        "What is my favourite programming language?"
    ]

    success_count = 0

    for i, intent in enumerate(workflows, 1):
        print(f"\n--- Running Autonomous Workflow {i}: '{intent}' ---")
        req = KernelRequest(user_input=intent)
        
        resp = await kernel.dispatch(req)
        
        if resp.status == KernelState.COMPLETED:
            print(f"[SUCCESS] Workflow {i}")
            print(f"Response: {resp.content}\n")
            success_count += 1
        else:
            print(f"[FAIL] Workflow {i} failed.")
            print(f"Error: {getattr(resp, 'error', 'Unknown')}\n")

    print("=== AUTONOMOUS E2E VERIFICATION COMPLETE ===")
    print(f"Success Rate: {success_count}/{len(workflows)}")
    
    if success_count == len(workflows):
        await kernel.shutdown()
        sys.exit(0)
    else:
        await kernel.shutdown()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_autonomous_verification())
