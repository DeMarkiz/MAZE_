from dataclasses import dataclass
from datetime import datetime

from app.domain.entities.models.chat import Chat


@dataclass
class Message:
    id: int
    chat: Chat
    content: str
    is_from_user: bool
    created_at: datetime
    context_summary: str
    emotion: str
    topic: str
    importance: int
    out_of_scope: bool
