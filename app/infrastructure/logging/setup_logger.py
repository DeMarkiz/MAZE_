import logging
import sys


def setup_logger(name: str = "my_logger", log_level: int = logging.INFO) -> logging.Logger:
    """Настройка и возврат логгера."""

    # Создаем логгер
    logger = logging.getLogger(name)
    logger.setLevel(log_level)  # Устанавливаем уровень логирования

    # Проверяем, нет ли уже обработчиков (чтобы избежать дублирования)
    if logger.handlers:
        return logger

    # Создаем форматтер
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Добавляем консольный обработчик (вывод в stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# Создаем глобальный логгер (можно импортировать в других модулях)
logger = setup_logger()
