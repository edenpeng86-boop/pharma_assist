"""In-memory conversation history."""

from __future__ import annotations

from collections import defaultdict

from src.core.models import ConversationMessage


class ConversationMemory:
    def __init__(self, max_messages: int = 20) -> None:
        self.max_messages = max_messages
        self.sessions: dict[str, list[ConversationMessage]] = defaultdict(list)

    def add(self, session_id: str, role: str, content: str) -> None:
        self.sessions[session_id].append(ConversationMessage(role=role, content=content))
        self.sessions[session_id] = self.sessions[session_id][-self.max_messages :]

    def get_history(self, session_id: str) -> list[ConversationMessage]:
        return list(self.sessions.get(session_id, []))

    def clear(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)


memory = ConversationMemory()
