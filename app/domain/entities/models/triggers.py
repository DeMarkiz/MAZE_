from typing import Optional
from dataclasses import dataclass


@dataclass
class Trigger:
    trigger_phrase: str
    system_prompt: str
    temperature: float
    max_tokens: int
    tone: Optional[str] = None
