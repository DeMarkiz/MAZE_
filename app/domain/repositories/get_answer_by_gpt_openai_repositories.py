from abc import ABC, abstractmethod

class GetAnswerByGptOpenai(ABC):

    @abstractmethod
    def get_answer_from_get_triggers(self, history: list) -> str:
        """
        Получает ответ от модели ChatGPT с учетом найденного триггера или дефолтного SYSTEM_PROMPT.
        """
        raise NotImplementedError("При наследовании необходимо реализовать это метод")