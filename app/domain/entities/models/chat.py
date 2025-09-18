from dataclasses import dataclass
from datetime import datetime

from app.domain.entities.models.user import User


@dataclass
class Chat:
    id: int
    user: User
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime
