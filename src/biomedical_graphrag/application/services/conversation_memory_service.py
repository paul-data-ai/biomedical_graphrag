"""Conversation memory management service using LangChain."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_core.messages import AIMessage, HumanMessage
from loguru import logger


class ConversationMemoryService:
    """
    Manages conversation memory for multiple chat sessions using LangChain.

    Uses in-memory storage with ConversationBufferWindowMemory to keep
    the last N conversation exchanges per session. This provides context
    for follow-up questions without requiring external storage.

    Attributes:
        sessions: Dict mapping session_id to memory objects
        max_messages: Maximum number of message pairs to keep per session
    """

    def __init__(self, max_messages: int = 10) -> None:
        """
        Initialize the conversation memory service.

        Args:
            max_messages: Maximum number of conversation exchanges to remember (default: 10)
        """
        self.sessions: dict[str, ConversationBufferWindowMemory] = {}
        self.max_messages = max_messages
        self.session_metadata: dict[str, dict[str, Any]] = {}
        logger.info(f"Initialized ConversationMemoryService with max_messages={max_messages}")

    def create_session(self, session_id: str | None = None) -> str:
        """
        Create a new conversation session.

        Args:
            session_id: Optional session ID. If not provided, generates a new UUID.

        Returns:
            Session ID
        """
        if session_id is None:
            session_id = str(uuid4())

        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationBufferWindowMemory(
                k=self.max_messages,  # Keep last N exchanges
                return_messages=True,
                memory_key="chat_history",
            )
            self.session_metadata[session_id] = {
                "created_at": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "message_count": 0,
            }
            logger.info(f"Created new session: {session_id}")

        return session_id

    def add_message(self, session_id: str, human_message: str, ai_message: str) -> None:
        """
        Add a conversation exchange to the session memory.

        Args:
            session_id: Session identifier
            human_message: User's message/question
            ai_message: AI's response/answer
        """
        # Ensure session exists
        if session_id not in self.sessions:
            self.create_session(session_id)

        # Add messages to memory
        memory = self.sessions[session_id]
        memory.chat_memory.add_user_message(human_message)
        memory.chat_memory.add_ai_message(ai_message)

        # Update metadata
        self.session_metadata[session_id]["last_accessed"] = datetime.now().isoformat()
        self.session_metadata[session_id]["message_count"] += 1

        logger.debug(f"Added message to session {session_id}")

    def get_conversation_context(self, session_id: str) -> str:
        """
        Get formatted conversation history for LLM context.

        Args:
            session_id: Session identifier

        Returns:
            Formatted conversation history as a string
        """
        if session_id not in self.sessions:
            return ""

        memory = self.sessions[session_id]
        messages = memory.chat_memory.messages

        if not messages:
            return ""

        # Format messages into readable context
        context_parts = ["Previous conversation:"]
        for msg in messages:
            if isinstance(msg, HumanMessage):
                context_parts.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                context_parts.append(f"Assistant: {msg.content}")

        return "\n".join(context_parts)

    def get_messages(self, session_id: str) -> list[dict[str, str]]:
        """
        Get all messages in a session as a list of dicts.

        Args:
            session_id: Session identifier

        Returns:
            List of message dicts with 'role' and 'content' keys
        """
        if session_id not in self.sessions:
            return []

        memory = self.sessions[session_id]
        messages = memory.chat_memory.messages

        result = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                result.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                result.append({"role": "assistant", "content": msg.content})

        return result

    def clear_session(self, session_id: str) -> bool:
        """
        Clear all messages from a session.

        Args:
            session_id: Session identifier

        Returns:
            True if session was cleared, False if session didn't exist
        """
        if session_id not in self.sessions:
            return False

        self.sessions[session_id].clear()
        self.session_metadata[session_id]["message_count"] = 0
        self.session_metadata[session_id]["last_accessed"] = datetime.now().isoformat()
        logger.info(f"Cleared session: {session_id}")
        return True

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session completely.

        Args:
            session_id: Session identifier

        Returns:
            True if session was deleted, False if session didn't exist
        """
        if session_id not in self.sessions:
            return False

        del self.sessions[session_id]
        del self.session_metadata[session_id]
        logger.info(f"Deleted session: {session_id}")
        return True

    def list_sessions(self) -> list[dict[str, Any]]:
        """
        List all active sessions with metadata.

        Returns:
            List of session info dicts
        """
        sessions_info = []
        for session_id, metadata in self.session_metadata.items():
            # Get first and last messages for preview
            messages = self.get_messages(session_id)
            first_message = messages[0]["content"] if messages else ""
            last_message = messages[-1]["content"] if messages else ""

            sessions_info.append(
                {
                    "session_id": session_id,
                    "created_at": metadata["created_at"],
                    "last_accessed": metadata["last_accessed"],
                    "message_count": metadata["message_count"],
                    "first_message": first_message[:100],  # First 100 chars
                    "last_message": last_message[:100],  # First 100 chars
                }
            )

        return sessions_info

    def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists.

        Args:
            session_id: Session identifier

        Returns:
            True if session exists, False otherwise
        """
        return session_id in self.sessions
