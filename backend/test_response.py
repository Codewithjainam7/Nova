import asyncio
import pytest
from backend.response.schema import ResponseInput, ResponseType, ResponseFormat
from backend.response.core import ResponseGenerator

@pytest.mark.asyncio
async def test_response_markdown_parsing():
    generator = ResponseGenerator()
    
    # Simulate an LLM returning markdown json block
    raw = "Here is the result:\n```json\n{\"status\": \"ok\", \"value\": 10}\n```"
    request = ResponseInput(
        raw_content=raw,
        provider="gemini",
        model="gemini-1.5-pro",
        response_type=ResponseType.PLANNING,
        target_format=ResponseFormat.JSON
    )
    
    output = await generator.generate(request)
    
    assert output.confidence_score == 1.0
    assert "parsed_json" in output.metadata
    assert output.metadata["parsed_json"]["value"] == 10

@pytest.mark.asyncio
async def test_response_validation_failure():
    generator = ResponseGenerator()
    
    # Simulate an LLM returning broken json when JSON is required
    raw = "Here is the result: { broken json"
    request = ResponseInput(
        raw_content=raw,
        provider="gemini",
        model="gemini-1.5-pro",
        response_type=ResponseType.PLANNING,
        target_format=ResponseFormat.JSON
    )
    
    output = await generator.generate(request)
    
    assert output.confidence_score == 0.0 # Confidence drops on validation failure
    assert output.metadata.get("validation_failed") is True

@pytest.mark.asyncio
async def test_response_streaming():
    generator = ResponseGenerator()
    
    async def mock_stream():
        yield "Chunk 1 "
        yield "Chunk 2 "
        yield "Chunk 3"
        
    request = ResponseInput(
        raw_content="", # Will be filled by streamer
        provider="gemini",
        model="gemini-1.5-pro",
        response_type=ResponseType.CONVERSATION,
        target_format=ResponseFormat.PLAIN_TEXT
    )
    
    output = await generator.generate_from_stream(mock_stream(), request)
    
    assert output.rendered_content == "Chunk 1 Chunk 2 Chunk 3"

if __name__ == "__main__":
    asyncio.run(test_response_markdown_parsing())
    asyncio.run(test_response_validation_failure())
    asyncio.run(test_response_streaming())
    print("ALL RESPONSE TESTS PASSED")
