from typing import Any
from app.domain.entities.models.user import User
from app.infrastructure.repositories.user_use_repositories import UserUseRepositories
from app.infrastructure.logging.setup_logger import logger
from app.interfaces.telegram.services.keyboard_manager import KeyboardManager
from app.interfaces.telegram.services.message_sender import MessageSender


class StartUseCase:
    def __init__(self, user_repo: UserUseRepositories):
        self.user_repo = user_repo
        self.keyboard_manager = KeyboardManager()
        self.message_sender = MessageSender()

    async def execute(self, update: Any, context: Any) -> None:
        user_info = update.effective_user
        # Обработка реферальной ссылки
        invited_by = None
        logger.info(f"ARGS: {context.args}")
        if context.args and len(context.args) > 0 and context.args[0].startswith('ref_'):
            try:
                invited_by = int(context.args[0][4:])
                if invited_by == user_info.id:
                    invited_by = None  # нельзя пригласить самого себя
            except Exception:
                invited_by = None
        logger.info(f"invited_by: {invited_by}")
        user, created = await self.user_repo.create_or_update_user(user_info, invited_by=invited_by)

        # Проверка бана
        from datetime import datetime
        now = datetime.utcnow()
        if user.is_banned or (user.banned_until and user.banned_until > now):
            ban_msg = "Вы забанены. Обратитесь к администратору."
            if user.banned_until and user.banned_until > now:
                ban_msg = f"Вы временно забанены до {user.banned_until.strftime('%d.%m.%Y %H:%M')}."
            await update.message.reply_text(ban_msg)
            return

        logger.info(
            f"{'Новый пользователь' if created else 'Пользователь'} "
            f"{user_info.id} ({user_info.username or 'no_username'}) "
            f"{'зарегистрирован' if created else 'перезапустил бота'}."
        )

        reply_markup = self.keyboard_manager.get_lk_inline_keyboard()
        await self.message_sender.send_welcome_message(update, created, reply_markup)