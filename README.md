# Account Wallet Service Demo

Демонстрационный backend-проект на микросервисной архитектуре: отдельный сервис аутентификации (`auth_service`) и отдельный сервис кошельков (`wallet_service`).

Проект показывает практические инженерные решения для финансовых операций:
- JWT-аутентификация между сервисами.
- Денежные операции с блокировками строк в БД (`FOR UPDATE`).
- Идемпотентность операций через уникальный ключ транзакции.
- Контейнеризация и CI/CD через Jenkins + Docker Compose.

## Цели проекта

- Показать продуманный API для регистрации/логина и работы с виртуальными счетами.
- Обеспечить целостность баланса при конкурентных запросах.
- Обеспечить предсказуемое поведение при повторной отправке одного и того же запроса.
- Продемонстрировать базовый production-процесс поставки в DEV/PROD.

## Архитектура

Компоненты:
- `auth_service` (FastAPI): регистрация пользователя, логин, выдача JWT.
- `wallet_service` (FastAPI): счета, пополнение, списание, перевод, история операций.
- `PostgreSQL`: общая инфраструктурная БД (разные БД внутри одного Postgres-инстанса).
- `Jenkins`: pipeline сборки/деплоя.

Поток запроса:
1. Клиент регистрируется/логинится в `auth_service`.
2. `auth_service` выдаёт JWT access token.
3. Клиент вызывает `wallet_service` с `Authorization: Bearer <token>`.
4. `wallet_service` валидирует JWT и выполняет операции от имени `sub` (user_id).

## Технологический стек

- Python 3.12
- FastAPI
- SQLAlchemy (async) + asyncpg
- Alembic
- PostgreSQL 16
- Docker / Docker Compose
- Jenkins Pipeline
- `uv` для управления зависимостями и запуска

## Структура репозитория

```text
account-wallet-service-demo/
├── auth_service/
│   ├── app/
│   ├── migrations/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── auth_service_architecture.md
├── wallet_service/
│   ├── app/
│   ├── migrations/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── wallet_service_architecture.md
├── infra/
│   └── docker-compose.yml
├── Jenkinsfile
└── README.md
```

## Быстрый запуск (Docker Compose)

1. Поднять инфраструктуру PostgreSQL:

```bash
docker compose -f infra/docker-compose.yml up -d
```

2. Поднять `auth_service`:

```bash
docker compose -f auth_service/docker-compose.yml up --build -d
```

3. Поднять `wallet_service`:

```bash
docker compose -f wallet_service/docker-compose.yml up --build -d
```

Swagger:
- Auth: `http://localhost:8001/docs`
- Wallet: `http://localhost:8002/docs`

## Локальный запуск без Docker

```bash
# auth_service
cd auth_service
uv sync --frozen
uv run uvicorn app.main:app --reload --port 8001

# wallet_service
cd ../wallet_service
uv sync --frozen
uv run uvicorn app.main:app --reload --port 8002
```

## Конфигурация (env)

`auth_service` (минимум):
- `POSTGRES_USER`
- `POSTGRES_PASSWORD` (обязательный, min length 8)
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `JWT_SECRET` (обязательный, min length 32)
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `UVICORN_PORT`

`wallet_service` (минимум):
- `POSTGRES_USER`
- `POSTGRES_PASSWORD` (обязательный, min length 8)
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `JWT_SECRET` (обязательный, min length 32)
- `JWT_ALGORITHM`
- `UVICORN_PORT`

Важно:
- `JWT_SECRET` должен быть одинаковым в `auth_service` и `wallet_service`, иначе `wallet_service` не сможет валидировать токены.

## API: демонстрационный сценарий

1. Регистрация:

```bash
curl -X POST http://localhost:8001/users/ \
  -H "Content-Type: application/json" \
  -d '{"username":"demo_user","password":"StrongPass123"}'
```

2. Логин:

```bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo_user","password":"StrongPass123"}'
```

3. Создание счета:

```bash
curl -X POST http://localhost:8002/wallet/accounts \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

4. Пополнение (идемпотентный ключ обязателен):

```bash
curl -X POST http://localhost:8002/wallet/deposit \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id":"<ACCOUNT_ID>",
    "amount":"100.00",
    "idempotency_key":"dep_20260221_0001"
  }'
```

5. Получение истории операций:

```bash
curl -X GET "http://localhost:8002/wallet/accounts/<ACCOUNT_ID>/transactions?limit=20&offset=0" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

## Инженерные решения

### 1) Консистентность денежных операций
- Для изменения баланса используется `SELECT ... FOR UPDATE`.
- Это предотвращает race condition при одновременных списаниях/переводах.

### 2) Идемпотентность
- На `transactions.idempotency_key` установлен `UNIQUE` индекс.
- Повторный запрос с тем же ключом возвращает `409 Transaction already processed`.
- Для переводов используется отдельный внутренний namespace ключей для входящей записи (`__internal__:...`).

### 3) Валидация входных данных
- Ограничены длины и формат `username`, `password`, `idempotency_key`.
- Для истории транзакций ограничены `limit` и `offset`.

### 4) Безопасность
- Пароли хешируются через `bcrypt`.
- JWT имеет `sub` и `exp`.
- Секреты не имеют insecure default'ов в коде.
- Docker-контейнеры сервисов запускаются под non-root пользователем.

## CI/CD (Jenkins)

Pipeline (`Jenkinsfile`) поддерживает:
- Выбор деплоя: `AUTO` / конкретный сервис / `ALL`.
- Выкатку инфраструктуры, затем сервисов в DEV.
- Опциональный запуск внешнего QA job.
- Опциональный деплой в PROD.

Особенности:
- Образы публикуются в `ghcr.io`.
- Для SSH используется `UserKnownHostsFile` + `StrictHostKeyChecking=accept-new`.
- `.env` передаётся на удалённый хост из Jenkins credentials.

## Тестирование

В этом репозитории нет автотестов по договорённости проекта.
Интеграционные и end-to-end проверки запускаются во внешнем QA-репозитории (Jenkins job `Account Wallet AT`).

## Ограничения текущего демо

- Нет refresh-токенов и управления сессиями.
- Нет rate limiting и anti-bruteforce механизма на логине.
- Нет полноценного audit trail (кроме таблицы транзакций).
- Нет observability-стека (метрики/трейсинг).

## Что можно улучшить дальше

- Добавить refresh token flow и ротацию ключей JWT.
- Добавить role/permission модель.
- Добавить contract tests между `auth_service` и `wallet_service`.
- Добавить OpenTelemetry + Prometheus/Grafana.
- Перевести host key политику в Jenkins на pinned known_hosts credential.

## Лицензия

MIT (`LICENSE`).
