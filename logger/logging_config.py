import logging
import os
from datetime import datetime
from logging.config import dictConfig

from dotenv import load_dotenv

from logger.custom_formatter import CustomJsonFormatter

load_dotenv()

# Название сервиса вынесено в отдельную переменную.
# Его можно менять напрямую или через переменную окружения.
SERVICE_NAME = os.getenv("SERVICE_NAME", "my_service")

LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)  # Создаёт папку logs, если её нет


class MaskingFilter(logging.Filter):
    """Пример фильтра для маскировки конфиденциальных данных."""

    def __init__(self, fields_to_mask):
        super().__init__()
        self.fields_to_mask = fields_to_mask

    def filter(self, record):
        for field in self.fields_to_mask:
            if hasattr(record, field):
                setattr(record, field, "****")  # Маскируем данные
        return True


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': CustomJsonFormatter,  # Указываем кастомный форматтер
        },
        'console': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
    },
    'filters': {
        'mask_sensitive': {
            '()': MaskingFilter,
            'fields_to_mask': ['hashed_password'],
        },
        # Фильтр теперь использует переменную SERVICE_NAME
        'only_service': {
            '()': 'logging.Filter',
            'name': SERVICE_NAME,
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console',
            'level': 'DEBUG',
        },
        'file': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, f'app_{datetime.now().strftime("%Y-%m-%d")}.log'),
            'when': 'W0',  # Ротация раз в неделю по понедельникам
            'interval': 1,  # Каждую неделю
            'backupCount': 4,  # Хранить 4 недели логов
            'encoding': 'utf-8',
            'level': 'DEBUG',
            'formatter': 'json',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',  # Устанавливаем более высокий уровень, чтобы "шумные" логи не попадали
            'propagate': True,
        },
        'uvicorn.access': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'tortoise.db_client': {
            'handlers': ['file'],
            'level': 'WARNING',  # Подавляем DEBUG для tortoise.db_client
            'propagate': False,
        },
        'aiosqlite': {
            'handlers': ['file'],
            'level': 'WARNING',  # Подавляем DEBUG для aiosqlite
            'propagate': False,
        },
        # Логгер для сервиса теперь определяется через переменную SERVICE_NAME.
        SERVICE_NAME: {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}


def setup_logging(allow_all_logs: bool = False, console_level: str = "DEBUG"):
    """
    Настраивает логирование с возможностью изменения уровня логирования для консоли.

    :param console_level: Уровень логирования для консольного вывода (по умолчанию "DEBUG").
    """
    # Устанавливаем уровень для консольного обработчика
    LOGGING['handlers']['console']['level'] = console_level.upper()

    if not allow_all_logs:
        # Отключаем существующие логгеры, чтобы показывать только нужные логи
        LOGGING['disable_existing_loggers'] = True
    else:
        # Включаем все логи
        LOGGING['disable_existing_loggers'] = False

    # Применяем конфигурацию
    dictConfig(LOGGING)
