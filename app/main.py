import asyncio
import json
import logging

from fastapi import FastAPI, HTTPException, Request
from tortoise.contrib.fastapi import register_tortoise
from aiogram.types import BotCommand as AIOBotCommand, Update as AiogramUpdate

from app.infrastructure.database.setup_db import TORTOISE_ORM
from app.config import settings
from app.infrastructure.database.models.subscribe import SubscriptionPlanModel
from app.interfaces.youmoney_webhooks import router as yoomoney_router
from app.infrastructure.redis.redis_client import redis_client
from app.interfaces.telegram.aiogram_app import create_bot_and_dispatcher


# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

app = FastAPI()
app.include_router(yoomoney_router, prefix="/webhook", tags=["yoomoney"])

# Регистрация Tortoise ORM
register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=True,
    add_exception_handlers=True,
)

# Инициализация aiogram бота
aiogram_bot, aiogram_dp = create_bot_and_dispatcher()


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    try:
        # Подключение к Redis
        await redis_client.connect()
        
        # Устанавливаем webhook для aiogram

        # Установка меню команд для aiogram
        await aiogram_bot.set_my_commands(
            [
                AIOBotCommand(command="start", description="🚀 Начать/Перезапустить диалог"),
                AIOBotCommand(command="upgrade", description="💎 Улучшить подписку"),
                AIOBotCommand(command="lk", description="📱 Личный кабинет"),
            ]
        )

        # Создание планов подписки
        await SubscriptionPlanModel.get_or_create(
            id=1,
            name="pro",
            defaults={
                "description": "Полный доступ ко всем функциям бота на 30 дней.",
                "price_usd": 10.00,
                "duration_days": 30,
                "is_active": True,
            },
        )
        await SubscriptionPlanModel.get_or_create(
            id=2,
            name="vip",
            defaults={
                "description": "VIP-доступ с расширенными сессиями и персональными подталкиваниями.",
                "price_usd": 50.00,
                "duration_days": 30,
                "is_active": True,
            },
        )

        # Гарантируем наличие главного админа
        from app.infrastructure.repositories.user_use_repositories import UserUseRepositories
        user_repo = UserUseRepositories()
        await user_repo.add_admin(426391848)

        # Ждем, пока база данных будет готова
        for _ in range(30):  # 30 попыток
            try:
                # Устанавливаем новый webhook на FastAPI маршрут
                webhook_url = f"{settings.webhook_url}/bot/webhook"
                logger.info(f"Setting aiogram webhook to: {webhook_url}")
                await aiogram_bot.delete_webhook(drop_pending_updates=True)
                await aiogram_bot.set_webhook(url=webhook_url)
                break
            except Exception as e:
                logger.warning(f"Waiting for database... {str(e)}")
                await asyncio.sleep(1)
        else:
            raise Exception("Could not connect to database")
            
        logger.info("Приложение запущено успешно")
    except Exception as e:
        logger.error(f"Ошибка при запуске приложения: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при остановке"""
    try:
        await aiogram_bot.delete_webhook(drop_pending_updates=False)
        await redis_client.disconnect()
        logger.info("Приложение остановлено")
    except Exception as e:
        logger.error(f"Ошибка при остановке приложения: {e}")


@app.post("/bot/webhook")
async def webhook(request: Request) -> dict:
    try:
        # Aiogram webhook handler
        body = await request.json()
        logger.info(f"Received webhook data: {json.dumps(body)}")
        update = AiogramUpdate.model_validate(body)
        await aiogram_dp.feed_update(aiogram_bot, update)
        return {"status": "ok"}
    except Exception as e:
        logger.exception(f"Error in webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}
