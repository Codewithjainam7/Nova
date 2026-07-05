from backend.response.schema import ResponseFormat

class ResponseFormatter:
    """Formats the valid response for the final output."""
    def format(self, content: str, target_format: ResponseFormat) -> str:
        # In a more advanced implementation, this could inject UI specific markdown,
        # or structure JSON for specific frontend consumption.
        return content
