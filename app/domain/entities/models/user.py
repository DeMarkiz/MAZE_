from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class User:
    telegram_id: int
    username: str
    first_name: str
    last_name: str
    subscription_level: str
    created_at: datetime
    updated_at: datetime
    is_admin: bool = False
    is_banned: bool = False
    banned_until: datetime = None
    invited_by: Optional[int] = None  # user_id пригласившего
    referrals: List[int] = None  # список user_id приглашённых
    message_limit: int = 20  # лимит сообщений (по умолчанию 20)
    used_messages: int = 0  # использовано сообщений
