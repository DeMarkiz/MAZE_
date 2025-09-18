from abc import ABC, abstractmethod

from app.domain.entities.models.user import User


class IUserRepository(ABC):

    @abstractmethod
    async def get_user_by_telegram_id(self, telegram_id: int) -> User | None:
        """Получить пользователя по id в телеграме"""
        raise NotImplementedError("При наследовании необходимо реализовать это метод")

    @abstractmethod
    async def create_or_update_user(self, tg_user) -> tuple[User | None, bool]:
        """Создать пользователя"""
        raise NotImplementedError("При наследовании необходимо реализовать это метод")

    @abstractmethod
    async def add_admin(self, telegram_id: int) -> None:
        """Добавить пользователя в админы"""
        raise NotImplementedError("При наследовании необходимо реализовать это метод")

    @abstractmethod
    async def remove_admin(self, telegram_id: int) -> None:
        """Удалить пользователя из админов"""
        raise NotImplementedError("При наследовании необходимо реализовать это метод")

    @abstractmethod
    async def get_admins(self) -> list[User]:
        """Получить всех админов"""
        raise NotImplementedError("При наследовании необходимо реализовать это метод")
