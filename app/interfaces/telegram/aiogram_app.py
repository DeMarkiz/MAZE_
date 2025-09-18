from __future__ import annotations

from typing import Tuple, Dict, Any, Optional

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup as AIOInlineKeyboardMarkup, InlineKeyboardButton as AIOInlineKeyboardButton
from aiogram import Router

from app.config import settings
from app.application.use_cases.start_use_case import StartUseCase
from app.application.use_cases.message_use_case import MessageUseCase
from app.application.use_cases.payment_use_case import PaymentUseCase
from app.application.use_cases.lk_use_case import LkUseCase
from app.infrastructure.repositories.user_use_repositories import UserUseRepositories
from app.infrastructure.repositories.message_use_repo import MessageUseRepo
from app.infrastructure.repositories.subscription_use_repositories import (
    SubscriptionUseRepositories,
)
from app.infrastructure.openai.get_answer_by_gpt_openai import GetAnswerByGPTUseRepo
from app.interfaces.telegram.services.admin_panel import AdminPanelHandler
from app.interfaces.telegram.services.user_menu import UserMenuHandler
from app.infrastructure.logging.setup_logger import logger


class _ReplyMessage:
    """Lightweight wrapper to mimic PTB returned message with id."""

    def __init__(self, message_id: int):
        self.message_id = message_id


class PTBBotAdapter:
    """Adapter exposing minimal PTB-like bot interface used in use cases."""

    def __init__(self, bot: Bot):
        self._bot = bot

    async def edit_message_text(self, text: str, chat_id: int, message_id: int) -> None:
        await self._bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text)

    async def get_me(self):
        me = await self._bot.get_me()
        return me


class PTBContextAdapter:
    """Context shim carrying args, user_data and bot adapter."""

    _user_data_store: Dict[int, Dict[str, Any]] = {}

    def __init__(self, bot: Bot, command_args: Optional[list[str]], user_id: int):
        self.args = command_args or []
        self.user_data = self._user_data_store.setdefault(user_id, {})
        self.bot = PTBBotAdapter(bot)


class _EffectiveChat:
    def __init__(self, chat_id: int):
        self.id = chat_id


class _MessageAdapter:
    """PTB-like message adapter with text and reply_text support."""

    def __init__(self, msg: Message):
        self._msg = msg

    @property
    def text(self) -> Optional[str]:
        return self._msg.text

    @property
    def chat(self):
        return self._msg.chat

    async def reply_text(self, text: str, reply_markup=None, parse_mode: Optional[str] = None):
        sent = await self._msg.answer(text, reply_markup=_convert_reply_markup(reply_markup), parse_mode=parse_mode)
        return _ReplyMessage(sent.message_id)


class _CallbackQueryAdapter:
    def __init__(self, cq: CallbackQuery, bot: Bot):
        self._cq = cq
        self._bot = bot

    @property
    def data(self) -> str:
        return self._cq.data or ""

    async def answer(self, text: Optional[str] = None, show_alert: bool = False):
        await self._cq.answer(text=text, show_alert=show_alert)

    async def edit_message_text(self, text: str, reply_markup=None, parse_mode: Optional[str] = None):
        await self._bot.edit_message_text(
            chat_id=self._cq.message.chat.id,
            message_id=self._cq.message.message_id,
            text=text,
            reply_markup=_convert_reply_markup(reply_markup),
        )

    @property
    def message(self) -> _MessageAdapter:
        return _MessageAdapter(self._cq.message)


class PTBUpdateAdapter:
    """Update shim that exposes attributes/methods used by PTB-based use cases."""

    def __init__(self, message: Optional[Message], callback_query: Optional[CallbackQuery], bot: Bot):
        self._message = message
        self._callback_query = callback_query
        self._bot = bot

    @property
    def effective_chat(self) -> _EffectiveChat:
        chat_id = (
            self._message.chat.id if self._message else self._callback_query.message.chat.id
        )
        return _EffectiveChat(chat_id)

    @property
    def effective_user(self):
        user = self._message.from_user if self._message else self._callback_query.from_user
        return user

    @property
    def message(self):
        return _MessageAdapter(self._message) if self._message else None

    @property
    def callback_query(self):
        return _CallbackQueryAdapter(self._callback_query, self._bot) if self._callback_query else None

    async def reply_text(self, text: str, reply_markup=None, parse_mode: Optional[str] = None):
        sent = await self._message.answer(text, reply_markup=_convert_reply_markup(reply_markup), parse_mode=parse_mode)
        return _ReplyMessage(sent.message_id)


