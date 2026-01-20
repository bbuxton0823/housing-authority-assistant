"""
Tests for the Housing Authority Assistant API.
"""
import pytest
from fastapi.testclient import TestClient
import os


# Set environment variables before importing the app
os.environ["OPENAI_API_KEY"] = ""  # Empty to test degraded mode


@pytest.fixture
def client():
    """Create a test client for the API."""
    from api import app
    return TestClient(app)


def test_health_endpoint(client):
    """Test that the health endpoint returns 200 with status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_chat_endpoint_returns_valid_response(client):
    """Test that the chat endpoint returns a valid response structure."""
    response = client.post(
        "/chat",
        json={"message": "Hello"}
    )
    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "conversation_id" in data
    assert "current_agent" in data
    assert "messages" in data
    assert "events" in data
    assert "context" in data
    assert "agents" in data
    assert "guardrails" in data

    # Verify messages is a list with at least one item
    assert isinstance(data["messages"], list)
    assert len(data["messages"]) > 0

    # Verify each message has content and agent
    for msg in data["messages"]:
        assert "content" in msg
        assert "agent" in msg


def test_chat_endpoint_graceful_degradation(client):
    """Test that chat endpoint degrades gracefully when OPENAI_API_KEY is not set."""
    # Since we set OPENAI_API_KEY="" in the fixture, this should return degraded mode
    response = client.post(
        "/chat",
        json={"message": "I need to schedule an inspection"}
    )
    assert response.status_code == 200
    data = response.json()

    # Should still have valid structure
    assert "messages" in data
    assert len(data["messages"]) > 0

    # The message should indicate unavailability or provide contact info
    message_content = data["messages"][0]["content"].lower()
    assert (
        "unavailable" in message_content or
        "contact" in message_content or
        "customerservice" in message_content
    )


def test_chat_endpoint_returns_conversation_id(client):
    """Test that conversation_id is returned."""
    response = client.post(
        "/chat",
        json={"message": "Hello"}
    )
    assert response.status_code == 200
    data = response.json()
    conversation_id = data["conversation_id"]
    assert conversation_id is not None
    assert len(conversation_id) > 0


def test_agents_list_populated(client):
    """Test that the agents list contains expected agents."""
    response = client.post(
        "/chat",
        json={"message": "Hello"}
    )
    assert response.status_code == 200
    data = response.json()

    # Should have agents
    assert "agents" in data
    assert isinstance(data["agents"], list)
    assert len(data["agents"]) > 0

    # Each agent should have required fields
    for agent in data["agents"]:
        assert "name" in agent
        assert "description" in agent


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
