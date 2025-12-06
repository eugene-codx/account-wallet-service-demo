## Общая структура каталогов
```tree
auth-service/
 ├── app/
 │    ├── api/v1/
 │    │    ├── auth.py
 │    │    └── users.py
 │    ├── core/
 │    │    ├── config.py
 │    │    └── security.py
 │    ├── db/
 │    │    └── database.py
 │    ├── models/
 │    │    └── user.py
 │    ├── schemas/
 │    │    ├── auth.py
 │    │    └── user.py
 │    ├── services/
 │    │    ├── user_service.py
 │    │    └── auth_service.py
 │    └── main.py
 ├── migrations/
 │    ├── versions/
 │    └── env.py
 ├── .env
 ├── alembic.ini
 ├── auth_service_architecture.md
 ├── docker-compose.yml
 ├── Dockerfile
 └── requirements.txt

```

## Модель данных (wallets + transactions)
Таблица wallets и таблица transactions.
```text
wallets:
id
user_id
balance (decimal, 2 digits)
created_at

transactions:
id
wallet_id
amount (положительное или отрицательное)
type ("deposit", "withdraw")
created_at

Баланс в кошельке всегда = сумма всех транзакций.
```

## Основные эндпоинты (v1/wallet):
```text
POST /wallet/create
Создать кошелёк для текущего пользователя

Вход: пусто
Выход: wallet_id
```
```text
POST /wallet/deposit
Пополнение

Вход:
{
  "wallet_id": "...",
  "amount": 100.0
}
Выход: новое значение баланса
```
```text
POST /wallet/withdraw
Списание

Логика: проверка достаточности средств
Выход: новое значение баланса
```
```text
GET /wallet/{wallet_id}/balance
Получить текущий баланс
```
```text
GET /wallet/{wallet_id}/transactions
История операций (paging по желанию)
```

## Авторизация
- Все эндпоинты требуют JWT access token.
- Токен проверяется через тот же механизм FastAPI middleware, который используется в вашем Awakeia auth-сервисе.
- user_id извлекается из токена и передается в бизнес-логику.

## Бизнес-логика (service layer)
### Слой services/wallet_service.py:
- create_wallet(user_id)
- deposit(wallet_id, amount)
- withdraw(wallet_id, amount)
- get_balance(wallet_id)
- get_transactions(wallet_id)
---
### Особенности:
- Запрет создания двух кошельков на одного пользователя, либо разрешение, но осознанное.
- Каждая операция — транзакция в БД (+ оптимистичная блокировка при списании).

## Автоматические тесты
- автотесты на pytest находятся в другом проекте (отдельный framework для интеграционных тестов с auth-сервисом).

## Описание для README
### Структура:
- описание сервиса
- как запустить (docker-compose или вручную)
- пример запросов
- пример тестов
- архитектура