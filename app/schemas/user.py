from fastapi import Form
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(..., min_length=5, max_length=15)
    email: EmailStr | None = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=5, max_length=15)
    firstname: str | None = None
    lastname: str | None = None


class UserUpdate(UserCreate):
    email: str = Field(..., min_length=5, max_length=15)


class UserLogin(BaseModel):
    username: str = Field(..., min_length=5, max_length=15)
    password: str = Field(...)

    @classmethod
    def as_form(
            cls,
            username: str = Form(..., min_length=5, max_length=15),
            password: str = Form(...)
    ):
        return cls(username=username, password=password)

class UserOut(UserBase):
    id: int
    slug: str

    class Config:
        from_attributes = True
