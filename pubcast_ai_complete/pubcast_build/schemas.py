"""
Pydantic schemas for PubCast AI WebSocket messages.
Provides strict input validation, sanitization, and type safety.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, Union
import html
import logging

logger = logging.getLogger("pubcast.schemas")

# Constants
MAX_MESSAGE_LENGTH = 10000
MIN_MESSAGE_LENGTH = 1
MAX_ROOM_ID_LENGTH = 256
MAX_USER_ID_LENGTH = 256
MAX_INTENT_LENGTH = 200


class ChatMessage(BaseModel):
    """Standard chat message from user."""
    type: Literal["chat"] = "chat"
    text: str = Field(..., min_length=MIN_MESSAGE_LENGTH, max_length=MAX_MESSAGE_LENGTH)
    room_id: Optional[str] = Field(None, max_length=MAX_ROOM_ID_LENGTH)
    user_id: Optional[str] = Field(None, max_length=MAX_USER_ID_LENGTH)
    
    @field_validator('text')
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        """Prevent XSS and normalize whitespace."""
        # HTML escape dangerous characters
        v = html.escape(v, quote=True)
        # Normalize whitespace (collapse multiple spaces)
        v = ' '.join(v.split())
        return v.strip()
    
    @field_validator('room_id', 'user_id')
    @classmethod
    def validate_ids(cls, v: Optional[str]) -> Optional[str]:
        """Validate ID format (alphanumeric + underscore/hyphen)."""
        if v is None:
            return v
        if not all(c.isalnum() or c in ('_', '-') for c in v):
            raise ValueError("IDs must be alphanumeric with underscores/hyphens only")
        return v


class FeedbackMessage(BaseModel):
    """User feedback on a response."""
    type: Literal["feedback"] = "feedback"
    response_id: str = Field(..., min_length=1, max_length=256)
    positive: bool
    comment: Optional[str] = Field(None, max_length=1000)
    
    @field_validator('comment')
    @classmethod
    def sanitize_comment(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return html.escape(v.strip(), quote=True)


class CorrectionMessage(BaseModel):
    """User correction of intent recognition."""
    type: Literal["correction"] = "correction"
    message_id: str = Field(..., min_length=1, max_length=256)
    correct_intent: str = Field(..., min_length=1, max_length=MAX_INTENT_LENGTH)
    original_intent: Optional[str] = Field(None, max_length=MAX_INTENT_LENGTH)
    
    @field_validator('correct_intent', 'original_intent')
    @classmethod
    def sanitize_intent(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = html.escape(v.strip(), quote=True)
        if not all(c.isalnum() or c in ('_', ' ', '-') for c in v):
            raise ValueError("Intent names must be alphanumeric")
        return v


class PersonaSelectionMessage(BaseModel):
    """Request to set session persona."""
    type: Literal["set_persona"] = "set_persona"
    persona_name: str = Field(..., min_length=1, max_length=128)
    
    @field_validator('persona_name')
    @classmethod
    def validate_persona_name(cls, v: str) -> str:
        v = v.strip()
        if not all(c.isalnum() or c in ('_', '-', ' ') for c in v):
            raise ValueError("Persona names must be alphanumeric")
        return v


class RoomJoinMessage(BaseModel):
    """Request to join a room."""
    type: Literal["join_room"] = "join_room"
    room_id: str = Field(..., min_length=1, max_length=MAX_ROOM_ID_LENGTH)
    user_id: str = Field(..., min_length=1, max_length=MAX_USER_ID_LENGTH)
    
    @field_validator('room_id', 'user_id')
    @classmethod
    def validate_ids(cls, v: str) -> str:
        if not all(c.isalnum() or c in ('_', '-') for c in v):
            raise ValueError("IDs must be alphanumeric with underscores/hyphens")
        return v


class PingMessage(BaseModel):
    """Heartbeat ping from client."""
    type: Literal["ping"] = "ping"
    timestamp: Optional[float] = None


# Discriminated union for all valid message types
WebSocketMessage = Union[
    ChatMessage,
    FeedbackMessage,
    CorrectionMessage,
    PersonaSelectionMessage,
    RoomJoinMessage,
    PingMessage
]


def validate_websocket_message(data: dict) -> tuple[str, BaseModel]:
    """
    Validate raw JSON data against schema.
    
    Returns:
        (message_type, validated_model)
    
    Raises:
        ValueError: If validation fails
    """
    msg_type = data.get("type", "chat")
    
    try:
        if msg_type == "chat":
            model = ChatMessage(**data)
        elif msg_type == "feedback":
            model = FeedbackMessage(**data)
        elif msg_type == "correction":
            model = CorrectionMessage(**data)
        elif msg_type == "set_persona":
            model = PersonaSelectionMessage(**data)
        elif msg_type == "join_room":
            model = RoomJoinMessage(**data)
        elif msg_type == "ping":
            model = PingMessage(**data)
        else:
            raise ValueError(f"Unknown message type: {msg_type}")
        
        return msg_type, model
    except Exception as e:
        logger.warning(f"Message validation failed for type '{msg_type}': {e}")
        raise ValueError(f"Invalid message format: {str(e)}")


# Response models for WebSocket events
class StreamEventResponse(BaseModel):
    """Standard streaming response."""
    type: Literal["stream"] = "stream"
    agent_id: str
    chunk: str
    metadata: Optional[dict] = None


class CompleteEventResponse(BaseModel):
    """Message completion event."""
    type: Literal["complete"] = "complete"
    message_id: str
    agent_id: str
    total_tokens: Optional[int] = None


class ErrorEventResponse(BaseModel):
    """Error response."""
    type: Literal["error"] = "error"
    error: str
    error_code: Optional[str] = None
    recoverable: bool = True


class PongMessage(BaseModel):
    """Heartbeat pong response."""
    type: Literal["pong"] = "pong"
    timestamp: float
