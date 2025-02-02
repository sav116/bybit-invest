FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Создаем директорию для данных до копирования кода
RUN mkdir -p /app/data && \
    chmod 777 /app/data

COPY . .

CMD ["python", "bot.py"] 