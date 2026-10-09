from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from models.chat_message import MessageType, SenderType


class ChatMessageCreateSchema(BaseModel):
    body: str = Field(min_length=1)
    attachment_url: str | None = None


class ChatMessageResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chat_room_id: int
    message_type: MessageType
    sender_type: SenderType
    sender_id: int | None
    body: str
    attachment_url: str | None
    created_at: datetime
