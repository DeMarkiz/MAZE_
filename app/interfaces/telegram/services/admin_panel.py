from typing import Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.infrastructure.repositories.user_use_repositories import UserUseRepositories
from app.infrastructure.database.models.subscribe import SubscriptionPlanModel
from app.infrastructure.database.models.user import UserModel
from app.application.use_cases.subscriptions import activate_subscription_for_user

class AdminPanelHandler:
    def __init__(self):
        self.user_repo = UserUseRepositories()

    async def handle_callback(self, update: Any, context: Any, data: str):
        if data == "admin_change_prices":
            await self.show_price_list(update)
        elif data.startswith("admin_edit_price:"):
            await self.ask_new_price(update, context, data)
        elif data == "admin_add_subscription":
            await self.ask_username_for_subscription(update, context)
        elif data.startswith("admin_add_subscription_plan:"):
            await self.add_subscription_to_user(update, context, data)
        elif data == "admin_remove_subscription":
            await self.ask_username_for_remove_subscription(update, context)
        elif data.startswith("admin_remove_subscription_plan:"):
            await self.remove_subscription_from_user(update, context, data)
        elif data == "admin_search_user":
            await self.ask_username_for_search(update, context)
        elif data == "admin_manage_user":
            await self.ask_username_for_manage(update, context)
        elif data.startswith("admin_user_action:"):
            await self.handle_user_action(update, context, data)
        elif data == "admin_back":
            await self.show_main_panel(update, context)
        else:
            await update.callback_query.answer("Неизвестная команда", show_alert=True)

    async def handle_text(self, update: Any, context: Any):
        user = await self.user_repo.get_user_by_telegram_id(update.effective_user.id)
        if not user or not user.is_admin:
            return
        if context.user_data.get("edit_price_plan_id"):
            await self.set_new_price(update, context)
            return
        if context.user_data.get("admin_add_subscription"):
            await self.ask_plan_for_subscription(update, context)
            return
        if context.user_data.get("admin_remove_subscription"):
            await self.ask_plan_for_remove_subscription(update, context)
            return
        if context.user_data.get("admin_search_user"):
            await self.show_user_info(update, context)
            return
        if context.user_data.get("admin_manage_user"):
            await self.show_manage_user_panel(update, context)
            return

    async def show_main_panel(self, update, context):
        keyboard = [
            [InlineKeyboardButton(text="💸 Изменить цены", callback_data="admin_change_prices")],
            [InlineKeyboardButton(text="➕ Добавить подписку", callback_data="admin_add_subscription")],
            [InlineKeyboardButton(text="➖ Удалить подписку", callback_data="admin_remove_subscription")],
            [InlineKeyboardButton(text="🔍 Поиск пользователя", callback_data="admin_search_user")],
            [InlineKeyboardButton(text="👤 Управление пользователем", callback_data="admin_manage_user")],
        ]
        text = (
            "<b>👑 Админ-панель</b>\n\n"
            "💸 <b>Изменить цены</b> — редактировать стоимость подписок.\n"
            "➕ <b>Добавить подписку</b> — выдать подписку пользователю.\n"
            "➖ <b>Удалить подписку</b> — снять подписку с пользователя.\n"
            "🔍 <b>Поиск пользователя</b> — найти пользователя по username или id.\n"
            "👤 <b>Управление пользователем</b> — бан, разбан, удаление, инфо.\n"
        )
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        if hasattr(update, "callback_query") and update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")
        else:
            await update.message.reply_text(text, reply_markup=markup, parse_mode="HTML")

    async def show_price_list(self, update):
        from app.infrastructure.database.models.subscribe import SubscriptionPlanModel
        plans = await SubscriptionPlanModel.all()
        keyboard = [
            [InlineKeyboardButton(f"{plan.name.value.upper()} — {plan.price_usd}₽", callback_data=f"admin_edit_price:{plan.id}")]
            for plan in plans
        ]
        keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")])
        text = "<b>💸 Изменение цен</b>\n\nВыберите план для изменения цены:"
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

    async def ask_new_price(self, update, context, data):
        plan_id = int(data.split(":")[1])
        context.user_data["edit_price_plan_id"] = plan_id
        await update.callback_query.edit_message_text("Введите новую цену для этого плана:")

    async def set_new_price(self, update, context):
        plan_id = context.user_data.get("edit_price_plan_id")
        if not plan_id:
            return
        try:
            new_price = float(update.message.text.replace(",", "."))
            plan = await SubscriptionPlanModel.get_or_none(id=plan_id)
            if not plan:
                await update.message.reply_text("План не найден.")
                return
            plan.price_usd = new_price
            await plan.save(update_fields=["price_usd"])
            del context.user_data["edit_price_plan_id"]
            await update.message.reply_text(f"Цена для {plan.name.value.upper()} обновлена: ${new_price}")
        except Exception as e:
            await update.message.reply_text(f"Ошибка: {e}\nВведите корректную цену.")

    async def ask_username_for_subscription(self, update, context):
        context.user_data["admin_add_subscription"] = True
        text = "<b>➕ Добавить подписку</b>\n\nВведите username пользователя (без @):"
        await update.callback_query.edit_message_text(text, parse_mode="HTML")

    async def ask_plan_for_subscription(self, update, context):
        username = update.message.text.strip().lstrip("@")
        context.user_data["admin_add_subscription_username"] = username
        del context.user_data["admin_add_subscription"]
        keyboard = [
            [InlineKeyboardButton(text="PRO", callback_data="admin_add_subscription_plan:pro")],
            [InlineKeyboardButton(text="VIP", callback_data="admin_add_subscription_plan:vip")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")],
        ]
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        text = f"<b>➕ Добавить подписку</b>\n\nВыберите план для @{username}:"
        await update.message.reply_text(text, reply_markup=markup, parse_mode="HTML")

    async def add_subscription_to_user(self, update, context, data):
        plan_name = data.split(":")[1]
        username = context.user_data.get("admin_add_subscription_username")
        if not username:
            await update.callback_query.edit_message_text("Ошибка: username не найден. Начните заново.")
            return
        user = await UserModel.get_or_none(username=username)
        if not user:
            await update.callback_query.edit_message_text("Пользователь не найден.")
            return
        plan = await SubscriptionPlanModel.get_or_none(name=plan_name)
        if not plan:
            await update.callback_query.edit_message_text("План не найден.")
            return
        await activate_subscription_for_user(user.telegram_id, plan.id, payment_id="admin_grant", payment_amount=0)
        del context.user_data["admin_add_subscription_username"]
        await update.callback_query.edit_message_text(f"Пользователю @{username} выдана подписка {plan_name.upper()}.")

    async def ask_username_for_remove_subscription(self, update, context):
        context.user_data["admin_remove_subscription"] = True
        text = "<b>➖ Удалить подписку</b>\n\nВведите username пользователя для удаления подписки (без @):"
        await update.callback_query.edit_message_text(text, parse_mode="HTML")

    async def ask_plan_for_remove_subscription(self, update, context):
        username = update.message.text.strip().lstrip("@")
        context.user_data["admin_remove_subscription_username"] = username
        del context.user_data["admin_remove_subscription"]
        keyboard = [
            [InlineKeyboardButton(text="PRO", callback_data="admin_remove_subscription_plan:pro")],
            [InlineKeyboardButton(text="VIP", callback_data="admin_remove_subscription_plan:vip")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")],
        ]
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        text = f"<b>➖ Удалить подписку</b>\n\nВыберите план для удаления у @{username}:"
        await update.message.reply_text(text, reply_markup=markup, parse_mode="HTML")

    async def remove_subscription_from_user(self, update, context, data):
        plan_name = data.split(":")[1]
        username = context.user_data.get("admin_remove_subscription_username")
        if not username:
            await update.callback_query.edit_message_text("Ошибка: username не найден. Начните заново.")
            return
        user = await UserModel.get_or_none(username=username)
        if not user:
            await update.callback_query.edit_message_text("Пользователь не найден.")
            return
        from app.infrastructure.database.models.subscribe import SubscriptionModel, PlanName
        from datetime import datetime
        # Деактивируем только активную подписку нужного плана
        plan_enum = PlanName[plan_name.upper()]
        active_sub = await SubscriptionModel.filter(user=user, is_active=True, end_date__gte=datetime.now(), plan__name=plan_enum).first()
        if not active_sub:
            await update.callback_query.edit_message_text(f"У пользователя @{username} нет активной подписки {plan_name.upper()}.")
            return
        active_sub.is_active = False
        await active_sub.save(update_fields=["is_active"])
        del context.user_data["admin_remove_subscription_username"]
        await update.callback_query.edit_message_text(f"У пользователя @{username} удалена подписка {plan_name.upper()}.")

    async def ask_username_for_search(self, update, context):
        context.user_data["admin_search_user"] = True
        text = "<b>🔍 Поиск пользователя</b>\n\nВведите username или id пользователя для поиска:"
        await update.callback_query.edit_message_text(text, parse_mode="HTML")

    async def show_user_info(self, update, context):
        query = update.message.text.strip().lstrip("@")
        del context.user_data["admin_search_user"]
        user = await UserModel.get_or_none(username=query) or await UserModel.get_or_none(telegram_id=query)
        if not user:
            await update.message.reply_text("Пользователь не найден.")
            return
        text = (
            f"👤 @{user.username or user.telegram_id}\n"
            f"ID: {user.telegram_id}\n"
            f"Имя: {user.first_name or ''} {user.last_name or ''}\n"
            f"Статус: {'Админ' if user.is_admin else 'Пользователь'}\n"
            f"Подписка: {user.subscription_level.value if user.subscription_level else 'free'}\n"
            f"Создан: {user.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"Обновлён: {user.updated_at.strftime('%d.%m.%Y %H:%M')}"
        )
        await update.message.reply_text(text)

    async def ask_username_for_manage(self, update, context):
        context.user_data["admin_manage_user"] = True
        text = "<b>👤 Управление пользователем</b>\n\nВведите username или id пользователя для управления:"
        await update.callback_query.edit_message_text(text, parse_mode="HTML")

    async def show_manage_user_panel(self, update, context):
        query = update.message.text.strip().lstrip("@")
        del context.user_data["admin_manage_user"]
        user = await UserModel.get_or_none(username=query) or await UserModel.get_or_none(telegram_id=query)
        if not user:
            await update.message.reply_text("Пользователь не найден.")
            return
        from datetime import datetime
        now = datetime.utcnow()
        ban_status = "Забанен до: " + user.banned_until.strftime('%d.%m.%Y %H:%M') if user.banned_until and user.banned_until > now else ("Забанен" if user.is_banned else "Не забанен")
        keyboard = [
            [InlineKeyboardButton(text=("🚫 Забанить" if not user.is_banned else "✅ Разбанить"), callback_data=f"admin_user_action:toggle_ban:{user.telegram_id}")],
            [InlineKeyboardButton(text="⏳ Временный бан (24ч)", callback_data=f"admin_user_action:temp_ban:{user.telegram_id}")],
            [InlineKeyboardButton(text="🔄 Сбросить подписку", callback_data=f"admin_user_action:reset_sub:{user.telegram_id}")],
            [InlineKeyboardButton(text="🕓 История сообщений", callback_data=f"admin_user_action:history:{user.telegram_id}")],
            [InlineKeyboardButton(text="❌ Удалить", callback_data=f"admin_user_action:delete:{user.telegram_id}")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")],
        ]
        markup = InlineKeyboardMarkup(keyboard)
        text = (
            f"<b>👤 Управление пользователем</b>\n\n"
            f"👤 @{user.username or user.telegram_id}\n"
            f"ID: {user.telegram_id}\n"
            f"Имя: {user.first_name or ''} {user.last_name or ''}\n"
            f"Статус: {'Админ' if user.is_admin else 'Пользователь'}\n"
            f"Подписка: {user.subscription_level.value if user.subscription_level else 'free'}\n"
            f"Бан: {ban_status}\n"
        )
        await update.message.reply_text(text, reply_markup=markup, parse_mode="HTML")

    async def handle_user_action(self, update, context, data):
        parts = data.split(":")
        action = parts[1]
        user_id = int(parts[2])
        user = await UserModel.get_or_none(telegram_id=user_id)
        if not user:
            await update.callback_query.edit_message_text("Пользователь не найден.")
            return
        from datetime import datetime, timedelta
        if action == "toggle_admin":
            user.is_admin = not user.is_admin
            await user.save(update_fields=["is_admin"])
            await update.callback_query.edit_message_text(f"Права администратора для @{user.username or user.telegram_id} изменены.")
        elif action == "toggle_ban":
            user.is_banned = not user.is_banned
            if user.is_banned:
                user.banned_until = None
            await user.save(update_fields=["is_banned", "banned_until"])
            await update.callback_query.edit_message_text(f"Статус бана для @{user.username or user.telegram_id} изменён.")
        elif action == "temp_ban":
            user.is_banned = True
            user.banned_until = datetime.utcnow() + timedelta(hours=24)
            await user.save(update_fields=["is_banned", "banned_until"])
            await update.callback_query.edit_message_text(f"Пользователь @{user.username or user.telegram_id} забанен на 24 часа.")
        elif action == "reset_sub":
            from app.infrastructure.database.models.subscribe import SubscriptionModel
            await SubscriptionModel.filter(user=user).update(is_active=False)
            await update.callback_query.edit_message_text(f"У пользователя @{user.username or user.telegram_id} сброшены все подписки.")
        elif action == "history":
            from app.infrastructure.database.models.message import MessageModel
            page = int(context.user_data.get(f"history_page_{user_id}", 0))
            page_size = 10
            offset = page * page_size
            messages = await MessageModel.filter(chat__user=user, is_from_user=True).order_by("-created_at").offset(offset).limit(page_size)
            total = await MessageModel.filter(chat__user=user, is_from_user=True).count()
            if not messages:
                await update.callback_query.edit_message_text("Нет сообщений пользователя.")
                return
            text = f"Последние сообщения пользователя (страница {page+1}):\nВсего сообщений: {total}\n\n"
            for msg in messages:
                dt = msg.created_at.strftime('%d.%m.%Y %H:%M')
                content = msg.content[:50].replace('\n', ' ')
                text += f"[{dt}] {content}\n"
            last_msg = messages[0].created_at.strftime('%d.%m.%Y %H:%M') if messages else '-'
            text += f"\nПоследнее сообщение: {last_msg}"
            keyboard = []
            if offset + page_size < total:
                keyboard.append([InlineKeyboardButton(text="Показать ещё", callback_data=f"admin_user_action:history_more:{user_id}")])
            keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")])
            markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
            await update.callback_query.edit_message_text(text, reply_markup=markup)
        elif action == "history_more":
            page = int(context.user_data.get(f"history_page_{user_id}", 0)) + 1
            context.user_data[f"history_page_{user_id}"] = page
            await self.handle_user_action(update, context, f"admin_user_action:history:{user_id}")
        elif action == "delete":
            await user.delete()
            await update.callback_query.edit_message_text(f"Пользователь @{user.username or user.telegram_id} удалён.") 