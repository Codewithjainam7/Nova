import asyncio
import pytest
from backend.prompt.schema import PromptRequest, PromptType
from backend.context.schema import ContextPackage, ContextItem, ContextType
from backend.prompt.core import PromptEngine

@pytest.mark.asyncio
async def test_prompt_generation():
    engine = PromptEngine()
    
    # Create mock context
    ctx = ContextPackage()
    ctx.conversation_context.append(ContextItem(type=ContextType.CONVERSATION, content="User said hi"))
    
    request = PromptRequest(
        prompt_type=PromptType.PLANNING,
        context_package=ctx,
        user_input="Make a plan",
        variables={"extra": "data"}
    )
    
    output = await engine.build_prompt(request)
    
    assert output.prompt_type == PromptType.PLANNING
    assert "Make a plan" in output.rendered_prompt
    assert "User said hi" in output.rendered_prompt
    assert output.estimated_tokens > 0

@pytest.mark.asyncio
async def test_prompt_caching():
    engine = PromptEngine()
    
    ctx = ContextPackage()
    request = PromptRequest(
        prompt_type=PromptType.PLANNING,
        context_package=ctx,
        user_input="Same input"
    )
    
    out1 = await engine.build_prompt(request)
    out2 = await engine.build_prompt(request)
    
    # Checksum should be identical
    assert out1.checksum == out2.checksum
    # Ideally tracking cache hits, but let's just assert they match
    assert out1.rendered_prompt == out2.rendered_prompt

@pytest.mark.asyncio
async def test_prompt_compression():
    engine = PromptEngine()
    
    # Using compression internally
    ctx = ContextPackage()
    # Adding bad whitespace
    request = PromptRequest(
        prompt_type=PromptType.PLANNING,
        context_package=ctx,
        user_input="Test   spacing\n\n\nNew"
    )
    
    output = await engine.build_prompt(request)
    assert "   " not in output.rendered_prompt
    assert "\n\n\n" not in output.rendered_prompt

if __name__ == "__main__":
    asyncio.run(test_prompt_generation())
    asyncio.run(test_prompt_caching())
    asyncio.run(test_prompt_compression())
    print("ALL PROMPT TESTS PASSED")
