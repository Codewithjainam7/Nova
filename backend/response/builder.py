import hashlib
from typing import Dict, Any
from backend.response.schema import ResponseInput, ResponseOutput
from backend.core.logger import app_logger

class ResponseAssembler:
    """Assembles the final validated output object."""
    def assemble(self, formatted_content: str, metadata: Dict[str, Any], request: ResponseInput) -> ResponseOutput:
        
        # Merge input metadata with parser metadata
        combined_metadata = {**request.metadata, **metadata}
        
        # Calculate checksum for caching and integrity
        checksum = hashlib.sha256(formatted_content.encode()).hexdigest()
        
        # Basic confidence calculation (could be more complex based on parsing success, provider scores, etc)
        confidence = 1.0
        if request.target_format.name == "JSON" and "parsed_json" not in combined_metadata:
             confidence = 0.0 # Failed to parse JSON when required

        return ResponseOutput(
            response_type=request.response_type,
            provider=request.provider,
            model=request.model,
            rendered_content=formatted_content,
            metadata=combined_metadata,
            confidence_score=confidence,
            checksum=checksum
        )
