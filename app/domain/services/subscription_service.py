from typing import Tuple
from datetime import datetime
from app.config import settings
from app.domain.entities.models.subscription import Subscription


class SubscriptionService:
    @staticmethod
    def check_subscription_status(subscription: Subscription, message_count: int) -> Tuple[str, int]:
        """Проверяет статус подписки и лимиты сообщений."""
        if not subscription or not subscription.is_active or subscription.end_date < datetime.now():
            return "free", message_count

        plan_name = subscription.plan.name.value
        if plan_name == "free" and message_count >= settings.FREE_MESSAGE_LIMIT:
            return "free", message_count
        return plan_name, message_count

    @staticmethod
    def get_upsell_trigger(plan: str, message_length: int, message_count: int) -> str:
        """Определяет триггер для предложения апгрейда подписки."""
        if plan == "free" and message_count >= settings.FREE_MESSAGE_LIMIT:
            return "limit_exhausted"
        if plan == "pro" and message_length > 500:
            return "long_messages"
        return ""
