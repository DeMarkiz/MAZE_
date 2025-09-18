import json
from pathlib import Path
from typing import List, Dict


class TriggersLoader:
    def __init__(self):
        self.TRIGGERS: List[Dict] = []
        self.TRIGGER_PHRASES: List[str] = []
        self._load_triggers()

    def _load_triggers(self) -> None:
        """Загружает триггеры из JSON файла"""
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent.parent.parent
        triggers_path = project_root / "app" / "core" / "triggers" / "prompts_neuromaze_1000_linked.json"

        with open(triggers_path, "r", encoding="utf-8") as f:
            self.TRIGGERS = json.load(f)

        self.TRIGGER_PHRASES = [trigger["trigger"] for trigger in self.TRIGGERS]
