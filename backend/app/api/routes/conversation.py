"""Conversation API endpoints - Phase 5: AI Conversation Engine.

Handles user messages, multi-turn context, and grounded legal retrieval.

Endpoints:
    POST /api/conversations/{session_id}/messages - Send a message
    GET /api/conversations/{session_id} - Get conversation state
"""

from fastapi import APIRouter, HTTPException, Path, Body

from app.db.session import get_connection
from app.repositories.conversation import ConversationRepository
from app.services.conversation import ConversationService
from app.schemas.conversation import (
    ConversationResponse,
    ConversationStatus,
    ClarificationRequest,
)


router = APIRouter(prefix="/api/conversations", tags=["conversation"])


@router.post(
    "/{session_id}/messages",
    response_model=ConversationResponse,
)
def post_message(
    session_id: str = Path(..., description="Conversation session ID"),
    request: dict[str, Any] = Body(
        ...,
        description={"message": "User's message text"},
    ),
):
    """Send a message in an existing conversation and get a grounded response.

    This is the primary endpoint for Member 3's AI conversation engine.
    It:
    1. Persists the user's message
    2. Analyzes the question intent and domain
    3. Retrieves relevant legal provisions via Member 2's retrieval service
    4. Assembles grounded context from retrieved provisions
    5. Generates a structured, citation-grounded response
    6. Persists the assistant's response

    The RETRIEVE → GROUND → GENERATE principle is enforced.
    """
    message = request.get("message", "")
    if not message or not message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message must be a non-empty string",
        )

    service = ConversationService()

    with get_connection() as conn:
        # Ensure session exists
        repo = ConversationRepository(conn)
        existing = repo.get_session(session_id)
        if existing is None:
            # Auto-create session if not exists
            repo.create_session(session_id=session_id, status="active", language="nepali")

        # Add user message
        repo.add_user_message(session_id=session_id, content=message.strip())

        # Generate grounded response
        response = service.generate_grounded_response(
            query=message.strip(),
            session_id=session_id,
            top_k=5,
            minimum_score=0.3,
        )

    # The service already returns citations in the correct schema format
    # since we built them with the ConversationResponse field names.
    # Just return directly mapped.
    return ConversationResponse(
        answer=response.get("answer", ""),
        citations=response.get("citations", []),
        follow_up_questions=response.get("follow_up_questions", []),
        needs_clarification=response.get("needs_clarification", False),
        confidence=response.get("confidence", "low"),
        disclaimer=response.get("disclaimer", ""),
    )


@router.get("/{session_id}", response_model=ConversationStatus)
def get_conversation(
    session_id: str = Path(..., description="Conversation session ID"),
):
    """Retrieve conversation state and message history.

    Returns the current session status and recent messages.
    """
    with get_connection() as conn:
        repo = ConversationRepository(conn)

        # Get session
        session = repo.get_session(session_id)
        if session is None:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation session '{session_id}' not found",
            )

        # Get recent messages
        messages = repo.list_session_messages(session_id=session_id, limit=50)

        return ConversationStatus(
            session_id=session_id,
            status=session.get("status", "unknown"),
            language=session.get("language", "nepali"),
            message_count=len(messages),
            started_at=str(session.get("started_at", "")),
        )