from abc import ABC, abstractmethod
from app.domain.entities.models.user import User
from app.domain.entities.models.messages import Message


class IMessageRepository(ABC):
    @abstractmethod
    async def get_message_by_chat_id(self, chat) -> str | None:
        pass

    @abstractmethod
    async def get_history_messages(self, user: User, max_last_messages: int = 10) -> list[Message]:
        pass