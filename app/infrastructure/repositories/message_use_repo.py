from app.domain.repositories.message_repositories import IMessageRepository
from app.infrastructure.database.models.chat import ChatModel
from app.infrastructure.database.models.message import MessageModel
from app.infrastructure.logging.setup_logger import logger
from app.domain.entities.models.user import User
from app.domain.entities.models.chat import Chat
from app.domain.entities.models.messages import Message
from datetime import datetime


class MessageUseRepo(IMessageRepository):
    async def get_message_by_chat_id(self, chat: Chat) -> str | None:
        """
        Получить текст последнего сообщения по чату.
        """
        try:
            chat_model = await ChatModel.get_or_none(id=chat.id)
            if not chat_model:
                logger.warning(f'Чат не найден по id: {chat.id}')
                return None

            last_message = await MessageModel.filter(chat=chat_model).order_by('-created_at').first()
            if last_message:
                logger.info(f'Последнее сообщение получено по chat(id): {chat.id}')
                return last_message.content
            else:
                logger.warning(f'Сообщений нет в чате (id): {chat.id}')
                return None
        except Exception as e:
            logger.error(f'Ошибка при получении последнего сообщения по chat(id): {e}', exc_info=True)
            return None

    async def get_history_messages(self, user: User, max_last_messages: int = 10) -> list[Message]:
        """
        Формирует историю диалога в виде списка Message для передачи в OpenAI.
        System prompt добавляется отдельно в use-case с триггерами.
        """
        try:
            history = []

            logger.info(f'Получаем чат для пользователя ID: {user.telegram_id}')
            chat_model = await ChatModel.get_or_none(user_id=user.telegram_id)
            if not chat_model:
                logger.warning(f'Чат не найден для пользователя ID: {user.telegram_id}')
                return history

            chat = Chat(
                id=chat_model.id,
                user=user,
                created_at=chat_model.created_at,
                updated_at=chat_model.updated_at,
                last_message_at=chat_model.last_message_at or datetime.now()
            )

            logger.info(f'Чат {chat.id} найден. Получаем последние {max_last_messages} сообщений.')
            messages = await MessageModel.filter(chat=chat_model).order_by('-created_at').limit(max_last_messages)

            for msg in reversed(messages):  # от старых к новым
                message = Message(
                    id=msg.id,
                    chat=chat,
                    content=msg.content,
                    is_from_user=msg.is_from_user,
                    created_at=msg.created_at,
                    context_summary=msg.context_summary or "",
                    emotion=msg.emotion or "",
                    topic=msg.topic or "",
                    importance=msg.importance or 0,
                    out_of_scope=msg.out_of_scope or False
                )
                history.append(message)
                logger.debug(f"Добавлено сообщение в историю: [{('user' if msg.is_from_user else 'assistant')}] {msg.content[:100]}")

            return history

        except Exception as e:
            logger.error(f'Ошибка при формировании истории диалога: {e}', exc_info=True)
            return []