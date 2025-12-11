"""Session management routes for conversation memory."""

from fastapi import APIRouter, HTTPException, status
from loguru import logger

from biomedical_graphrag.api.models import (
    SessionListResponse,
    SessionDetailResponse,
    SessionActionResponse,
    SessionInfo,
    ChatMessage,
)
from biomedical_graphrag.application.services.conversation_memory_service import ConversationMemoryService

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

# Global memory service instance (shared with query routes)
_memory_service: ConversationMemoryService | None = None


def get_memory_service() -> ConversationMemoryService:
    """Get or create the conversation memory service instance."""
    global _memory_service
    if _memory_service is None:
        _memory_service = ConversationMemoryService(max_messages=10)
    return _memory_service


@router.get("/", response_model=SessionListResponse)
async def list_sessions() -> SessionListResponse:
    """
    List all active conversation sessions.

    Returns:
        SessionListResponse with list of sessions and metadata
    """
    try:
        memory_service = get_memory_service()
        sessions_data = memory_service.list_sessions()

        sessions = [
            SessionInfo(
                session_id=session["session_id"],
                created_at=session["created_at"],
                last_accessed=session["last_accessed"],
                message_count=session["message_count"],
                first_message=session["first_message"],
                last_message=session["last_message"],
            )
            for session in sessions_data
        ]

        return SessionListResponse(sessions=sessions, total_count=len(sessions))

    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(e)}",
        ) from e


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: str) -> SessionDetailResponse:
    """
    Get details of a specific session including all messages.

    Args:
        session_id: Session identifier

    Returns:
        SessionDetailResponse with messages and metadata
    """
    try:
        memory_service = get_memory_service()

        if not memory_service.session_exists(session_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found"
            )

        messages_data = memory_service.get_messages(session_id)
        messages = [ChatMessage(role=msg["role"], content=msg["content"]) for msg in messages_data]

        metadata = memory_service.session_metadata.get(session_id, {})

        return SessionDetailResponse(session_id=session_id, messages=messages, metadata=metadata)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session: {str(e)}",
        ) from e


@router.post("/create", response_model=SessionActionResponse)
async def create_session() -> SessionActionResponse:
    """
    Create a new conversation session.

    Returns:
        SessionActionResponse with new session ID
    """
    try:
        memory_service = get_memory_service()
        session_id = memory_service.create_session()

        return SessionActionResponse(
            success=True, message="Session created successfully", session_id=session_id
        )

    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}",
        ) from e


@router.post("/{session_id}/clear", response_model=SessionActionResponse)
async def clear_session(session_id: str) -> SessionActionResponse:
    """
    Clear all messages from a session while keeping the session active.

    Args:
        session_id: Session identifier

    Returns:
        SessionActionResponse indicating success or failure
    """
    try:
        memory_service = get_memory_service()

        if not memory_service.session_exists(session_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found"
            )

        success = memory_service.clear_session(session_id)

        if success:
            return SessionActionResponse(
                success=True, message="Session cleared successfully", session_id=session_id
            )
        else:
            return SessionActionResponse(
                success=False, message="Failed to clear session", session_id=session_id
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear session: {str(e)}",
        ) from e


@router.delete("/{session_id}", response_model=SessionActionResponse)
async def delete_session(session_id: str) -> SessionActionResponse:
    """
    Delete a session completely.

    Args:
        session_id: Session identifier

    Returns:
        SessionActionResponse indicating success or failure
    """
    try:
        memory_service = get_memory_service()

        if not memory_service.session_exists(session_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found"
            )

        success = memory_service.delete_session(session_id)

        if success:
            return SessionActionResponse(
                success=True, message="Session deleted successfully", session_id=session_id
            )
        else:
            return SessionActionResponse(
                success=False, message="Failed to delete session", session_id=session_id
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}",
        ) from e
