# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List
import os


class Settings(BaseSettings):
    """Настройки приложения из переменных окружения"""
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./homelibrary.db",
        description="URL подключения к базе данных"
    )
    
    # Security
    SECRET_KEY: str = Field(
        ...,  # Обязательное поле
        min_length=32,
        description="Секретный ключ для JWT"
    )
    ALGORITHM: str = Field(
        default="HS256",
        description="Алгоритм шифрования JWT"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=10080,  # 7 дней
        description="Время жизни токена в минутах"
    )
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Разрешенные источники для CORS"
    )
    
    # App
    APP_NAME: str = Field(
        default="HomeLibrary",
        description="Название приложения"
    )
    DEBUG: bool = Field(
        default=False,
        description="Режим отладки"
    )
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str | None = Field(
        default=None,
        description="Токен Telegram бота"
    )
    TELEGRAM_ADMIN_ID: int | None = Field(
        default=None,
        description="ID администратора в Telegram"
    )
    
    # Настройки Pydantic
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Игнорировать лишние переменные
    )


# Создаем singleton
settings = Settings()


# Для отладки (можно удалить потом)
if __name__ == "__main__":
    print("🔧 Текущие настройки:")
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    print(f"SECRET_KEY: {settings.SECRET_KEY[:10]}...")
    print(f"DEBUG: {settings.DEBUG}")
    print(f"ALLOWED_ORIGINS: {settings.ALLOWED_ORIGINS}")