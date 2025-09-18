from app.domain.repositories.chat_repositories import IChatRepository
from app.infrastructure.database.models.chat import ChatModel
from app.infrastructure.database.models.user import UserModel
from app.infrastructure.logging.setup_logger import logger


class ChatUseRepo(IChatRepository):

    async def get_time_last_message_by_chat_on_user(self, user: UserModel) -> object | int:
        '''Получение времени последнего сообщения для чата(Пользователя)'''
        try:

            find = await ChatModel.get_or_none(user=user)
            logger.info(f'Получение времени последнего сообщения для чата(Пользователя) -> {find}')

            if find:
                logger.info(f'Чат найден -> {find}')
                if find.last_message_at:
                    logger.info(f'Возвращаем время последнего сообщения -> {find.last_message_at}')
                    return find.last_message_at
                else:
                    logger.warning(f'Время не найдено возвращаем "0" -> {find.last_message_at}')
                    logger.warning(f'Возвращаем "0"')
                    return 0

        except Exception as e:
            logger.error(f'Ошибка при получении времени последнего сообщения -> {e}')