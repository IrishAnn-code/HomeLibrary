from pydantic import BaseModel, Field
from datetime import datetime

from app.schemas.book import BookOut


class LibraryBase(BaseModel):
    """Базовая схема библиотеки"""
    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Название библиотеки",
        examples=["Домашняя библиотека"],
    )


class LibraryCreate(LibraryBase):
    """Схема для создания библиотеки"""
    password: str | None = Field(
        None,
        min_length=4,
        max_length=50,
        description="Пароль для доступа (если библиотека приватная)",
        examples=["secret123"],
    )

    class Config:
        json_schema_extra = {
            "example": {"name": "Семейная библиотека", "password": "secret123"}
        }


class LibraryJoin(BaseModel):
    """Схема для присоединения к библиотеке"""

    library_id_or_name: str = Field(
        ..., description="ID или название библиотеки", examples=["1"]
    )
    password: str | None = Field(
        None, description="Пароль (если библиотека приватная)", examples=["secret123"]
    )


class LibraryOut(LibraryBase):
    """Схема для возврата библиотеки"""

    id: int
    slug: str
    owner_id: int | None
    created_at: datetime
    is_private: bool = Field(description="Требуется ли пароль для входа")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Домашняя библиотека",
                "slug": "domashniaia-biblioteka",
                "owner_id": 1,
                "created_at": "2024-10-22T15:30:00",
                "is_private": True,
            }
        }


class LibraryWithBooks(LibraryOut):
    """Библиотека со списком книг"""

    books: list["BookOut"] = []  # Forward reference

    class Config:
        from_attributes = True


class LibraryUpdate(BaseModel):
    """Схема для обновления библиотеки"""

    name: str | None = Field(None, min_length=3, max_length=100)
    password: str | None = Field(None, min_length=4, max_length=50)
