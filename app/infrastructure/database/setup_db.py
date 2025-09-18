from app.config import settings

DATABASE_URL: str = \
    f"postgres://{settings.db_user}:{settings.db_pass}@{settings.db_host}:{settings.db_port}/{settings.db_name}"

TORTOISE_ORM = {
    "connections": {"default": DATABASE_URL},
    "apps": {
        "models": {
            "models": [
                "app.infrastructure.database.models.chat",
                "app.infrastructure.database.models.message",
                "app.infrastructure.database.models.user",
                "app.infrastructure.database.models.subscribe",
                "app.infrastructure.database.models.payment",
            ],
            "default_connection": "default",
        },
    },
}