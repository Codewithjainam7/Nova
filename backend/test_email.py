import asyncio
import pytest
from backend.email.schema import EmailAction, EmailActionType, EmailPermissionLevel, EmailProviderType
from backend.email.core import EmailAgent

@pytest.mark.asyncio
async def test_email_read_action():
    agent = EmailAgent() # Defaults to READ_ONLY
    
    action = EmailAction(
        action_type=EmailActionType.READ,
        provider=EmailProviderType.GMAIL
    )
    
    results = await agent.perform_action(action)
    assert len(results) == 1
    assert results[0].subject == "Mock Gmail Subject"
    assert agent.metrics.total_actions == 1

@pytest.mark.asyncio
async def test_email_permissions():
    agent = EmailAgent(permission_level=EmailPermissionLevel.READ_ONLY)
    
    action = EmailAction(
        action_type=EmailActionType.SEND,
        provider=EmailProviderType.GMAIL,
        payload={"recipients": ["user@example.com"]}
    )
    
    with pytest.raises(PermissionError):
        await agent.perform_action(action)
        
    assert agent.metrics.failed_actions == 1

@pytest.mark.asyncio
async def test_email_policy_blocked_domain():
    agent = EmailAgent(permission_level=EmailPermissionLevel.COMPOSE)
    
    action = EmailAction(
        action_type=EmailActionType.DRAFT,
        provider=EmailProviderType.GMAIL,
        payload={"recipients": ["hacker@malicious.com"]}
    )
    
    with pytest.raises(PermissionError):
        await agent.perform_action(action)
        
    assert agent.metrics.failed_actions == 1

@pytest.mark.asyncio
async def test_email_workflow_ai():
    agent = EmailAgent(permission_level=EmailPermissionLevel.COMPOSE)
    
    action = EmailAction(
        action_type=EmailActionType.COMPOSE_AI,
    )
    
    result = await agent.perform_action(action)
    assert result["draft_id"] == "draft_123"

if __name__ == "__main__":
    asyncio.run(test_email_read_action())
    asyncio.run(test_email_permissions())
    asyncio.run(test_email_policy_blocked_domain())
    asyncio.run(test_email_workflow_ai())
    print("ALL EMAIL TESTS PASSED")
