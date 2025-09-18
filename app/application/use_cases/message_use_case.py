from typing import Any
from datetime import datetime
from app.infrastructure.repositories.user_use_repositories import UserUseRepositories
from app.infrastructure.repositories.message_use_repo import MessageUseRepo
from app.infrastructure.repositories.subscription_use_repositories import SubscriptionUseRepositories
from app.infrastructure.openai.get_answer_by_gpt_openai import GetAnswerByGPTUseRepo
from app.infrastructure.database.models.chat import ChatModel
from app.infrastructure.database.models.message import MessageModel
from app.domain.entities.models.chat import Chat
from app.domain.entities.models.messages import Message
from app.domain.services.subscription_service import SubscriptionService
from app.interfaces.telegram.services.message_sender import MessageSender
from app.application.use_cases.lk_use_case import LkUseCase
from app.infrastructure.redis.fsm_manager import fsm_manager, FSMState
from app.infrastructure.logging.setup_logger import logger
# from app.infrastructure.triggers.trigger_loader import TriggersLoader  # ТРИГГЕРЫ ОТКЛЮЧЕНЫ
# from app.infrastructure.triggers.trigger_matcher import TriggerMatcher  # ТРИГГЕРЫ ОТКЛЮЧЕНЫ
import json
from pathlib import Path


