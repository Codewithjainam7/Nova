import os
import sys

# Load environment using centralized loader
from backend.core.environment import load_environment
project_root, env_path, env_local_path = load_environment()

def verify():
    print(f"Project Root: {project_root}")
    print(f".env location: {env_path}")
    print(f".env.local location: {env_local_path}")
    print()
    
    gemini_key = os.environ.get("GEMINI_API_KEY")
    groq_key = os.environ.get("GROQ_API_KEY")
    
    print(f"{'[PASS]' if gemini_key else '[FAIL]'} GEMINI_API_KEY exists")
    print(f"{'[PASS]' if groq_key else '[FAIL]'} GROQ_API_KEY exists")
    print()
    
    print(f"Gemini Key Length: {len(gemini_key) if gemini_key else 0}")
    print(f"Groq Key Length: {len(groq_key) if groq_key else 0}")

if __name__ == "__main__":
    verify()
