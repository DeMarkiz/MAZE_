import logging
from datetime import datetime, timedelta
from decimal import Decimal

from app.infrastructure.database.models.subscribe import (SubscriptionModel,
                                                          SubscriptionPlanModel)
from app.infrastructure.database.models.user import UserModel

logger = logging.getLogger(__name__)

# FREE_MESSAGE_LIMIT = 60  # Лимит сообщений для бесплатного уровня

# async def check_subscription_status(user: UserModel) -> tuple[str, int]:
#     """
#     Проверяет статус подписки пользователя.
#     Возвращает кортеж: (plan_name: str, message_count: int).
#     """
#     # Сначала проверяем, есть ли активная подписка
#     active_subscription = (
#         await SubscriptionModel.filter(
#             user=user, is_active=True, end_date__gte=datetime.utcnow()
#         )
#         .prefetch_related("plan")
#         .first()
#     )
#
#     current_plan = "free"
#     if active_subscription:
#         current_plan = active_subscription.plan.name.value  # pro или vip
#
#     # Обновляем статус пользователя в БД, если он изменился
#     if user.subscription_level != current_plan and not (
#         user.subscription_level is None and current_plan == "free"
#     ):
#         user.subscription_level = (
#             PlanName[current_plan.upper()] if current_plan != "free" else None
#         )
#         await user.save(update_fields=["subscription_level"])
#
#     message_count = await MessageModel.filter(chat__user=user, is_from_user=True).count()
#
#     return current_plan, message_count


async def activate_subscription_for_user(user_id: int, plan_id: int, payment_id: str, payment_amount: Decimal):
    """
    Активирует или продлевает подписку для пользователя.
    """

    user = await UserModel.get_or_none(telegram_id=user_id)  # ищем по telegram_id
    plan = await SubscriptionPlanModel.get_or_none(id=plan_id)

    if not user or not plan:
        logger.error(
            f"Не удалось найти пользователя {user_id} или план {plan_id} для активации подписки."
        )
        return

    # Проверяем, есть ли у пользователя уже активная подписка того же уровня или выше
    existing_subscription = (
        await SubscriptionModel.filter(
            user=user, is_active=True, end_date__gte=datetime.utcnow()
        )
        .prefetch_related("plan")
        .first()
    )

    start_date = datetime.utcnow()
    # Если есть активная подписка, продлеваем ее
    if existing_subscription and existing_subscription.plan.name == plan.name:
        start_date = existing_subscription.end_date
        logger.info(
            f"Продление подписки {plan.name} для пользователя {user_id} с {start_date}."
        )
    else:
        # Деактивируем старые подписки, если они есть
        await SubscriptionModel.filter(user=user, is_active=True).update(is_active=False)
        logger.info(f"Создание новой подписки {plan.name} для пользователя {user_id}.")

    end_date = start_date + timedelta(days=plan.duration_days)

    # Создаем новую запись о подписке
    await SubscriptionModel.create(
        user=user,
        plan=plan,
        start_date=start_date,
        end_date=end_date,
        is_active=True,
        payment_id=payment_id,
        payment_amount=payment_amount,
    )

    # Обновляем статус пользователя
    user.subscription_level = plan.name
    await user.save()

    logger.info(
        f"Подписка '{plan.name.value}' для пользователя {user.telegram_id} успешно активирована до {end_date}."
    )
