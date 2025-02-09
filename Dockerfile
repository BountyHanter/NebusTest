# Используем Python 3.10
FROM python:3.10

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файлы проекта в контейнер
COPY . /app

# Устанавливаем зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r req.txt

# Устанавливаем netcat (nc) для wait-for-db.sh
RUN apt-get update && apt-get install -y netcat-openbsd

# Ожидание базы данных перед запуском сервера
COPY ./docker/wait-for-db.sh /wait-for-db.sh
RUN chmod +x /wait-for-db.sh

EXPOSE 8000

# Указываем команду по умолчанию (запуск сервера)
CMD ["/bin/bash", "-c", "/wait-for-db.sh db 5432 && alembic upgrade head && python test_data.py && uvicorn main:app --host 0.0.0.0 --port 8000"]
