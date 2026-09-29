"""JWT (HS256) — создание и проверка access-токенов."""

import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import settings


def create_access_token(sub: str, ttl_min: int | None = None) -> str:
    """
    Создаёт access-токен (HS256).
    sub — идентификатор пользователя (обычно id или email).
    ttl_min — время жизни в минутах (по умолчанию из настроек).
    """
    now = datetime.now(timezone.utc)
    ttl = ttl_min if ttl_min is not None else settings.access_token_ttl_min
    payload = {
        "sub": sub,
        "iat": now,
        "exp": now + timedelta(minutes=ttl),
        "jti": uuid.uuid4().hex,
        "typ": "access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """
    Декодирует и проверяет подпись/срок. При ошибке — ValueError.
    Возвращает payload (dict).
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise ValueError(f"Invalid token: {exc}") from exc

    if payload.get("typ") != "access":
        raise ValueError("Invalid token type")

    return payload