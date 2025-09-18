from rapidfuzz import fuzz, process

from app.domain.entities.models.triggers import Trigger
from app.infrastructure.logging.setup_logger import logger


class TriggerMatcher:
    def __init__(self, triggers):
        self.triggers = triggers
        self.trigger_phrases = [t["trigger"] for t in triggers]

    def find_similar_trigger(self, user_input: str, threshold: int = 80, scorer=fuzz.partial_ratio):
        """Находит наиболее подходящий триггер для пользовательского ввода."""
        if not self.trigger_phrases:
            return None

        try:
            match, score, idx = process.extractOne(
                query=user_input.lower(),
                choices=[phrase.lower() for phrase in self.trigger_phrases],
                scorer=scorer
            )
            if score >= threshold:
                return self.triggers[idx]
            return None
        except Exception as e:
            logger.error('Ошибка при поиске триггера:', str(e))
            return None
