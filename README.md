# Account Wallet Service (Demo)

Демо-проект: виртуальные кошельки + авторизация.  
Покрыт тестами на `pytest`, идемпотентность, async-обработка.

## Запуск (самый простой способ)

```bash
git clone git@github.com:eugene-codx/account-wallet-service-demo.git
cd account-wallet-service-demo
docker-compose up --build
```

## Сервисы:
### Auth: http://localhost:8001/docs
### Wallet: http://localhost:8000/docs

## Локальная разработка:
```bash
# В корне проекта
pip install poetry

# Установка зависимостей и активация виртуального окружения (в корне проекта)
poetry install --all-extras

# Запуск
uvicorn auth_service.main:app --reload --port 8001
uvicorn wallet_service.main:app --reload --port 8000
```