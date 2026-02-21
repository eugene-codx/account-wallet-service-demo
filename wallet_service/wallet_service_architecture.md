## wallet_service overview

### Структура
- `app/api/v1/wallet.py`: операции кошелька и история транзакций.
- `app/models/account.py`: таблица `accounts`.
- `app/models/transaction.py`: таблица `transactions`.
- `app/schemas/schemas.py`: контракты API.

### Модель данных
`accounts`:
- `id` UUID PK
- `user_id` UUID index
- `balance` Numeric(18,4)
- `currency`, `created_at`, `updated_at`

`transactions`:
- `id` UUID PK
- `idempotency_key` unique index
- `account_id` FK -> accounts.id
- `amount`, `type`, `created_at`

### Эндпоинты
- `GET /wallet/accounts`
- `POST /wallet/accounts`
- `POST /wallet/deposit`
- `POST /wallet/withdraw`
- `POST /wallet/transfer`
- `GET /wallet/accounts/{account_id}/transactions?limit=20&offset=0`

### Безопасность и консистентность
- Все эндпоинты требуют Bearer JWT.
- `sub` из токена используется как `user_id`.
- Денежные операции используют row lock (`FOR UPDATE`).
- Идемпотентность обеспечивается уникальным индексом + обработкой `IntegrityError`.

### Тестирование
- Основные автотесты находятся во внешнем QA-проекте.
