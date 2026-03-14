# Используем официальный образ Python
FROM python:3.10-slim

# Запрещаем Python писать файлы .pyc на диск и буферизовать stdout/stderr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Рабочая директория внутри контейнера
WORKDIR /app

# Устанавливаем зависимости системы (нужны для сборки некоторых пакетов)
RUN apt-get update \
    && apt-get install -y gcc libpq-dev \
    && apt-get clean

# Устанавливаем зависимости Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . /app/