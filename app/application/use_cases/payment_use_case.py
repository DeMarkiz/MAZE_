from typing import Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.infrastructure.database.models.user import UserModel
from app.infrastructure.services.youmoney import create_payment
from app.infrastructure.logging.setup_logger import logger
from fastapi import HTTPException


class PaymentUseCase:
    async def send_payment_link(self, update: Any, context: Any, plan_name: str) -> None:
        chat_id = update.effective_chat.id
        message = getattr(update, 'message', None) or update.callback_query.message

        user = await UserModel.get_or_none(telegram_id=chat_id)
        if not user:
            await message.reply_text("Сначала начните диалог с ботом командой /start")
            return

        plan_id = None
        if plan_name == "pro":
            plan_id = 1
        elif plan_name == "vip":
            plan_id = 2
        if not plan_id:
            await message.reply_text("Такой план подписки не найден.")
            return

        try:
            label, payment_url, amount_rub = await create_payment(plan_id, user.telegram_id)
            context.user_data["last_payment_label"] = label
            keyboard = [[InlineKeyboardButton(text=f"💎 Оплатить {plan_name.upper()} ({amount_rub}₽)", url=payment_url)]]
            reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
            await message.reply_text(
                f"Для получения доступа к плану {plan_name.upper()}, пожалуйста, оплатите {amount_rub}₽ по ссылке ниже.",
                reply_markup=reply_markup,
            )
            await message.reply_text(
                "После оплаты вы автоматически получите доступ. Если оплата не прошла — нажмите кнопку ниже, чтобы повторить попытку.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="🔄 Проверить оплату", callback_data=f"check_payment:{label}")]]
                )
            )
        except HTTPException as e:
            logger.error(f"Ошибка при создании сессии оплаты: {e.detail}")
            await message.reply_text("Не удалось создать ссылку на оплату. Попробуйте позже.")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при создании ссылки на оплату: {e}")
            await message.reply_text("Произошла внутренняя ошибка. Пожалуйста, попробуйте еще раз позже.")