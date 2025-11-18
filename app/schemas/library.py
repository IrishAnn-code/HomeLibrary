from pydantic import BaseModel


class LibraryCreate(BaseModel):
    name: str
    password: str | None = None


class LibraryJoin(BaseModel):
    password: str | None = None
