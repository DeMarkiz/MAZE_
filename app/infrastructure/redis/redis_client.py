import redis.asyncio as aioredis
import json
from typing import Optional, Any, Dict
from app.config import settings
from app.infrastructure.logging.setup_logger import logger

def _to_serializable(val):
    # Преобразует Enum в строку, если нужно
    if hasattr(val, 'value'):
        return val.value
    return val

class RedisClient:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self._connection_string = f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
        if settings.redis_password:
            self._connection_string = f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"

    async def connect(self):
        try:
            self.redis = aioredis.from_url(self._connection_string, decode_responses=True)
            await self.redis.ping()
            logger.info(f"[REDIS] Подключено: {self._connection_string}")
        except Exception as e:
            logger.error(f"[REDIS] Ошибка подключения: {e}")
            raise

    async def disconnect(self):
        if self.redis:
            await self.redis.close()
            logger.info("[REDIS] Отключено")

    async def set_user_state(self, user_id: int, state: str, data: Dict[str, Any] = None, ttl: int = 3600):
        if not self.redis:
            return
        key = f"user_state:{user_id}"
        value = {
            "state": _to_serializable(state),
            "data": {k: _to_serializable(v) for k, v in (data or {}).items()},
        }
        try:
            await self.redis.setex(key, ttl, json.dumps(value))
            logger.info(f"[REDIS] SET {key} = {value} (ttl={ttl})")
        except Exception as e:
            logger.error(f"[REDIS] Ошибка SET {key}: {e}")

    async def get_user_state(self, user_id: int) -> Optional[Dict[str, Any]]:
        if not self.redis:
            return None
        key = f"user_state:{user_id}"
        try:
            value = await self.redis.get(key)
            logger.info(f"[REDIS] GET {key} -> {value}")
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"[REDIS] Ошибка GET {key}: {e}")
            return None

    async def clear_user_state(self, user_id: int):
        if not self.redis:
            return
        key = f"user_state:{user_id}"
        try:
            await self.redis.delete(key)
            logger.info(f"[REDIS] DEL {key}")
        except Exception as e:
            logger.error(f"[REDIS] Ошибка DEL {key}: {e}")

    async def set_cache(self, key: str, value: Any, ttl: int = 300):
        if not self.redis:
            return
        try:
            # Гарантируем сериализацию Enum
            if hasattr(value, 'value'):
                value = value.value
            await self.redis.setex(key, ttl, json.dumps(value))
            logger.info(f"[REDIS] SET {key} = {value} (ttl={ttl})")
        except Exception as e:
            logger.error(f"[REDIS] Ошибка SET {key}: {e}")

    async def get_cache(self, key: str) -> Optional[Any]:
        if not self.redis:
            return None
        try:
            value = await self.redis.get(key)
            logger.info(f"[REDIS] GET {key} -> {value}")
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"[REDIS] Ошибка GET {key}: {e}")
            return None

    async def delete_cache(self, key: str):
        if not self.redis:
            return
        try:
            await self.redis.delete(key)
            logger.info(f"[REDIS] DEL {key}")
        except Exception as e:
            logger.error(f"[REDIS] Ошибка DEL {key}: {e}")

    async def increment_counter(self, key: str, ttl: int = 3600) -> int:
        if not self.redis:
            return 0
        try:
            async with self.redis.pipeline() as pipe:
                await pipe.incr(key)
                await pipe.expire(key, ttl)
                result = await pipe.execute()
                logger.info(f"[REDIS] INCR {key} -> {result[0]} (ttl={ttl})")
                return result[0]
        except Exception as e:
            logger.error(f"[REDIS] Ошибка INCR {key}: {e}")
            return 0

    async def set_user_session(self, user_id: int, session_data: Dict[str, Any], ttl: int = 86400):
        if not self.redis:
            return
        key = f"user_session:{user_id}"
        try:
            await self.redis.setex(key, ttl, json.dumps(session_data))
            logger.info(f"[REDIS] SET {key} = {session_data} (ttl={ttl})")
        except Exception as e:
            logger.error(f"[REDIS] Ошибка SET {key}: {e}")

    async def get_user_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        if not self.redis:
            return None
        key = f"user_session:{user_id}"
        try:
            value = await self.redis.get(key)
            logger.info(f"[REDIS] GET {key} -> {value}")
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"[REDIS] Ошибка GET {key}: {e}")
            return None


# Глобальный экземпляр Redis клиента
redis_client = RedisClient() 