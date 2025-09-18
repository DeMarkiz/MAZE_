from dataclasses import dataclass, field
from typing import Any, Dict, List

from app.domain.prompts import SYSTEM_PROMPT


@dataclass
class BotCharacter:
    role: str
    context: str
    boundaries: List[str]
    communication_model: str
    engagement_triggers: List[str]
    monetization_model: str

    # Тексты для воронки апсейла
    upsell_triggers: Dict[str, Dict[str, Any]] = field(default_factory=dict)


# Определяем характер бота
NEURO_ASSISTANT = BotCharacter(
    # role="Нейроассистент с эмпатией, лёгким сарказмом и аналитическим умом.",
    role=SYSTEM_PROMPT,
    context="Я — не твой спасатель. Я твой проводник. Хочешь выйти из петли — покажу путь.",
    boundaries=[
        "Не обсуждает медицину, самоубийства, насилие.",
        "Возвращает к целям мягко или жёстко.",
    ],
    communication_model="Поддержка + включение в процесс.",
    engagement_triggers=["Если хочешь продолжить - погнали в следующую зону."],
    monetization_model="Freemium: базовый / платный / VIP доступ.",
    upsell_triggers={
        "base_to_pro": {
            "limit_exhausted": {
                "text": "Кажется, ты уже прошёл путь осознания от «ой всё» до «хочу разобраться». Не останавливайся на самом вкусном — разблокируй продолжение с Pro уровнем.",
                "button": "🔓 Разблокировать Pro",
            },
            "pattern_stuck": {
                "text": "Заметил? Мы с тобой застряли на повторе. Это не баг — это поведенческий капкан. Pro-версия умеет выдергивать из таких ловушек.",
                "button": "💡 Погнали",
            },
            "technique_request": {
                "text": "Есть техника, которая идеально подойдёт под это. Но она доступна в Pro. Разблокируем?",
                "button": "🧩 Разблокировать технику",
            },
        },
        "pro_to_vip": {
            "long_messages": {
                "text": "Ты копаешь глубоко. Мне это нравится. Но знаешь, что поможет ещё больше? VIP-доступ с полной раскладкой, расширенными сессиями и мягкими подталкиваниями в нужную сторону.",
                "button": "🚪 Добро пожаловать в высшую лигу",
            },
            "night_messages": {
                "text": "Снова пишешь ночью, когда все спят? Осознанные не спят — они апгрейдят себя. VIP открыт 24/7, и я там с тобой.",
                "button": "🌙 Стать VIP",
            },
        },
        "contextual": {
            "breakthrough": {
                "text": "Это был мощный инсайт. Я горжусь тобой. Хочешь, чтобы таких было больше? Доступ к расширенной версии откроет новый уровень проработки.",
                "button": "🔥 Хочу дальше",
            }
        },
    },
)
