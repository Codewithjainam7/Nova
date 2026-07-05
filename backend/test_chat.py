import asyncio
import pytest
from backend.chat.schema import ChatMessage, ChatMessageType
from backend.chat.core import ChatSystem

@pytest.mark.asyncio
async def test_chat_message_add_and_search():
    chat = ChatSystem()
    conv_id = "conv-1"
    
    msg1 = ChatMessage(type=ChatMessageType.USER, content="How do I write a Python script?")
    msg2 = ChatMessage(type=ChatMessageType.ASSISTANT, content="Here is a Python script example.")
    
    await chat.add_message(conv_id, msg1)
    await chat.add_message(conv_id, msg2)
    
    assert chat.metrics.total_messages == 2
    
    results = chat.manager.search.search("Python script example")
    assert len(results) == 1
    assert results[0].type == ChatMessageType.ASSISTANT

@pytest.mark.asyncio
async def test_chat_streaming():
    chat = ChatSystem()
    conv_id = "conv-2"
    
    async def mock_generator():
        yield "Hello, "
        yield "world!"
        
    final_msg = await chat.stream_response(conv_id, mock_generator())
    
    assert final_msg.content == "Hello, world!"
    assert final_msg.type == ChatMessageType.ASSISTANT
    assert chat.metrics.total_messages == 1

@pytest.mark.asyncio
async def test_chat_export():
    chat = ChatSystem()
    conv_id = "conv-3"
    
    msg = ChatMessage(type=ChatMessageType.USER, content="Hello")
    await chat.add_message(conv_id, msg)
    
    conv = chat.manager.store.get_conversation(conv_id)
    md_export = chat.manager.exports.export_to_markdown(conv)
    
    assert "Hello" in md_export
    assert "USER" in md_export

if __name__ == "__main__":
    asyncio.run(test_chat_message_add_and_search())
    asyncio.run(test_chat_streaming())
    asyncio.run(test_chat_export())
    print("ALL CHAT TESTS PASSED")
