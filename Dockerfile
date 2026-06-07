FROM python:3.11-slim

# Устанавливаем зависимости для работы бинарника Bot API (он может требовать библиотеки)
RUN apt-get update && apt-get install -y \
    libssl-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Даем права на выполнение бинарнику и скрипту
RUN chmod +x telegram-bot-api start.sh

# По умолчанию запускаем бота, но переопределим это в compose
CMD ["python", "main.py"]
