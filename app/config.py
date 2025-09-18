import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Optional

load_dotenv()


class Settings(BaseSettings):
    telegram_bot_token: str
    openai_api_key: str
    webhook_url: str
    FREE_MESSAGE_LIMIT: int = 20

    # Настройки базы данных
    db_host: str = "db"
    db_port: int = 5432
    db_user: str = "postgres"
    db_pass: str = "postgres"
    db_name: str = "neuze_bot"

    # Настройки Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # Настройки YouMoney
    yoomoney_shop_id: str
    yoomoney_secret_key: str
    yoomoney_token: Optional[str] = None

    class Config:
        env_file = ".env"
        # Для регистронезависимых переменных окружения
        case_sensitive = False
        extra = "ignore"


settings = Settings()
