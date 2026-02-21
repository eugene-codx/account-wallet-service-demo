## auth_service overview

### Структура
- `app/api/v1/auth.py`: логин и выдача JWT.
- `app/api/v1/users.py`: регистрация пользователя.
- `app/services/user_service.py`: создание/проверка пользователя, bcrypt.
- `app/core/security.py`: генерация access token.
- `app/models/user.py`: таблица `users`.

### Модель данных
`users`:
- `id` UUID PK
- `username` unique, indexed
- `hashed_password`

### Эндпоинты
- `POST /users/`:
  - вход: `{ "username": "...", "password": "..." }`
  - выход: `{ "id": "...", "username": "..." }`
- `POST /auth/login`:
  - вход: `{ "username": "...", "password": "..." }`
  - выход: `{ "access_token": "...", "token_type": "bearer" }`

### Безопасность
- Пароли хешируются через `bcrypt`.
- JWT создаётся с `sub=<user_id>` и `exp`.
- `JWT_SECRET` и `POSTGRES_PASSWORD` обязательны через env.

### Тестирование
- Основные автотесты находятся во внешнем QA-проекте.
