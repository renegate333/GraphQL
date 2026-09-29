"""Контекст GraphQL-запроса: db-сессия + текущий пользователь."""

from app.core.jwt import decode_token
from app.db.session import SessionLocal
from app.models import User


def _get_header(request, name: str):
    """Достаёт заголовок из request или ASGI-scope."""
    headers = getattr(request, "headers", None)
    if headers is not None and hasattr(headers, "get"):
        value = headers.get(name)
        if value:
            return value

    scope = request if isinstance(request, dict) else getattr(request, "scope", None)
    if isinstance(scope, dict):
        raw_headers = scope.get("headers") or []
        name_bytes = name.lower().encode()
        for key, value in raw_headers:
            if key.lower() == name_bytes:
                return value.decode()

    return None


async def get_context_value(request, data):
    """Ariadne вызывает это для каждого запроса."""
    db = SessionLocal()
    user = None

    auth = _get_header(request, "authorization")

    if auth and auth.startswith("Bearer "):
        token = auth.removeprefix("Bearer ").strip()
        try:
            payload = decode_token(token)
            sub = payload.get("sub")
            if sub and sub.isdigit():
                user = db.get(User, int(sub))
            elif sub:
                user = db.query(User).filter(User.email == sub).first()
            if user and not user.is_active:
                user = None
        except ValueError:
            user = None

    return {"request": request, "db": db, "user": user}