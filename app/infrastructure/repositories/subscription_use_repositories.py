from datetime import datetime
from app.domain.repositories.subscription_repositories import ISubscriptionRepository
from app.infrastructure.database.models.message import MessageModel
from app.infrastructure.database.models.subscribe import PlanName, SubscriptionModel
from app.infrastructure.database.models.user import UserModel
from app.domain.entities.models.user import User
from app.infrastructure.logging.setup_logger import logger


class SubscriptionUseRepositories(ISubscriptionRepository):
    async def check_subscription_status_by_user(self, user: User) -> tuple[str, int]:
        """Проверяет статус подписки пользователя
           Возвращает: План подписки, количество сообщений
        """
        active_subscription = (
            await SubscriptionModel.filter(
                user_id=user.telegram_id, is_active=True, end_date__gte=datetime.utcnow()
            )
            .prefetch_related("plan")
            .first()
        )

        current_plan = "free"
        if active_subscription:
            current_plan = active_subscription.plan.name.value
        # Обновляем статус пользователя в БД, если он изменился
        user_model = await UserModel.get_or_none(telegram_id=user.telegram_id)
        if user_model and user_model.subscription_level != current_plan and not (user_model.subscription_level is None and current_plan == "free"):
            user_model.subscription_level = PlanName[current_plan.upper()] if current_plan != "free" else None
            await user_model.save(update_fields=["subscription_level"])

        message_count = await MessageModel.filter(chat__user=user.telegram_id, is_from_user=True).count()

        return current_plan, message_count

    async def is_active(self, user: User) -> bool:
        """Проверить активность подписки"""
        try:
            subscription = await SubscriptionModel.filter(user_id=user.telegram_id).first()
            if subscription and subscription.is_active and subscription.end_date >= datetime.utcnow():
                logger.info(f'Подписка активна для пользователя {user.telegram_id}')
                return True
            logger.info(f'Подписка не активна для пользователя {user.telegram_id}')
            return False
        except Exception as e:
            logger.error(f'Ошибка при проверке активности подписки для пользователя {user.telegram_id}: {e}')
            return False

    async def get_end_date(self, user: User, plan: str) -> datetime | None:
        """Получить дату конца подписки и ее план"""
        try:
            subscription = await SubscriptionModel.filter(
                user_id=user.telegram_id,
                plan__name=plan  # Фильтр по имени плана
            ).first()
            if subscription:
                logger.info(f'Получена дата окончания подписки {subscription.end_date} для пользователя {user.telegram_id}')
                return subscription.end_date
            logger.warning(f'Не получена дата окончания подписки для пользователя {user.telegram_id}')
            return None
        except Exception as e:
            logger.error(f'Ошибка при получении даты окончания подписки для пользователя {user.telegram_id}: {e}')
            return None

    async def get_payment_id(self, user: User) -> str | None:
        """Получить id платежа"""
        try:
            subscription = await SubscriptionModel.filter(user_id=user.telegram_id).first()
            if subscription and subscription.payment_id:
                logger.info(f'Получен id платежа {subscription.payment_id} для пользователя {user.telegram_id}')
                return subscription.payment_id
            logger.warning(f'Не получен id платежа для пользователя {user.telegram_id}')
            return None
        except Exception as e:
            logger.error(f'Ошибка при получении id платежа для пользователя {user.telegram_id}: {e}')
            return None