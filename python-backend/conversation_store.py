from typing import Any, Dict, Optional, Protocol


class ConversationStore(Protocol):
    def get(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        ...

    def save(self, conversation_id: str, state: Dict[str, Any]) -> None:
        ...


class InMemoryConversationStore:
    def __init__(self) -> None:
        self._conversations: Dict[str, Dict[str, Any]] = {}

    def get(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        return self._conversations.get(conversation_id)

    def save(self, conversation_id: str, state: Dict[str, Any]) -> None:
        self._conversations[conversation_id] = state
