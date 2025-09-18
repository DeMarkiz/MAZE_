from typing import Any
from aiogram.types import InlineKeyboardMarkup
from app.core.bot_character import NEURO_ASSISTANT
from app.interfaces.telegram.services.keyboard_manager import KeyboardManager


class MessageSender:
    async def send_welcome_message(self, update: Any, is_new_user: bool, reply_markup: InlineKeyboardMarkup) -> None:
        if is_new_user:
            welcome_text = (
                "Maze активен. Говори."
            )
        else:
            welcome_text = "С возвращением! Чем могу помочь?"
        
        await update.message.reply_text(welcome_text, parse_mode="HTML")

    async def send_error(self, update: Any, message: str) -> None:
        if update.callback_query:
            await update.callback_query.answer(message, show_alert=True)
        else:
            await update.message.reply_text(message)

    async def send_upsell_offer(self, update: Any, context: Any, trigger: str) -> None:
        offer = None
        callback_data = ""
        if trigger in NEURO_ASSISTANT.upsell_triggers["base_to_pro"]:
            offer = NEURO_ASSISTANT.upsell_triggers["base_to_pro"][trigger]
            callback_data = "upgrade_pro"
        elif trigger in NEURO_ASSISTANT.upsell_triggers["pro_to_vip"]:
            offer = NEURO_ASSISTANT.upsell_triggers["pro_to_vip"][trigger]
            callback_data = "upgrade_vip"
        elif trigger in NEURO_ASSISTANT.upsell_triggers["contextual"]:
            offer = NEURO_ASSISTANT.upsell_triggers["contextual"][trigger]
            callback_data = "upgrade_pro"

        if offer:
            reply_markup = KeyboardManager.get_upsell_keyboard(offer, callback_data)
            await update.message.reply_text(text=offer["text"], reply_markup=reply_markup)