class MessageUseCase:
    def __init__(self, user_repo: UserUseRepositories, message_repo: MessageUseRepo,
                 subscription_repo: SubscriptionUseRepositories, gpt_repo: GetAnswerByGPTUseRepo):
        self.user_repo = user_repo
        self.message_repo = message_repo
        self.subscription_repo = subscription_repo
        self.gpt_repo = gpt_repo
        self.subscription_service = SubscriptionService()
        self.message_sender = MessageSender()

    async def execute(self, update: Any, context: Any) -> None:
        user_id = update.effective_chat.id
        user_text = update.message.text.strip() if update.message and update.message.text else ""

        if not user_text:
            await self.message_sender.send_error(update, "Пожалуйста, отправьте текстовое сообщение")
            return

        if user_text in ("/lk", "📱 Личный кабинет"):
            await LkUseCase(self.user_repo, self.subscription_repo).execute(update, context)
            return

        user = await self.user_repo.get_user_by_telegram_id(user_id)
        if not user:
            await self.message_sender.send_error(update, "Сначала зарегистрируйтесь с помощью команды /start")
            return
        
        # Проверка бана
        now = datetime.utcnow()
        if user.is_banned or (user.banned_until and user.banned_until > now):
            ban_msg = "Вы забанены. Обратитесь к администратору."
            if user.banned_until and user.banned_until > now:
                ban_msg = f"Вы временно забанены до {user.banned_until.strftime('%d.%m.%Y %H:%M')}."
            await self.message_sender.send_error(update, ban_msg)
            return

        # Не реагировать на сообщения админа при работе с админ-панелью
        if user.is_admin and any(flag in context.user_data for flag in [
            "admin_add_subscription", "admin_remove_subscription", "admin_search_user", "admin_manage_user", "edit_price_plan_id"
        ]):
            return

        # Получаем текущее FSM состояние пользователя
        current_fsm_state = await fsm_manager.get_user_state(user_id)
        
        # Обработка в зависимости от FSM состояния
        if current_fsm_state == FSMState.IDLE:
            # Обычная обработка сообщения
            await self._handle_normal_message(update, context, user, user_text)
        else:
            # Обработка в контексте FSM
            await self._handle_fsm_message(update, context, user, user_text, current_fsm_state)

    async def _handle_normal_message(self, update: Any, context: Any, user, user_text: str):
        """Обработка обычного сообщения (без FSM)"""
        # Проверка лимита сообщений для free-пользователей
        if user.subscription_level == "free":
            if user.used_messages >= user.message_limit:
                from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
                bot_username = (await context.bot.get_me()).username
                referral_link = f"https://t.me/{bot_username}?start=ref_{user.telegram_id}"
                text = (
                    "Ваш лимит бесплатных сообщений исчерпан.\n\n"
                    "Вы можете приобрести PRO или пригласить друга и получить +5 сообщений!\n\n"
                    f"<b>Приведи друга и получи +5 сообщений!</b>\n"
                    f"Твоя ссылка: <code>{referral_link}</code>\n"
                    "Скопируйте и отправьте эту ссылку другу, чтобы получить бонус!"
                )
                keyboard = [
                    [InlineKeyboardButton(text="Получить PRO", callback_data="upgrade_pro")]
                ]
                await update.message.reply_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                    parse_mode="HTML"
                )
                return
        plan, message_count = await self.subscription_repo.check_subscription_status_by_user(user)
        trigger = self.subscription_service.get_upsell_trigger(plan, len(user_text), message_count)
        if trigger:
            await self.message_sender.send_upsell_offer(update, context, trigger)
            return

        # --- Поиск и сохранение триггера в FSM ---
        # ТРИГГЕРЫ ОТКЛЮЧЕНЫ
        # triggers_loader = TriggersLoader()
        # matcher = TriggerMatcher(triggers_loader.TRIGGERS)
        # matched_trigger = matcher.find_similar_trigger(user_text)
        # if matched_trigger and matched_trigger.get("id"):
        #     await fsm_manager.update_user_data(user.telegram_id, {"trigger_id": matched_trigger["id"]})
        # else:
        #     await fsm_manager.update_user_data(user.telegram_id, {"trigger_id": None})
        await fsm_manager.update_user_data(user.telegram_id, {"trigger_id": None})
        # --- END ---

        # --- Пример старта сценария по ключевому слову ---
        # СЦЕНАРИИ ОТКЛЮЧЕНЫ
        # SCENARIOS_PATH = Path(__file__).parent.parent.parent / "core" / "triggers" / "scenarios.json"
        # with open(SCENARIOS_PATH, "r", encoding="utf-8") as f:
        #     scenarios = json.load(f)
        # scenario_started = False
        # if "знакомство" in user_text.lower():
        #     scenario = next((s for s in scenarios if s["name"].startswith("Сценарий знакомства")), None)
        #     if scenario:
        #         await fsm_manager.update_user_data(user.telegram_id, {"scenario_id": scenario["id"]})
        #         scenario_started = True
        # elif "мотивация" in user_text.lower():
        #     scenario = next((s for s in scenarios if s["name"].startswith("Сценарий мотивации")), None)
        #     if scenario:
        #         await fsm_manager.update_user_data(user.telegram_id, {"scenario_id": scenario["id"]})
        #         scenario_started = True
        # else:
        #     await fsm_manager.update_user_data(user.telegram_id, {"scenario_id": None})
        # --- END ---

        # Можно добавить вывод шага сценария, если он только что стартовал
        # if scenario_started:
        #     await update.message.reply_text(scenario["steps"][0]["text"])
        #     return
        
        await fsm_manager.update_user_data(user.telegram_id, {"scenario_id": None})

        # Создание или получение Chat
        chat_model, _ = await ChatModel.get_or_create(user_id=user.telegram_id, defaults={'id': user.telegram_id})
        chat = Chat(
            id=chat_model.id,
            user=user,
            created_at=chat_model.created_at,
            updated_at=chat_model.updated_at,
            last_message_at=chat_model.last_message_at or datetime.now()
        )

        # Сохранение сообщения пользователя
        await MessageModel.create(
            chat=chat_model,
            content=user_text,
            is_from_user=True,
            created_at=datetime.now()
        )

        # Получение истории
        history = await self.message_repo.get_history_messages(user=user, max_last_messages=20)
        if not history:
            await self.message_sender.send_error(update, f"Не удалось получить историю сообщений для {user.telegram_id}")
            return

        # Отправка ответа
        thinking_message = await update.message.reply_text("Думаю...")
        response_text = await self.gpt_repo.get_answer_from_get_triggers(history, user.telegram_id) or "Извините, не удалось обработать ваш запрос."
        await MessageModel.create(
            chat=chat_model,
            content=response_text,
            is_from_user=False,
            created_at=datetime.now()
        )

        await context.bot.edit_message_text(
            text=response_text,
            chat_id=user.telegram_id,
            message_id=thinking_message.message_id
        )

        # Увеличиваем used_messages для free-пользователей
        if user.subscription_level == "free":
            user_model = await self.user_repo.get_user_model_by_telegram_id(user.telegram_id)
            if user_model:
                user_model.used_messages = getattr(user_model, 'used_messages', 0) + 1
                await user_model.save(update_fields=["used_messages"])

    async def _handle_fsm_message(self, update: Any, context: Any, user, user_text: str, fsm_state: FSMState):
        """Обработка сообщения в контексте FSM"""
        user_id = user.telegram_id
        
        # Добавляем сообщение в историю FSM
        await fsm_manager.add_to_conversation_history(user_id, user_text, is_user=True)
        
        if fsm_state == FSMState.WAITING_FOR_QUESTION:
            # Пользователь задал вопрос
            await fsm_manager.update_user_data(user_id, {"current_question": user_text})
            await fsm_manager.transition_to(user_id, "question_received")
            
            # Проверяем, нужен ли дополнительный контекст
            if len(user_text) < 10:  # Короткий вопрос
                await fsm_manager.transition_to(user_id, "need_context")
                await update.message.reply_text(
                    "Расскажите больше о вашей ситуации, чтобы я мог дать более точный ответ."
                )
                return
            
            # Обрабатываем вопрос
            await self._process_ai_response(update, context, user, user_text)
            
        elif fsm_state == FSMState.WAITING_FOR_CONTEXT:
            # Пользователь предоставил контекст
            await fsm_manager.update_user_data(user_id, {"context": user_text})
            await fsm_manager.transition_to(user_id, "context_received")
            
            # Объединяем вопрос и контекст
            question = (await fsm_manager.get_user_data(user_id)).get("current_question", "")
            full_question = f"{question}\n\nКонтекст: {user_text}"
            
            await self._process_ai_response(update, context, user, full_question)
            
        elif fsm_state == FSMState.WAITING_FOR_FOLLOW_UP:
            # Пользователь задал уточняющий вопрос
            if user_text.lower() in ["спасибо", "хорошо", "понятно", "ок"]:
                await fsm_manager.transition_to(user_id, "conversation_end")
                await update.message.reply_text("Рад был помочь! Если у вас появятся новые вопросы, обращайтесь.")
            else:
                await fsm_manager.transition_to(user_id, "follow_up_received")
                await self._process_ai_response(update, context, user, user_text)
                
        elif fsm_state == FSMState.WAITING_FOR_CONFIRMATION:
            # Пользователь подтверждает или отклоняет ответ
            if user_text.lower() in ["да", "да", "подтверждаю", "верно"]:
                await fsm_manager.transition_to(user_id, "confirmed")
                await update.message.reply_text("Отлично! Что-то еще?")
            else:
                await fsm_manager.transition_to(user_id, "rejected")
                await update.message.reply_text("Понял, давайте попробуем по-другому. Задайте ваш вопрос:")
                
        else:
            # Неожиданное состояние - сбрасываем в обычный режим
            await fsm_manager.reset_user_state(user_id)
            await self._handle_normal_message(update, context, user, user_text)

    async def _process_ai_response(self, update: Any, context: Any, user, question: str):
        """Обработка ответа ИИ с FSM"""
        user_id = user.telegram_id
        
        # Создание или получение Chat
        chat_model, _ = await ChatModel.get_or_create(user_id=user_id, defaults={'id': user_id})
        
        # Сохранение сообщения пользователя
        await MessageModel.create(
            chat=chat_model,
            content=question,
            is_from_user=True,
            created_at=datetime.now()
        )

        # Получение истории
        history = await self.message_repo.get_history_messages(user=user, max_last_messages=20)
        if not history:
            await self.message_sender.send_error(update, f"Не удалось получить историю сообщений для {user_id}")
            return

        # Отправка ответа
        thinking_message = await update.message.reply_text("Думаю...")
        response_text = await self.gpt_repo.get_answer_from_get_triggers(history, user_id) or "Извините, не удалось обработать ваш запрос."
        
        # Сохраняем ответ
        await MessageModel.create(
            chat=chat_model,
            content=response_text,
            is_from_user=False,
            created_at=datetime.now()
        )

        # Добавляем ответ в историю FSM
        await fsm_manager.add_to_conversation_history(user_id, response_text, is_user=False)
        await fsm_manager.update_user_data(user_id, {"last_response": response_text})
        
        # Переходим в состояние ожидания уточнений
        await fsm_manager.transition_to(user_id, "response_ready")

        await context.bot.edit_message_text(
            text=response_text,
            chat_id=user_id,
            message_id=thinking_message.message_id
        )

    async def start_conversation_mode(self, update: Any, context: Any, user_id: int):
        """Начать режим беседы с FSM"""
        await fsm_manager.set_user_state(user_id, FSMState.WAITING_FOR_QUESTION)
        await update.message.reply_text(
            "Отлично! Теперь я буду вести с вами более структурированную беседу. "
            "Задайте ваш вопрос, и я помогу разобраться в ситуации."
        )

    async def end_conversation_mode(self, update: Any, context: Any, user_id: int):
        """Завершить режим беседы"""
        await fsm_manager.reset_user_state(user_id)
        await update.message.reply_text(
            "Режим беседы завершен. Теперь я буду отвечать в обычном режиме."
        )