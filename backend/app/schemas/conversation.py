"""Schema models for conversation API contracts."""

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """A citation grounding the AI's answer to a retrieved legal provision."""

    document: str = Field(..., description="Title of the legal document")
    section: str = Field(..., description="Section number or article title")
    provision: str = Field(..., description="Provision text or heading")
    source: str = Field(..., description="Source name")
    source_url: str = Field(None, description="Official URL if available")
    score: float = Field(..., description="Relevance score 0.0-1.0")


class FollowUpQuestion(BaseModel):
    """A suggested follow-up question for the user."""
    question: str = Field(..., description="The follow-up question text")
    reason: str | None = Field(None, description="Why this follow-up is suggested")


class ConversationResponse(BaseModel):
    """Structured AI response grounded on retrieved legal provisions."""

    answer: str = Field(..., description="The AI's answer in the user's language")
    citations: list[Citation] = Field(
        default_factory=list,
        description="Legal provisions cited as the basis for the answer",
    )
    follow_up_questions: list[FollowUpQuestion] = Field(
        default_factory=list,
        description="Suggested follow-up questions",
    )
    needs_clarification: bool = Field(
        default=False,
        description="Whether the response identifies missing information",
    )
    confidence: str = Field(
        ..., description="Confidence level: high|medium|low",
    )
    disclaimer: str = Field(
        ...,
        description="Disclaimer about legal advice",
    )


class ClarificationRequest(BaseModel):
    """A request for clarification from the user."""

    question: str = Field(..., description="The clarification question")
    missing_info: str = Field(
        ..., description="What information is missing",
    )
    suggested_approach: str = Field(
        ..., description="How to proceed with the information",
    )


class ConversationStatus(BaseModel):
    """Current conversation session status."""

    session_id: str = Field(..., description="Unique session identifier")
    status: str = Field(..., description="Session status (active, ended)")
    language: str = Field("nepali", description="User's preferred language")
    message_count: int = Field(
        default=0,
        description="Number of messages in the conversation",
    )
    started_at: str | None = Field(
        None, description="When the conversation started",
    )