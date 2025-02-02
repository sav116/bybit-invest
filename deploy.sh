#!/bin/bash

# Остановка и удаление старого контейнера
docker stop bybit-bot || true
docker rm bybit-bot || true

# Сборка нового образа
docker build -t bybit-bot .

# Запуск нового контейнера
docker run -d \
    --name bybit-bot \
    --restart unless-stopped \
    --env-file .env \
    bybit-bot 