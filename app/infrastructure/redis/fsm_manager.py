from typing import Optional, Dict, Any, Callable, List
from enum import Enum
from app.interfaces.telegram.services.state_manager import state_manager
from app.infrastructure.logging.setup_logger import logger


class FSMState(Enum):
    """Состояния FSM для нейросети"""
    IDLE = "idle"
    WAITING_FOR_QUESTION = "waiting_for_question"
    WAITING_FOR_CONTEXT = "waiting_for_context"
    WAITING_FOR_MODE_SELECTION = "waiting_for_mode_selection"
    WAITING_FOR_CONFIRMATION = "waiting_for_confirmation"
    PROCESSING_RESPONSE = "processing_response"
    WAITING_FOR_FOLLOW_UP = "waiting_for_follow_up"


class FSMManager:
    """FSM менеджер для нейросети"""
    
    def __init__(self):
        self.transitions: Dict[FSMState, Dict[str, FSMState]] = {
            FSMState.IDLE: {
                "start_conversation": FSMState.WAITING_FOR_QUESTION,
                "select_mode": FSMState.WAITING_FOR_MODE_SELECTION,
            },
            FSMState.WAITING_FOR_QUESTION: {
                "question_received": FSMState.PROCESSING_RESPONSE,
                "need_context": FSMState.WAITING_FOR_CONTEXT,
                "cancel": FSMState.IDLE,
            },
            FSMState.WAITING_FOR_CONTEXT: {
                "context_received": FSMState.PROCESSING_RESPONSE,
                "skip_context": FSMState.PROCESSING_RESPONSE,
                "cancel": FSMState.IDLE,
            },
            FSMState.WAITING_FOR_MODE_SELECTION: {
                "mode_selected": FSMState.WAITING_FOR_QUESTION,
                "cancel": FSMState.IDLE,
            },
            FSMState.PROCESSING_RESPONSE: {
                "response_ready": FSMState.WAITING_FOR_FOLLOW_UP,
                "need_confirmation": FSMState.WAITING_FOR_CONFIRMATION,
                "conversation_end": FSMState.IDLE,
            },
            FSMState.WAITING_FOR_CONFIRMATION: {
                "confirmed": FSMState.WAITING_FOR_FOLLOW_UP,
                "rejected": FSMState.WAITING_FOR_QUESTION,
                "cancel": FSMState.IDLE,
            },
            FSMState.WAITING_FOR_FOLLOW_UP: {
                "follow_up_received": FSMState.PROCESSING_RESPONSE,
                "conversation_end": FSMState.IDLE,
                "new_question": FSMState.WAITING_FOR_QUESTION,
            },
        }
        
        self.state_handlers: Dict[FSMState, Callable] = {}
        self.conversation_data: Dict[int, Dict[str, Any]] = {}

    async def set_user_state(self, user_id: int, state: FSMState, data: Dict[str, Any] = None):
        """Установить состояние пользователя в FSM"""
        # Сохраняем в Redis через state_manager
        await state_manager.set_state(
            user_id, 
            f"fsm_{state.value if isinstance(state, FSMState) else state}", 
            data or {},
            ttl=7200  # 2 часа для FSM состояний
        )
        
        # Сохраняем локально для быстрого доступа
        if user_id not in self.conversation_data:
            self.conversation_data[user_id] = {}
        
        self.conversation_data[user_id]["current_state"] = state
        if data:
            self.conversation_data[user_id].update(data)
            
        logger.debug(f"FSM состояние пользователя {user_id} установлено: {state.value}")

    async def get_user_state(self, user_id: int) -> Optional[FSMState]:
        """Получить текущее состояние пользователя"""
        # Сначала проверяем локальный кэш
        if user_id in self.conversation_data:
            state_name = self.conversation_data[user_id].get("current_state")
            if state_name:
                return state_name
        
        # Если нет в кэше, получаем из Redis
        redis_state = await state_manager.get_state(user_id)
        if redis_state and redis_state.get("state", "").startswith("fsm_"):
            state_value = redis_state.get("state").replace("fsm_", "")
            try:
                state = FSMState(state_value)
                # Обновляем локальный кэш
                if user_id not in self.conversation_data:
                    self.conversation_data[user_id] = {}
                self.conversation_data[user_id]["current_state"] = state
                return state
            except ValueError:
                pass
        
        return FSMState.IDLE

    async def get_user_data(self, user_id: int) -> Dict[str, Any]:
        """Получить данные пользователя"""
        # Сначала проверяем локальный кэш
        if user_id in self.conversation_data:
            return self.conversation_data[user_id].copy()
        
        # Если нет в кэше, получаем из Redis
        redis_state = await state_manager.get_state(user_id)
        if redis_state and redis_state.get("state", "").startswith("fsm_"):
            data = redis_state.get("data", {})
            # Обновляем локальный кэш
            self.conversation_data[user_id] = data.copy()
            return data
        
        return {}

    async def update_user_data(self, user_id: int, data: Dict[str, Any]):
        """Обновить данные пользователя"""
        # Обновляем локальный кэш
        if user_id not in self.conversation_data:
            self.conversation_data[user_id] = {}
        self.conversation_data[user_id].update(data)
        
        # Обновляем в Redis
        current_state = await self.get_user_state(user_id)
        await state_manager.set_state(
            user_id,
            f"fsm_{current_state.value if isinstance(current_state, FSMState) else current_state}",
            self.conversation_data[user_id],
            ttl=7200
        )

    async def transition_to(self, user_id: int, event: str) -> bool:
        """Переход в новое состояние по событию"""
        current_state = await self.get_user_state(user_id)
        
        if current_state not in self.transitions:
            logger.warning(f"Неизвестное состояние FSM: {current_state}")
            return False
        
        if event not in self.transitions[current_state]:
            logger.warning(f"Неизвестное событие '{event}' для состояния {current_state}")
            return False
        
        new_state = self.transitions[current_state][event]
        await self.set_user_state(user_id, new_state)
        
        logger.debug(f"FSM переход пользователя {user_id}: {current_state.value} -> {new_state.value} (событие: {event})")
        return True

    async def can_transition(self, user_id: int, event: str) -> bool:
        """Проверить, возможен ли переход по событию"""
        current_state = await self.get_user_state(user_id)
        
        if current_state not in self.transitions:
            return False
        
        return event in self.transitions[current_state]

    async def get_available_events(self, user_id: int) -> List[str]:
        """Получить список доступных событий для текущего состояния"""
        current_state = await self.get_user_state(user_id)
        
        if current_state not in self.transitions:
            return []
        
        return list(self.transitions[current_state].keys())

    async def reset_user_state(self, user_id: int):
        """Сбросить состояние пользователя"""
        await state_manager.clear_state(user_id)
        
        # Очищаем локальный кэш
        if user_id in self.conversation_data:
            del self.conversation_data[user_id]
        
        logger.debug(f"FSM состояние пользователя {user_id} сброшено")

    async def is_in_conversation(self, user_id: int) -> bool:
        """Проверить, находится ли пользователь в активной беседе"""
        current_state = await self.get_user_state(user_id)
        return current_state != FSMState.IDLE

    async def get_conversation_context(self, user_id: int) -> Dict[str, Any]:
        """Получить контекст беседы пользователя"""
        data = await self.get_user_data(user_id)
        return {
            "state": data.get("current_state", FSMState.IDLE),
            "question": data.get("current_question", ""),
            "context": data.get("context", ""),
            "mode": data.get("selected_mode", "default"),
            "history": data.get("conversation_history", []),
            "last_response": data.get("last_response", ""),
        }

    async def add_to_conversation_history(self, user_id: int, message: str, is_user: bool = True):
        """Добавить сообщение в историю беседы"""
        data = await self.get_user_data(user_id)
        history = data.get("conversation_history", [])
        
        history.append({
            "message": message,
            "is_user": is_user,
            "timestamp": state_manager.redis.time() if state_manager.redis else None
        })
        
        # Ограничиваем историю последними 20 сообщениями
        if len(history) > 20:
            history = history[-20:]
        
        await self.update_user_data(user_id, {"conversation_history": history})

    async def set_conversation_mode(self, user_id: int, mode: str):
        """Установить режим беседы"""
        await self.update_user_data(user_id, {"selected_mode": mode})

    async def get_conversation_mode(self, user_id: int) -> str:
        """Получить режим беседы"""
        data = await self.get_user_data(user_id)
        return data.get("selected_mode", "default")


# Глобальный экземпляр FSM менеджера
fsm_manager = FSMManager() 