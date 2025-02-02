#!/bin/bash

# Остановка и удаление старого контейнера
docker stop bybit-bot || true
docker rm bybit-bot || true

# Сборка нового образа
docker build -t bybit-bot .

# Создаем директорию для данных, если её нет
mkdir -p /opt/bybit-bot/data

# Запуск нового контейнера
docker run -d \
    --name bybit-bot \
    --restart unless-stopped \
    --env-file .env \
    -v /opt/bybit-bot/data:/app/data \
    bybit-bot 