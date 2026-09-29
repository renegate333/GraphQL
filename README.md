\# Vault — GraphQL-сервис управления пользователями и OAuth-клиентами



Лабораторная работа №2 по Python. Костяк backend-сервиса на FastAPI + Ariadne.



\## Стек



\- \*\*FastAPI\*\* — асинхронный веб-фреймворк

\- \*\*Ariadne\*\* — schema-first GraphQL для Python

\- \*\*SQLAlchemy 2.x\*\* — ORM

\- \*\*Alembic\*\* — миграции БД

\- \*\*Argon2id\*\* — хэширование паролей (+ pepper, + zxcvbn)

\- \*\*python-jose\*\* — JWT (HS256)

\- \*\*pydantic-settings\*\* — конфигурация через `.env`

\- \*\*SQLite\*\* — БД по умолчанию



\## Установка



```bash

git clone <repo-url>

cd lab2\_vault

python -m venv .venv

.venv\\Scripts\\activate      # Windows

\# source .venv/bin/activate  # Linux/macOS

pip install -r requirements.txt

