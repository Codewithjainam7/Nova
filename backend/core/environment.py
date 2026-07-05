import os
from pathlib import Path
from dotenv import load_dotenv

def load_environment():
    """
    Resolves the project root and loads .env first, then .env.local with override=True.
    Ensures that paths are resolved absolutely regardless of the CWD.
    """
    # Resolve the project root (assume backend/core/environment.py -> root is 3 levels up)
    # File is at: NOVA AI / backend / core / environment.py
    # Parents: [0] core, [1] backend, [2] root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    
    env_path = project_root / ".env"
    env_local_path = project_root / ".env.local"
    
    # Load .env first
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        
    # Load .env.local and override existing variables
    if env_local_path.exists():
        load_dotenv(dotenv_path=env_local_path, override=True)
        
    return project_root, env_path, env_local_path
