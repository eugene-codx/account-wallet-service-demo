# Account Wallet Service (Demo)

Демо-проект: виртуальные кошельки + авторизация.  
Идемпотентность и async-обработка реализованы в API; автотесты выполняются во внешнем QA-проекте.

## Запуск (самый простой способ)

```bash
git clone git@github.com:eugene-codx/account-wallet-service-demo.git
cd account-wallet-service-demo
docker compose -f infra/docker-compose.yml up -d
# далее поднять сервисы отдельно:
docker compose -f auth_service/docker-compose.yml up --build -d
docker compose -f wallet_service/docker-compose.yml up --build -d
```

## Сервисы:
### Auth: http://localhost:8001/docs
### Wallet: http://localhost:8002/docs

## Локальная разработка:
```bash
# Auth service
cd auth_service
uv sync --frozen
uv run uvicorn app.main:app --reload --port 8001

# Wallet service
cd ../wallet_service
uv sync --frozen
uv run uvicorn app.main:app --reload --port 8002
```
