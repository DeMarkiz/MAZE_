from typing import Optional, Dict, Any
from app.infrastructure.redis.redis_client import redis_client
from app.infrastructure.logging.setup_logger import logger


class StateManager:
    """Менеджер состояний пользователей"""
    
    # Определение состояний
    STATES = {
        "IDLE": "idle",
        "WAITING_FOR_USERNAME": "waiting_for_username",
        "WAITING_FOR_PAYMENT": "waiting_for_payment",
        "ADMIN_ADD_SUBSCRIPTION": "admin_add_subscription",
        "ADMIN_REMOVE_SUBSCRIPTION": "admin_remove_subscription",
        "ADMIN_SEARCH_USER": "admin_search_user",
        "ADMIN_MANAGE_USER": "admin_manage_user",
        "ADMIN_EDIT_PRICE": "admin_edit_price",
        "WAITING_FOR_MODE_CHOICE": "waiting_for_mode_choice",
    }

    @staticmethod
    async def set_state(user_id: int, state: str, data: Dict[str, Any] = None, ttl: int = 3600):
        """Установить состояние пользователя"""
        # Преобразуем state к строке, если это Enum
        if hasattr(state, 'value'):
            state = state.value
        await redis_client.set_user_state(user_id, state, data, ttl)
        logger.debug(f"Состояние пользователя {user_id} установлено: {state}")

    @staticmethod
    async def get_state(user_id: int) -> Optional[Dict[str, Any]]:
        """Получить состояние пользователя"""
        return await redis_client.get_user_state(user_id)

    @staticmethod
    async def clear_state(user_id: int):
        """Очистить состояние пользователя"""
        await redis_client.clear_user_state(user_id)
        logger.debug(f"Состояние пользователя {user_id} очищено")

    @staticmethod
    async def is_in_state(user_id: int, state: str) -> bool:
        """Проверить, находится ли пользователь в определенном состоянии"""
        user_state = await redis_client.get_user_state(user_id)
        if user_state and user_state.get("state") == state:
            return True
        return False

    @staticmethod
    async def get_state_data(user_id: int) -> Optional[Dict[str, Any]]:
        """Получить данные состояния пользователя"""
        user_state = await redis_client.get_user_state(user_id)
        if user_state:
            return user_state.get("data", {})
        return None

    @staticmethod
    async def update_state_data(user_id: int, data: Dict[str, Any]):
        """Обновить данные состояния пользователя"""
        user_state = await redis_client.get_user_state(user_id)
        if user_state:
            current_data = user_state.get("data", {})
            current_data.update(data)
            await redis_client.set_user_state(
                user_id, 
                user_state.get("state", "idle"), 
                current_data
            )

    @staticmethod
    async def set_admin_state(user_id: int, admin_state: str, data: Dict[str, Any] = None):
        """Установить состояние админа"""
        await redis_client.set_user_state(user_id, admin_state, data, ttl=1800)  # 30 минут для админских состояний

    @staticmethod
    async def is_admin_in_state(user_id: int, admin_state: str) -> bool:
        """Проверить состояние админа"""
        return await StateManager.is_in_state(user_id, admin_state)

    @staticmethod
    async def clear_admin_state(user_id: int):
        """Очистить состояние админа"""
        await redis_client.clear_user_state(user_id)

    @staticmethod
    async def set_payment_state(user_id: int, payment_data: Dict[str, Any]):
        """Установить состояние ожидания оплаты"""
        await redis_client.set_user_state(
            user_id, 
            StateManager.STATES["WAITING_FOR_PAYMENT"], 
            payment_data, 
            ttl=1800  # 30 минут для оплаты
        )

    @staticmethod
    async def get_payment_state(user_id: int) -> Optional[Dict[str, Any]]:
        """Получить состояние оплаты"""
        if await StateManager.is_in_state(user_id, StateManager.STATES["WAITING_FOR_PAYMENT"]):
            return await StateManager.get_state_data(user_id)
        return None

    @staticmethod
    async def clear_payment_state(user_id: int):
        """Очистить состояние оплаты"""
        if await StateManager.is_in_state(user_id, StateManager.STATES["WAITING_FOR_PAYMENT"]):
            await redis_client.clear_user_state(user_id)

    @staticmethod
    async def set_user_session_data(user_id: int, session_data: Dict[str, Any]):
        """Установить данные сессии пользователя"""
        await redis_client.set_user_session(user_id, session_data)

    @staticmethod
    async def get_user_session_data(user_id: int) -> Optional[Dict[str, Any]]:
        """Получить данные сессии пользователя"""
        return await redis_client.get_user_session(user_id)

    @staticmethod
    async def increment_user_message_count(user_id: int) -> int:
        """Инкремент счетчика сообщений пользователя"""
        key = f"user_messages:{user_id}"
        return await redis_client.increment_counter(key, ttl=86400)  # 24 часа

    @staticmethod
    async def get_user_message_count(user_id: int) -> int:
        """Получить счетчик сообщений пользователя"""
        key = f"user_messages:{user_id}"
        count = await redis_client.get_cache(key)
        return int(count) if count else 0

    @staticmethod
    async def reset_user_message_count(user_id: int):
        """Сбросить счетчик сообщений пользователя"""
        key = f"user_messages:{user_id}"
        await redis_client.delete_cache(key)


# Глобальный экземпляр менеджера состояний
state_manager = StateManager() 