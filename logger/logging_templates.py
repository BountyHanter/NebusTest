import logging
import json
import os

from dotenv import load_dotenv

load_dotenv()

# Название сервиса вынесено в отдельную переменную.
# Его можно менять напрямую или через переменную окружения.
SERVICE_NAME = os.getenv("SERVICE_NAME", "my_service")

logger = logging.getLogger(SERVICE_NAME)


def log_debug(action: str, message: str, **kwargs):
    serialized_data = json.dumps(kwargs, ensure_ascii=False) if kwargs else ""
    logger.debug(f"[DEBUG] {action} - {message} - {serialized_data}")


def log_info(action: str, message: str, **kwargs):
    serialized_data = json.dumps(kwargs, ensure_ascii=False) if kwargs else ""
    logger.info(f"[SUCCESS] {action} - {message} - {serialized_data}")


def log_warning(action: str, message: str, **kwargs):
    serialized_data = json.dumps(kwargs, ensure_ascii=False) if kwargs else ""
    logger.warning(f"[WARNING] {action} - {message} - {serialized_data}")


def log_error(action: str, message: str, exc_info=False, **kwargs):
    serialized_data = json.dumps(kwargs, ensure_ascii=False) if kwargs else ""
    logger.error(f"[ERROR] {action} - {message} - {serialized_data}", exc_info=exc_info)
