from abc import ABC, abstractmethod
from app.domain.entities.models.user import User


class ISubscriptionRepository(ABC):

    @abstractmethod
    async def check_subscription_status_by_user(self, user: User) -> tuple[str, int]:
        """Проверяет статус подписки пользователя"""
        raise NotImplementedError("При наследовании необходимо реализовать это метод")

    @abstractmethod
    async def is_active(self, user: User):
        """Проверить активность подписки"""
        raise NotImplementedError("При наследовании необходимо реализовать это метод")

    @abstractmethod
    async def get_end_date(self, user: User, plan):
        """Получить дату конца подписки и ее план"""
        raise NotImplementedError("При наследовании необходимо реализовать это метод")

    @abstractmethod
    async def get_payment_id(self, user: User):
        """Получить id платежа"""
        raise NotImplementedError("При наследовании необходимо реализовать это метод")