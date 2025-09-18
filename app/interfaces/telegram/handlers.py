"""Deprecated PTB handlers stub kept for backward compatibility imports.

This module previously registered python-telegram-bot handlers. After migration
to aiogram, FastAPI uses aiogram webhook. We keep only minimal helpers that are
still referenced (e.g., admin panel callbacks) via aiogram adapters.
"""

from app.interfaces.telegram.services.admin_panel import AdminPanelHandler
from app.interfaces.telegram.services.user_menu import UserMenuHandler
from app.infrastructure.logging.setup_logger import logger

admin_panel = AdminPanelHandler()
user_menu = UserMenuHandler()

async def admin_panel_handler(update, context):
    user = update.effective_user
    if not user:
        return
    await admin_panel.show_main_panel(update, context)

async def admin_text_handler(update, context):
    await admin_panel.handle_text(update, context)

async def error_handler(update: object, context) -> None:
    logger.error("Exception while handling an update:", exc_info=getattr(context, "error", None))