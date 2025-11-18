from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserBase(BaseModel):
    username: str = Field(..., min_length=5, max_length=15)
    email: EmailStr | None = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=5, max_length=15)
    firstname: str
    lastname: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(UserBase):
    id: int
    slug: str

    class Config:
        from_attributes = True
