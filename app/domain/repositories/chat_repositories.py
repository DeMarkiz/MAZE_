from abc import ABC, abstractmethod

from app.domain.entities.models.user import User


class IChatRepository(ABC):

    @abstractmethod
    async def get_time_last_message_by_chat_on_user(self, user: User) -> object:
        '''Получить время последнего сообщения в чате пользователя.'''
        raise NotImplementedError("При наследовании необходимо реализовать это метод")

    async def get_history(self, user_id: str, max_messages: int) -> object:
        '''Получить историю чата.'''
        raise NotImplementedError("При наследовании необходимо реализовать это метод")