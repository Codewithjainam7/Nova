import os
import sys
import asyncio
from dotenv import load_dotenv
from google import genai
import groq

# Load environment
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env.local"), override=True)

def verify_gemini():
    print("=== Gemini Diagnostics ===")
    
    # 1. SDK version
    try:
        import importlib.metadata
        gemini_version = importlib.metadata.version('google-genai')
    except Exception:
        gemini_version = "unknown"
        
    print(f"SDK Version: {gemini_version}")
    
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("Loaded API key length: 0")
        print("Root cause: GEMINI_API_KEY not found in environment.")
        return
        
    print(f"Loaded API key length: {len(api_key)}")
    print(f"Last 6 characters: {api_key[-6:] if len(api_key) >= 6 else api_key}")
    
    model_name = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    print(f"Loaded model: {model_name}")
    
    print("\nRunning request: 'Hello'")
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents="Hello"
        )
        print("Status: SUCCESS")
        print(f"Response body: {response.text}")
    except Exception as e:
        print("Status: FAILED")
        print(f"Full exception: {repr(e)}")
        if hasattr(e, 'status'):
            print(f"HTTP status: {e.status}")
        if hasattr(e, 'message'):
            print(f"Response body: {e.message}")
        print(f"Root cause: {str(e)}")

def verify_groq():
    print("\n=== Groq Diagnostics ===")
    
    try:
        import importlib.metadata
        groq_version = importlib.metadata.version('groq')
    except Exception:
        groq_version = groq.__version__ if hasattr(groq, '__version__') else "unknown"
        
    print(f"SDK Version: {groq_version}")
    
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        print("Loaded API key length: 0")
        print("Root cause: GROQ_API_KEY not found in environment.")
        return
        
    print(f"Loaded API key length: {len(api_key)}")
    print(f"Last 6 characters: {api_key[-6:] if len(api_key) >= 6 else api_key}")
    
    model_name = os.environ.get("GROQ_MODEL", "llama3-8b-8192")
    print(f"Loaded model: {model_name}")
    
    print("\nRunning request: 'Hello'")
    try:
        client = groq.Client(api_key=api_key)
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Hello"}]
        )
        print("Status: SUCCESS")
        print(f"Response body: {response.choices[0].message.content}")
    except Exception as e:
        print("Status: FAILED")
        print(f"Full exception: {repr(e)}")
        if hasattr(e, 'status_code'):
            print(f"HTTP status: {e.status_code}")
        if hasattr(e, 'response'):
            print(f"Response body: {e.response.text if hasattr(e.response, 'text') else e.response}")
        print(f"Root cause: {str(e)}")

if __name__ == "__main__":
    verify_gemini()
    verify_groq()
