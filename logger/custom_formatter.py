import logging
import json


class CustomJsonFormatter(logging.Formatter):
    def format(self, record):
        # Получаем стандартные поля
        log_record = {
            "time": self.formatTime(record),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
            "filename": record.filename,
            "lineno": record.lineno,
            "funcName": record.funcName,
            "module": record.module,
        }

        # Добавляем данные из extra и сериализуем их
        if hasattr(record, "__dict__"):
            extra = {key: self._serialize(value) for key, value in record.__dict__.items()
                     if key not in log_record}
            log_record.update(extra)

        return json.dumps(log_record, ensure_ascii=False)

    @staticmethod
    def _serialize(value):
        try:
            json.dumps(value)  # Проверяем, можно ли сериализовать значение
            return value
        except (TypeError, ValueError):
            return str(value)  # Преобразуем несериализуемые объекты в строку
