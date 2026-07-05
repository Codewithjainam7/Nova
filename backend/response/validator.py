from typing import Dict, Any
from backend.response.schema import ResponseFormat
from backend.core.logger import app_logger

class ResponsePolicy:
    """Configuration and rules for acceptable responses."""
    require_json_success: bool = True

class ResponseValidator:
    """Validates the parsed response against policies."""
    def __init__(self, policy: ResponsePolicy):
        self.policy = policy

    def validate(self, parsed_content: str, metadata: Dict[str, Any], target_format: ResponseFormat) -> bool:
        if target_format == ResponseFormat.JSON:
            if self.policy.require_json_success and "parsed_json" not in metadata:
                app_logger.error("Response validation failed: Expected valid JSON, but parsing failed.")
                return False
                
        if not parsed_content:
            app_logger.error("Response validation failed: Content is empty.")
            return False
            
        return True
