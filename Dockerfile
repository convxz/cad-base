# 1. Берем за основу официальный образ Python (версия 3.10, легкая версия)
FROM python:3.10-slim

# 2. Устанавливаем рабочую папку внутри контейнера
WORKDIR /app

# 3. Запрещаем Питону создавать лишние файлы кэша и просим выводить логи сразу
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 4. Копируем файл с зависимостями внутрь контейнера
COPY requirements.txt .

# 5. Устанавливаем библиотеки
RUN pip install --no-cache-dir -r requirements.txt

# 6. Копируем весь остальной код проекта в контейнер
COPY . .