# Используем официальный образ uv для копирования бинарного файла
FROM python:3.12-slim

# Установка uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Настройка переменных окружения для uv
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Сначала копируем только файлы зависимостей для эффективного кэширования слоев Docker
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости (без установки самого проекта)
# Используем --frozen для строгого соответствия lock-файлу
RUN uv sync --frozen --no-install-project --no-dev

# Копируем остальной код проекта
COPY . .

# Финальная синхронизация проекта
RUN uv sync --frozen --no-dev

# Добавляем виртуальное окружение uv в PATH, чтобы команды (alembic, uvicorn) были доступны напрямую
ENV PATH="/app/.venv/bin:$PATH"

# В данном случае команда запуска переопределяется в docker-compose