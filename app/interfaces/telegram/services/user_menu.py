from typing import Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class UserMenuHandler:
    MODES = [
        ("🟢 Soft", "Мягкий, поддерживающий стиль"),
        ("🔥 Toxic", "Жёсткий, прямой стиль, без оскорблений"),
        ("🪞 Mirror", "Зеркало: задаёт вопросы, помогает разобраться"),
        ("📖 Philosopher", "Философский, глубокий стиль"),
        ("😈 Humor", "Юмор, мемы, сарказм, лёгкость")
    ]

    async def show_main_menu(self, update: Any, context: Any):
        keyboard = [
            [InlineKeyboardButton(text="📱 Личный кабинет", callback_data="open_lk")],
            [InlineKeyboardButton(text="💎 Апгрейд подписки", callback_data="upgrade")],
        ]
        text = (
            "<b>Главное меню</b>\n\n"
            "Выберите действие:\n"
            "\n📱 <b>Личный кабинет</b> — управление подпиской и профилем."
            "\n💎 <b>Апгрейд подписки</b> — откройте PRO или VIP-возможности."
        )
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        if hasattr(update, "callback_query") and update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")
        else:
            await update.message.reply_text(text, reply_markup=markup, parse_mode="HTML")

    async def show_upgrade_menu(self, update: Any, context: Any):
        from app.infrastructure.database.models.subscribe import SubscriptionPlanModel, PlanName
        plans = await SubscriptionPlanModel.filter(is_active=True).all()
        pro = next((p for p in plans if p.name == PlanName.PRO), None)
        vip = next((p for p in plans if p.name == PlanName.VIP), None)
        keyboard = [
            [InlineKeyboardButton(text="⭐️ PRO", callback_data="upgrade_pro")],
            [InlineKeyboardButton(text="👑 VIP", callback_data="upgrade_vip")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main_menu")],
        ]
        text = (
            "<b>Выберите подписку для апгрейда:</b>\n\n"
            "⭐️ <b>PRO</b>\n"
            f"<i>Цена: {pro.price_usd if pro else '-'}₽/мес</i>\n"
            "• Доступ к расширенным функциям\n"
            "• Больше лимитов\n\n"
            "👑 <b>VIP</b>\n"
            f"<i>Цена: {vip.price_usd if vip else '-'}₽/мес</i>\n"
            "• Все возможности PRO\n"
            "• Персональный приоритет\n"
            "• Максимальные лимиты\n"
        )
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

    async def show_modes_menu(self, update: Any, context: Any):
        keyboard = [[InlineKeyboardButton(text=f"{name} — {desc}", callback_data=f"set_mode:{i}")] for i, (name, desc) in enumerate(self.MODES)]
        keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main_menu")])
        text = (
            "<b>🤖 Режимы бота</b>\n\n"
            "Выберите стиль работы ассистента:\n" +
            "\n".join([f"{i+1}. <b>{name}</b> — {desc}" for i, (name, desc) in enumerate(self.MODES)])
        )
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

    async def set_mode(self, update: Any, context: Any, mode_index: int):
        context.user_data["bot_mode"] = mode_index
        name, desc = self.MODES[mode_index]
        text = f"<b>🤖 Режим бота установлен:</b> {name} — {desc}"
        await update.callback_query.edit_message_text(text, reply_markup=None, parse_mode="HTML")
        await self.show_main_menu(update, context)

    async def handle_callback(self, update: Any, context: Any, data: str):
        if data == "back_to_main_menu":
            await self.show_main_menu(update, context)
        elif data == "upgrade":
            await self.show_upgrade_menu(update, context)
        elif data == "choose_mode":
            await self.show_modes_menu(update, context)
        elif data.startswith("set_mode:"):
            mode_index = int(data.split(":")[1])
            await self.set_mode(update, context, mode_index)
        elif data in ("upgrade_pro", "upgrade_vip"):
            # Здесь можно вызвать PaymentUseCase или другой flow оплаты
            await update.callback_query.edit_message_text(
                f"<b>💳 Переход к оплате:</b> {data.replace('upgrade_', '').upper()}\n\nСледуйте дальнейшим инструкциям.",
                parse_mode="HTML"
            )
        elif data == "open_lk":
            # Вызвать личный кабинет
            from app.application.use_cases.lk_use_case import LkUseCase
            from app.infrastructure.repositories.user_use_repositories import UserUseRepositories
            from app.infrastructure.repositories.subscription_use_repositories import SubscriptionUseRepositories
            user_repo = UserUseRepositories()
            sub_repo = SubscriptionUseRepositories()
            lk_use_case = LkUseCase(user_repo, sub_repo)
            await lk_use_case.execute(update, context) 
