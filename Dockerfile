# Используем официальный образ Python 3.9 (совместим с проектом)
FROM python:3.9-slim

# Рабочая директория внутри контейнера
WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код проекта
COPY . .

# Директория для данных (SQLite + фото) — монтируется как volume
RUN mkdir -p /app/Tables

# Токен передаётся через переменную окружения BOT_TOKEN
ENV BOT_TOKEN=""

# Запуск бота
CMD ["python", "main.py"]