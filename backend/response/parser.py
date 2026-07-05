import json
from typing import Dict, Any, Tuple
from backend.response.schema import ResponseFormat
from backend.core.logger import app_logger

class ResponseParser:
    """Parses raw text into structured data if applicable."""
    def parse(self, raw_content: str, target_format: ResponseFormat) -> Tuple[str, Dict[str, Any]]:
        metadata = {}
        parsed_content = raw_content

        if target_format == ResponseFormat.JSON:
            try:
                # Naive JSON extraction (handles markdown json blocks)
                content_to_parse = raw_content
                if "```json" in raw_content:
                    start = raw_content.find("```json") + 7
                    end = raw_content.rfind("```")
                    content_to_parse = raw_content[start:end].strip()
                
                parsed_json = json.loads(content_to_parse)
                metadata["parsed_json"] = parsed_json
                
                # We could serialize it back out cleanly
                parsed_content = json.dumps(parsed_json, indent=2)
            except json.JSONDecodeError as e:
                app_logger.warning(f"Failed to parse JSON response: {str(e)}")
                # If we fail, we keep raw_content and rely on validation to catch it
                pass

        return parsed_content, metadata
