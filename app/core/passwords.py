from argon2 import PasswordHasher, exceptions as argon2_exceptions
from zxcvbn import zxcvbn
from app.config import settings

class WeakPasswordError(ValueError):
    """Пароль не прошёл политику безопасности."""
    pass

# Параметры по рекомендациям OWASP для Argon2id
_hasher = PasswordHasher(
    time_cost=3,        # iterations
    memory_cost=65536,  # 64 MiB
    parallelism=4,
    hash_len=32,
    salt_len=16,
)

def hash_password(password: str) -> str:
    """Возвращает Argon2id-хэш от password + pepper."""
    return _hasher.hash(password + settings.password_pepper)

def verify_password(password: str, hashed: str) -> bool:
    """Проверяет соответствие пароля хэшу. False при любой ошибке."""
    try:
        _hasher.verify(hashed, password + settings.password_pepper)
        return True
    except argon2_exceptions.VerifyMismatchError:
        return False
    except argon2_exceptions.VerificationError:
        return False
    except Exception:
        return False

def validate_policy(password: str, user_inputs: list[str] | None = None) -> None:
    """
    Проверяет пароль на соответствие политике.
    Бросает WeakPasswordError с понятным сообщением, если не прошёл.
    """
    if len(password) < settings.password_min_length:
        raise WeakPasswordError(
            f"Пароль должен быть не короче {settings.password_min_length} символов"
        )

    result = zxcvbn(password, user_inputs=user_inputs or [])
    if result["score"] < 3:
        raise WeakPasswordError(
            "Пароль слишком слабый. Попробуйте добавить больше символов, "
            "избегайте словарных слов и простых паттернов"
        )