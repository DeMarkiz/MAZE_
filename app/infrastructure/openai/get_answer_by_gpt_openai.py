from pathlib import Path

from openai import AsyncOpenAI

from app.config import settings
from app.domain.prompts import SYSTEM_PROMPT, DEFAULT_SETTINGS, SOFT_PROMPT, HARD_PROMPT, BRIEF_PROMPT, LONG_PROMPT
from app.domain.repositories.get_answer_by_gpt_openai_repositories import GetAnswerByGptOpenai
from app.infrastructure.logging.setup_logger import logger

import json
from app.infrastructure.redis.fsm_manager import fsm_manager

# Для загрузки триггеров
# from app.infrastructure.triggers.trigger_loader import TriggersLoader  # ТРИГГЕРЫ ОТКЛЮЧЕНЫ

# Для загрузки сценариев
# SCENARIOS_PATH = Path(__file__).parent.parent.parent / "core" / "triggers" / "scenarios.json"  # СЦЕНАРИИ ОТКЛЮЧЕНЫ
# def load_scenarios():  # СЦЕНАРИИ ОТКЛЮЧЕНЫ
#     with open(SCENARIOS_PATH, "r", encoding="utf-8") as f:  # СЦЕНАРИИ ОТКЛЮЧЕНЫ
#         return json.load(f)  # СЦЕНАРИИ ОТКЛЮЧЕНЫ

# --- Новый блок: автодетект режима и типа ответа ---
def detect_mode_and_reply_type(user_text: str) -> tuple[str, str]:
    hard_keywords = [
        "кричит", "запрещает", "унижает", "обесценивает",
        "игнорирует", "молчание", "терплю", "угрожает",
        "он сказал что без него я никто", "он давит", "он контролирует",
        "я сама виновата", "это я всё накрутила", "я прошу слишком много"
    ]
    # Анализ на HARD/soft
    for kw in hard_keywords:
        if kw in user_text.lower():
            mode = "hard"
            break
    else:
        mode = "soft"
    # Анализ на brief/long
    text_len = len(user_text.strip())
    is_caps = user_text.isupper() and text_len > 5
    is_brief = text_len < 20 or user_text.count("!") > 2 or is_caps
    reply_type = "brief" if is_brief else "long"
    return mode, reply_type

class GetAnswerByGPTUseRepo(GetAnswerByGptOpenai):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        # self.triggers_loader = TriggersLoader()  # ТРИГГЕРЫ ОТКЛЮЧЕНЫ
        # self.scenarios = load_scenarios()  # СЦЕНАРИИ ОТКЛЮЧЕНЫ

    async def get_answer_from_get_triggers(self, history: list, user_id: int = None) -> str:
        try:
            openai_history = []
            for msg in history:
                role = "user" if msg.is_from_user else "assistant"
                openai_history.append({"role": role, "content": msg.content})
            user_message = next((msg.content for msg in reversed(history) if msg.is_from_user), "")

            # --- Динамические system prompts ---
            system_prompts = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "system", "content": "ЛОГИКА ОПРЕДЕЛЕНИЯ РЕЖИМА:\n\n1. По умолчанию используй мягкий режим (SOFT).\n2. Если текст пользователя содержит следующие слова или фразы:\n  - 'кричит', 'запрещает', 'унижает', 'обесценивает',\n  - 'игнорирует', 'молчание', 'терплю', 'угрожает',\n  - 'он сказал что без него я никто', 'он давит', 'он контролирует',\n  то переключайся на жёсткий режим (HARD).\n3. Если в тексте есть фразы:\n  - 'я сама виновата', 'это я всё накрутила', 'я прошу слишком много',\n  то включай жёсткий режим (HARD) с мягким рефреймингом."},
            ]
            mode, reply_type = detect_mode_and_reply_type(user_message)
            if mode == "hard":
                system_prompts.append({"role": "system", "content": HARD_PROMPT})
            else:
                system_prompts.append({"role": "system", "content": SOFT_PROMPT})
            if reply_type == "brief":
                system_prompts.append({"role": "system", "content": BRIEF_PROMPT})
            else:
                system_prompts.append({"role": "system", "content": LONG_PROMPT})

            openai_history = [msg for msg in openai_history if msg["role"] != "system"]
            messages = system_prompts + openai_history

            temperature = DEFAULT_SETTINGS["temperature"]
            max_tokens = DEFAULT_SETTINGS["max_tokens"]
            response = await self.client.chat.completions.create(
                model=DEFAULT_SETTINGS["model"],
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Ошибка при получении ответа от GPT: {e}")
            return None
