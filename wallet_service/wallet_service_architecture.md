# wallet_service: Architecture and Design Notes

## Назначение

`wallet_service` отвечает за операции со счетами пользователя:
- создание и просмотр счетов;
- пополнение;
- списание;
- перевод между счетами;
- история транзакций.

## Контекст в системе

Сервис доверяет JWT от `auth_service`:
- принимает `Bearer` токен;
- декодирует JWT тем же `JWT_SECRET`;
- берёт `sub` как `user_id` для авторизации доступа к счетам.

## API контракты

### `GET /wallet/accounts`
Возвращает список счетов текущего пользователя.

### `POST /wallet/accounts`
Создаёт новый счёт текущего пользователя.

### `POST /wallet/deposit`
Вход:
- `account_id`
- `amount > 0`
- `idempotency_key` (8..128, regex `^[A-Za-z0-9][A-Za-z0-9_.-]{7,127}$`)

### `POST /wallet/withdraw`
Вход аналогичен `deposit`.

Ошибки:
- `400` если недостаточно средств.
- `404` если счёт не принадлежит пользователю/не найден.

### `POST /wallet/transfer`
Вход:
- `from_account_id`
- `to_account_id`
- `amount > 0`
- `idempotency_key`

Ошибки:
- `403` если source account не принадлежит пользователю.
- `404` если один из счетов не найден.
- `400` если недостаточно средств.

### `GET /wallet/accounts/{account_id}/transactions`
Параметры:
- `limit` 1..100
- `offset` 0..10000

## Модель данных

Таблица `accounts`:
- `id UUID` PK
- `user_id UUID` index
- `balance Numeric(18,4)`
- `currency`
- `created_at`, `updated_at`

Таблица `transactions`:
- `id UUID` PK
- `idempotency_key` unique index
- `account_id` FK -> `accounts.id`
- `amount Numeric(18,4)`
- `type` (`DEPOSIT`, `WITHDRAW`, `TRANSFER_OUT`, `TRANSFER_IN`)
- `created_at`

## Консистентность и конкурентность

### Row-level locking
Для денежных операций счёт читается с `FOR UPDATE`, что предотвращает параллельную порчу баланса.

### Идемпотентность
- База данных гарантирует уникальность `idempotency_key`.
- При конфликте уникальности сервис возвращает `409 Transaction already processed`.
- В переводе исходящая и входящая проводки разделены по ключам:
  - клиентский ключ для `TRANSFER_OUT`;
  - внутренний ключ `__internal__:tx:<client_key>:in` для `TRANSFER_IN`.

### Защита от дедлоков
В переводе блокировка обоих счетов происходит в согласованном порядке (`sorted(ids)`).

## Безопасность

- Все endpoint'ы защищены JWT.
- Доступ к операциям проверяется по владельцу счёта (`user_id`).
- Обязательные env-переменные:
  - `POSTGRES_PASSWORD`
  - `JWT_SECRET`

## Нефункциональные характеристики

- Async stack: FastAPI + SQLAlchemy AsyncSession.
- В финансовых операциях приоритет консистентности выше сырой производительности.

## Известные ограничения

- Нет межсервисной валидации отзыва токена.
- Нет внешнего ledger/event store.
- Нет отдельного anti-fraud слоя.

## Почему это решение корректное для демо

- Реализованы базовые, но правильные для wallet-домена гарантии:
  - авторизация по владельцу;
  - row locks;
  - идемпотентность;
  - обработка конкурентных дублей на уровне БД.
