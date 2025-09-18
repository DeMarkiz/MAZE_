from tortoise.transactions import in_transaction
from app.domain.repositories.user_repositories import IUserRepository
from app.infrastructure.database.models.user import UserModel
from app.infrastructure.logging.setup_logger import logger
from app.domain.entities.models.user import User
from datetime import datetime
from app.infrastructure.database.models.subscribe import PlanName


class UserUseRepositories(IUserRepository):
    async def get_user_by_telegram_id(self, telegram_id: int) -> User | None:
        try:
            user_model = await UserModel.get_or_none(telegram_id=telegram_id)
            if user_model:
                logger.info(f"Пользователь с id {telegram_id} найден")
                return User(
                    telegram_id=user_model.telegram_id,
                    username=user_model.username or "",
                    first_name=user_model.first_name or "",
                    last_name=user_model.last_name or "",
                    subscription_level=user_model.subscription_level.value if user_model.subscription_level else "free",
                    created_at=user_model.created_at,
                    updated_at=user_model.updated_at,
                    is_admin=getattr(user_model, 'is_admin', False),
                    is_banned=getattr(user_model, 'is_banned', False),
                    banned_until=getattr(user_model, 'banned_until', None),
                    invited_by=getattr(user_model, 'invited_by_id', None),
                    referrals=getattr(user_model, 'referrals', []),
                    message_limit=getattr(user_model, 'message_limit', 20),
                    used_messages=getattr(user_model, 'used_messages', 0)
                )
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя {telegram_id}: {e}")
            return None

    async def get_user_model_by_telegram_id(self, telegram_id: int):
        return await UserModel.get_or_none(telegram_id=telegram_id)

    async def create_or_update_user(self, tg_user, invited_by=None):
        async with in_transaction():
            try:
                existing_user_model = await UserModel.get_or_none(telegram_id=tg_user.id)
                if existing_user_model:
                    logger.info(f"Пользователь {tg_user.id} найден")
                    return (
                        User(
                            telegram_id=existing_user_model.telegram_id,
                            username=existing_user_model.username or "",
                            first_name=existing_user_model.first_name or "",
                            last_name=existing_user_model.last_name or "",
                            subscription_level=existing_user_model.subscription_level.value if existing_user_model.subscription_level else "free",
                            created_at=existing_user_model.created_at,
                            updated_at=existing_user_model.updated_at,
                            is_admin=getattr(existing_user_model, 'is_admin', False),
                            is_banned=getattr(existing_user_model, 'is_banned', False),
                            banned_until=getattr(existing_user_model, 'banned_until', None),
                            invited_by=getattr(existing_user_model, 'invited_by_id', None),
                            referrals=getattr(existing_user_model, 'referrals', []),
                            message_limit=getattr(existing_user_model, 'message_limit', 20),
                            used_messages=getattr(existing_user_model, 'used_messages', 0)
                        ),
                        False
                    )

                # Новый пользователь
                new_user_model = await UserModel.create(
                    telegram_id=tg_user.id,
                    username=tg_user.username,
                    first_name=tg_user.first_name,
                    last_name=tg_user.last_name,
                    subscription_level=PlanName.FREE,  # Используем Enum
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    is_admin=(tg_user.id == 426391848),
                    is_banned=False,
                    banned_until=None,
                    invited_by=invited_by,
                    referrals=[],
                    message_limit=20,
                    used_messages=0
                )
                logger.info(f"Пользователь {new_user_model.telegram_id} создан")

                # Если есть пригласивший, добавляем в его referrals и начисляем бонус
                if invited_by:
                    inviter = await UserModel.get_or_none(telegram_id=invited_by)
                    if inviter and tg_user.id not in (inviter.referrals or []):
                        inviter.referrals = (inviter.referrals or []) + [tg_user.id]
                        inviter.message_limit = getattr(inviter, 'message_limit', 20) + 5
                        await inviter.save(update_fields=["referrals", "message_limit"])

                return (
                    User(
                        telegram_id=new_user_model.telegram_id,
                        username=new_user_model.username or "",
                        first_name=new_user_model.first_name or "",
                        last_name=new_user_model.last_name or "",
                        subscription_level=new_user_model.subscription_level.value,
                        created_at=new_user_model.created_at,
                        updated_at=new_user_model.updated_at,
                        is_admin=getattr(new_user_model, 'is_admin', False),
                        is_banned=getattr(new_user_model, 'is_banned', False),
                        banned_until=getattr(new_user_model, 'banned_until', None),
                        invited_by=getattr(new_user_model, 'invited_by_id', None),
                        referrals=getattr(new_user_model, 'referrals', []),
                        message_limit=getattr(new_user_model, 'message_limit', 20),
                        used_messages=getattr(new_user_model, 'used_messages', 0)
                    ),
                    True
                )
            except Exception as e:
                logger.error(f"Ошибка при создании/получении пользователя {tg_user.id}: {e}")
                return None, False

    async def add_admin(self, telegram_id: int) -> None:
        user = await UserModel.get_or_none(telegram_id=telegram_id)
        if user:
            user.is_admin = True
            await user.save(update_fields=["is_admin"])

    async def remove_admin(self, telegram_id: int) -> None:
        user = await UserModel.get_or_none(telegram_id=telegram_id)
        if user:
            user.is_admin = False
            await user.save(update_fields=["is_admin"])

    async def get_admins(self) -> list[User]:
        users = await UserModel.filter(is_admin=True).all()
        return [
            User(
                telegram_id=u.telegram_id,
                username=u.username or "",
                first_name=u.first_name or "",
                last_name=u.last_name or "",
                subscription_level=u.subscription_level.value if u.subscription_level else "free",
                created_at=u.created_at,
                updated_at=u.updated_at,
                is_admin=True
            ) for u in users
        ]