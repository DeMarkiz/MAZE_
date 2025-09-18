from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.infrastructure.database.models.subscribe import SubscriptionPlanModel, PlanName


class KeyboardManager:
    @staticmethod
    async def get_subscription_keyboard() -> InlineKeyboardMarkup:
        plans = await SubscriptionPlanModel.filter(is_active=True).all()
        keyboard = [
            [InlineKeyboardButton(
                text=(f"⭐️ {plan.name.value.upper()} - ${plan.price_usd}" if plan.name == PlanName.PRO else f"👑 {plan.name.value.upper()} - ${plan.price_usd}"),
                callback_data=f"choose_plan:{plan.name.value}"
            )] for plan in plans
        ]
        keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_lk")])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_upsell_keyboard(offer: dict, callback_data: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=offer["button"], callback_data=callback_data)]])

    @staticmethod
    def get_lk_inline_keyboard() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="📱 Личный кабинет", callback_data="open_lk")]]
        )

    @staticmethod
    def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text="Изменить цены", callback_data="admin_change_prices")],
            [InlineKeyboardButton(text="Добавить подписку", callback_data="admin_add_subscription")],
            [InlineKeyboardButton(text="Удалить подписку", callback_data="admin_remove_subscription")],
            [InlineKeyboardButton(text="Поиск пользователя", callback_data="admin_search_user")],
            [InlineKeyboardButton(text="Управление пользователем", callback_data="admin_manage_user")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)