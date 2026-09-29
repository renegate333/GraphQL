from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- строка подключения к БД ---
    database_url: str  # обязательно, без дефолта

    # --- секрет для подписи JWT ---
    jwt_secret: str  # обязательно
    jwt_algorithm: str = "HS256"
    access_token_ttl_min: int = 60

    # --- пароли ---
    password_pepper: str  # глобальный «перец» для паролей
    password_min_length: int = 12 # минимальная длина пароля

    # --- служебные поля ---
    environment: str = "development"
    app_name: str = "Vault"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

settings = Settings()