def _convert_reply_markup(markup) -> Optional[AIOInlineKeyboardMarkup]:
    """Convert PTB InlineKeyboardMarkup to aiogram InlineKeyboardMarkup if needed."""
    if markup is None:
        return None
    # Already aiogram markup
    if isinstance(markup, AIOInlineKeyboardMarkup):
        return markup
    # PTB-like markup: try duck typing using .inline_keyboard
    rows = getattr(markup, "inline_keyboard", None)
    if not rows:
        return None
    aio_rows: list[list[AIOInlineKeyboardButton]] = []
    for row in rows:
        aio_row: list[AIOInlineKeyboardButton] = []
        for btn in row:
            text = getattr(btn, "text", "")
            callback_data = getattr(btn, "callback_data", None)
            url = getattr(btn, "url", None)
            if url:
                aio_row.append(AIOInlineKeyboardButton(text=text, url=url))
            else:
                aio_row.append(AIOInlineKeyboardButton(text=text, callback_data=callback_data))
        aio_rows.append(aio_row)
    return AIOInlineKeyboardMarkup(inline_keyboard=aio_rows)


def _build_use_cases():
    """Factory that wires use cases with infrastructure repositories."""
    user_repo = UserUseRepositories()
    message_repo = MessageUseRepo()
    subscription_repo = SubscriptionUseRepositories()
    gpt_repo = GetAnswerByGPTUseRepo()
    return {
        "start": StartUseCase(user_repo),
        "message": MessageUseCase(user_repo, message_repo, subscription_repo, gpt_repo),
        "payment": PaymentUseCase(),
        "lk": LkUseCase(user_repo, subscription_repo),
    }


def register_handlers(router: Router, bot: Bot) -> None:
    """Register aiogram handlers and route into existing PTB-based use cases via adapters."""
    admin_panel = AdminPanelHandler()
    user_menu = UserMenuHandler()
    cases = _build_use_cases()

    @router.message(Command("start"))
    async def on_start(message: Message):
        update = PTBUpdateAdapter(message=message, callback_query=None, bot=bot)
        args = message.text.split()[1:] if message.text else []
        context = PTBContextAdapter(bot, args, message.from_user.id)
        await cases["start"].execute(update, context)
        await user_menu.show_main_menu(update, context)

    @router.message(Command("admin"))
    async def on_admin(message: Message):
        update = PTBUpdateAdapter(message=message, callback_query=None, bot=bot)
        context = PTBContextAdapter(bot, None, message.from_user.id)
        # Проверка прав администратора
        user = await UserUseRepositories().get_user_by_telegram_id(message.from_user.id)
        if not user or not user.is_admin:
            await update.message.reply_text("Доступ запрещён. Только для администраторов.")
            return
        await admin_panel.show_main_panel(update, context)

    @router.message(Command("upgrade"))
    async def on_upgrade(message: Message):
        update = PTBUpdateAdapter(message=message, callback_query=None, bot=bot)
        context = PTBContextAdapter(bot, None, message.from_user.id)
        await cases["payment"].send_payment_link(update, context, "pro")

    @router.message(Command("lk"))
    async def on_lk(message: Message):
        update = PTBUpdateAdapter(message=message, callback_query=None, bot=bot)
        context = PTBContextAdapter(bot, None, message.from_user.id)
        await cases["lk"].execute(update, context)

    @router.callback_query()
    async def on_callback(cq: CallbackQuery):
        update = PTBUpdateAdapter(message=None, callback_query=cq, bot=bot)
        context = PTBContextAdapter(bot, None, cq.from_user.id)
        data = cq.data or ""
        if data.startswith("admin_"):
            await admin_panel.handle_callback(update, context, data)
            return
        if data in ("upgrade_pro", "upgrade_vip"):
            plan_name = "pro" if data == "upgrade_pro" else "vip"
            await cases["payment"].send_payment_link(update, context, plan_name)
            return
        if data.startswith("choose_plan:"):
            plan_name = data.split(":", 1)[1]
            await cases["payment"].send_payment_link(update, context, plan_name)
            return
        if data in ("back_to_lk", "open_lk"):
            await cases["lk"].execute(update, context)
            return
        await user_menu.handle_callback(update, context, data)

    @router.message(F.text & ~F.via_bot)
    async def on_text(message: Message):
        update = PTBUpdateAdapter(message=message, callback_query=None, bot=bot)
        context = PTBContextAdapter(bot, None, message.from_user.id)
        await admin_panel.handle_text(update, context)
        await cases["message"].execute(update, context)


def create_bot_and_dispatcher() -> Tuple[Bot, Dispatcher]:
    """Create aiogram Bot and Dispatcher with registered handlers."""
    bot = Bot(token=settings.telegram_bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    router = Router()
    register_handlers(router, bot)
    dp.include_router(router)
    logger.info("Aiogram dispatcher initialized and handlers registered")
    return bot, dp


