# auth_service: Architecture and Design Notes

## Назначение

`auth_service` отвечает за:
- регистрацию пользователя;
- проверку логина/пароля;
- выпуск JWT access token для остальных сервисов.

Сервис является stateless и не хранит сессии.

## Контекст в системе

Взаимодействие:
1. Клиент создаёт пользователя (`POST /users/`).
2. Клиент получает access token (`POST /auth/login`).
3. Клиент использует токен в `wallet_service`.

## API контракты

### `POST /users/`
Вход:
- `username`: 3..64, regex `^[A-Za-z0-9_.-]+$`
- `password`: 8..128

Выход:
- `id`
- `username`

Ошибки:
- `400` если username уже существует.

### `POST /auth/login`
Вход:
- `username`
- `password`

Выход:
- `access_token`
- `token_type=bearer`

Ошибки:
- `401 Invalid credentials`.

## Модель данных

Таблица `users`:
- `id UUID` PK
- `username` unique + index
- `hashed_password`

## Безопасность

- Пароль никогда не хранится в открытом виде.
- Хеширование: `bcrypt`.
- Токен содержит `sub=<user_id>` и `exp`.
- Обязательные env-переменные:
  - `POSTGRES_PASSWORD` (min length 8)
  - `JWT_SECRET` (min length 32)

## Конфигурация

Ключевые настройки:
- `POSTGRES_*` для подключения к БД.
- `JWT_SECRET`, `JWT_ALGORITHM`.
- `ACCESS_TOKEN_EXPIRE_MINUTES`.
- `UVICORN_PORT`.

## Транзакционные свойства

- Регистрация пользователя выполняется с проверкой уникальности `username`.
- Гарантия уникальности дополнительно обеспечивается ограничением БД (`unique index`).

## Нефункциональные характеристики

- Async stack: FastAPI + SQLAlchemy AsyncSession.
- Простая горизонтальная масштабируемость (stateless).
- Производительность ограничивается БД и bcrypt cost factor.

## Известные ограничения

- Нет refresh token flow.
- Нет блокировок пользователя после неудачных попыток логина.
- Нет отдельного audit log входов.

## Почему это решение корректное для демо

- Разделение auth и wallet по bounded context.
- Минимально достаточная безопасность для демо:
  - bcrypt;
  - exp в JWT;
  - обязательные секреты через env;
  - валидация входа.
