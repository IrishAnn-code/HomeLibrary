from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class UserBase(BaseModel):
    """Базовая схема пользователя"""
    username: str = Field(..., min_length=5, max_length=15, description="Уникальное имя пользователя")
    email: EmailStr | None = Field(None, description="Email адрес")


class UserCreate(UserBase):
    """Схема для создания пользователя"""
    password: str = Field(..., min_length=8, max_length=50, description="Пароль")
    firstname: str | None = Field(None, min_length=2, max_length=50, description="Имя")
    lastname: str | None = Field(None, min_length=2, max_length=50, description="Фамилия")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "SecurePass123",
                "firstname": "John",
                "lastname": "Doe"
            }
        }

class UserUpdate(BaseModel):
    """Схема для обновления пользователя"""
    firstname: str | None = Field(None, min_length=2, max_length=50)
    lastname: str | None = Field(None, min_length=2, max_length=50)
    email: EmailStr | None = None
    password: str | None = Field(None, min_length=8, max_length=50)

    class Config:
        json_schema_extra = {
            "example": {
                "firstname": "John",
                "lastname": "Smith",
                "email": "john.smith@example.com"
            }
        }

class UserLogin(BaseModel):
    """Схема для входа в систему"""
    username: str = Field(..., description="Имя пользователя")
    password: str = Field(..., description="Пароль")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "password": "SecurePass123"
            }
        }


class UserOut(UserBase):
    """Схема для возврата пользователя (без пароля)"""
    id: int
    slug: str | None
    firstname: str | None
    lastname: str | None
    tg_id: int | None
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "john_doe",
                "email": "john@example.com",
                "slug": "john-doe",
                "firstname": "John",
                "lastname": "Doe",
                "tg_id": None,
                "created_at": "2024-11-19T14:00:00",
                "updated_at": "2024-11-19T14:00:00"
            }
        }
