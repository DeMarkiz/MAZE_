from typing import Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timezone
from app.infrastructure.database.models.user import UserModel
from app.infrastructure.database.models.subscribe import SubscriptionModel, PlanName
from app.infrastructure.repositories.user_use_repositories import UserUseRepositories
from app.infrastructure.repositories.subscription_use_repositories import SubscriptionUseRepositories
from app.infrastructure.logging.setup_logger import logger


class LkUseCase:
    def __init__(self, user_repo: UserUseRepositories, subscription_repo: SubscriptionUseRepositories):
        self.user_repo = user_repo
        self.subscription_repo = subscription_repo

    async def execute(self, update: Any, context: Any) -> None:
        user = await UserModel.get_or_none(telegram_id=update.effective_user.id)
        if not user:
            await update.message.reply_text("Пожалуйста, сначала запустите бота командой /start")
            return
        now = datetime.now(timezone.utc)
        if user.is_banned or (user.banned_until and user.banned_until > now):
            ban_msg = "Вы забанены. Обратитесь к администратору."
            if user.banned_until and user.banned_until > now:
                ban_msg = f"Вы временно забанены до {user.banned_until.strftime('%d.%m.%Y %H:%M')}."
            if update.callback_query:
                await update.callback_query.edit_message_text(ban_msg)
            else:
                await update.message.reply_text(ban_msg)
            return

        active_sub = await SubscriptionModel.filter(
            user=user,
            is_active=True,
            end_date__gte=now
        ).order_by("-end_date").select_related("plan").first()

        status = "Free"
        days = 0
        until = "не активна"
        if active_sub and active_sub.plan:
            status = f"⭐️ PRO" if active_sub.plan.name == PlanName.PRO else f"👑 VIP"
            days = (active_sub.end_date - now).days
            until = active_sub.end_date.strftime("%d.%m.%Y")

        text = (
            f"<b>👤 Личный кабинет @{user.username or user.telegram_id}</b>\n\n"
            f"💎 <b>Статус:</b> {status}\n"
            f"⏳ <b>Осталось дней:</b> {days}\n"
            f"📅 <b>Подписка до:</b> {until}"
        )
        buttons = []
        if active_sub and active_sub.plan:
            buttons.append([InlineKeyboardButton(text="🔄 Продлить подписку", callback_data="renew_sub")])
        buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main_menu")])
        reply_markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        if update.callback_query:
            try:
                await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="HTML")
            except Exception as e:
                if "Message is not modified" not in str(e):
                    raise
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")

        # Добавляем блок про рефералов
        bot_username = (await context.bot.get_me()).username
        referral_link = f"https://t.me/{bot_username}?start=ref_{user.telegram_id}"
        referrals = user.referrals or []
        referrals_text = "\n".join([f"- <code>{uid}</code>" for uid in referrals]) if referrals else "Пока никого не пригласили."
        referral_block = (
            f"\n\n<b>Приведи друга и получи +5 сообщений!</b>\n"
            f"Твоя ссылка: <code>{referral_link}</code>\n"
            f"Скопируйте и отправьте эту ссылку другу, чтобы получить +5 сообщений!\n"
            f"<i>Бонус начисляется только если друг впервые запускает бота по вашей ссылке.</i>\n"
            f"<i>Если друг уже запускал бота, пусть отправит команду</i> <code>/start ref_{user.telegram_id}</code> <i>вручную.</i>\n"
            f"Приглашено: {len(referrals)}\n"
            f"{referrals_text}"
        )
        text += referral_block

        # Формируем reply_markup без кнопки 'Приведи друга'
        buttons = []
        if active_sub and active_sub.plan:
            buttons.append([InlineKeyboardButton(text="🔄 Продлить подписку", callback_data="renew_sub")])
        buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main_menu")])
        reply_markup = InlineKeyboardMarkup(inline_keyboard=buttons)

        if update.callback_query:
            try:
                await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="HTML")
            except Exception as e:
                if "Message is not modified" not in str(e):
                    raise
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")