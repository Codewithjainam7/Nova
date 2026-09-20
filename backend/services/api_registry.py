from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

class AuthMethod(str, Enum):
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    NONE = "none"

class ExecutionEngine(str, Enum):
    API = "api"
    NATIVE = "native"
    BROWSER = "browser"
    DESKTOP = "desktop"

class IntegrationMetadata(BaseModel):
    service_name: str
    auth_method: AuthMethod
    docs_link: str
    oauth_requirements: Optional[List[str]] = None
    api_key_requirements: Optional[List[str]] = None
    free_tier_info: str = "Unknown"
    has_sdk: bool = False
    background_capable: bool = True
    preferred_engine: ExecutionEngine = ExecutionEngine.API
    fallback_engine: ExecutionEngine = ExecutionEngine.DESKTOP
    verification_method: str

# Static Registry of Supported Services
API_REGISTRY: Dict[str, IntegrationMetadata] = {
    "spotify": IntegrationMetadata(
        service_name="Spotify",
        auth_method=AuthMethod.NONE,
        docs_link="https://spotify.com",
        free_tier_info="Free local desktop app control.",
        has_sdk=False,
        background_capable=True,
        preferred_engine=ExecutionEngine.DESKTOP,
        fallback_engine=ExecutionEngine.DESKTOP,
        verification_method="desktop process check"
    ),
    "gmail": IntegrationMetadata(
        service_name="Gmail",
        auth_method=AuthMethod.NONE,
        docs_link="https://mail.google.com",
        free_tier_info="Standard web browser access.",
        has_sdk=False,
        background_capable=True,
        preferred_engine=ExecutionEngine.BROWSER,
        fallback_engine=ExecutionEngine.BROWSER,
        verification_method="browser navigation verify"
    ),
    "windows": IntegrationMetadata(
        service_name="Windows OS",
        auth_method=AuthMethod.NONE,
        docs_link="https://learn.microsoft.com/en-us/windows/win32/api/",
        free_tier_info="N/A",
        has_sdk=True,
        background_capable=True,
        preferred_engine=ExecutionEngine.NATIVE,
        fallback_engine=ExecutionEngine.DESKTOP,
        verification_method="process running / WMI query"
    )
    # Add others here as we build them out
}

def get_integration(service_name: str) -> Optional[IntegrationMetadata]:
    """Retrieve integration metadata from the registry by service name."""
    return API_REGISTRY.get(service_name.lower())
