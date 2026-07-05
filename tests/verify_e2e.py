import asyncio
import os
import sys
from backend.core.environment import load_environment
load_environment()

from backend.core.di import di_container, bootstrap_di
from backend.kernel.core import NovaKernel
from backend.kernel.schema import KernelRequest, KernelState

if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GROQ_API_KEY"):
    print("FATAL: Real AI provider API keys (GEMINI_API_KEY or GROQ_API_KEY) are unavailable.")
    print("Please set them in .env.local")
    sys.exit(1)

async def verify_e2e():
    print("=== STARTING FULL END-TO-END VERIFICATION ===")
    print("Bootstrapping DI Container...")
    bootstrap_di()
    
    from backend.providers.core import AIProviderManager
    provider_manager = di_container.resolve(AIProviderManager)
    provider_manager.bootstrap()

    kernel = NovaKernel()
    await kernel.startup()

    workflows = [
        {
            "name": "1. Voice Workflow (Speak: 'Open Google')",
            "request": KernelRequest(user_input="", metadata={"is_voice": True, "audio_bytes": b'\x00' * 32000}), 
            "simulate_intent": "Open Google."
        },
        {
            "name": "2. Vision Workflow (Type: 'Take a screenshot and tell me what is on my screen.')",
            "request": KernelRequest(user_input="Take a screenshot and tell me what is on my screen.")
        },
        {
            "name": "3. Desktop Workflow (Type: 'Open Notepad and write Hello NOVA.')",
            "request": KernelRequest(user_input="Open Notepad and write Hello NOVA.")
        },
        {
            "name": "4. Browser & Search Workflow (Type: 'Search Python async tutorial.')",
            "request": KernelRequest(user_input="Search Python async tutorial.")
        },
        {
            "name": "5. Memory Store (Ask: 'My favourite language is Python.')",
            "request": KernelRequest(user_input="My favourite language is Python.")
        },
        {
            "name": "6. Memory Retrieve (Ask: 'What is my favourite language?')",
            "request": KernelRequest(user_input="What is my favourite language?")
        }
    ]

    success_count = 0

    for wf in workflows:
        print(f"\n--- Running: {wf['name']} ---")
        req = wf["request"]
        
        # Inject voice intent if it's the voice test to avoid needing real mic input to match plan
        if "simulate_intent" in wf:
            # We bypass the actual STT block since it's dummy bytes, just set intent manually
            req.user_input = wf["simulate_intent"]
            
        try:
            response = await kernel.dispatch(req)
            if response.status == KernelState.COMPLETED:
                print(f"[SUCCESS] {wf['name']}")
                print(f"Response: {response.content}")
                success_count += 1
            else:
                print(f"[FAILED] {wf['name']}")
                print(f"Error: {response.error}")
        except Exception as e:
            print(f"[FATAL] Exception in workflow: {str(e)}")
            
    print("\n=== E2E VERIFICATION COMPLETE ===")
    print(f"Success Rate: {success_count}/{len(workflows)}")
    
    await kernel.shutdown()

if __name__ == "__main__":
    asyncio.run(verify_e2e())
