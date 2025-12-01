from pydantic import BaseModel, Field
from datetime import datetime
from app.models.enum import ReadStatus, GenreStatus
from app.schemas.base import BaseSchema


class BookBase(BaseSchema):
    author: str = Field(..., min_length=1, max_length=200)
    title: str = Field(..., min_length=1, max_length=300)
    description: str | None = Field(None, max_length=2000)
    genre: str | None = Field(None)
    color: str | None = Field(None, pattern="^#[0-9A-Fa-f]{6}$")  # HEX цвет
    read_status: ReadStatus = Field(default=ReadStatus.NOT_READ)
    lib_address: str = Field(..., max_length=100)
    room: str | None = Field(None, max_length=100)
    shelf: str | None = Field(None, max_length=100)
    location: str = Field(..., max_length=100)


class BookCreate(BookBase):
    author: str
    title: str


class BookUpdate(BookBase):
    pass


class BookOut(BaseModel):
    """Схема для возврата книги"""

    id: int
    author: str
    title: str
    description: str | None
    genre: str | None
    color: str | None
    read_status: ReadStatus
    lib_address: str
    room: str
    shelf: str
    location: str
    slug: str
    library_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
