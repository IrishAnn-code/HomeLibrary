from pydantic import BaseModel


class BookCreate(BaseModel):
    author: str
    title: str
    description: str = None
    genre: str
    color: str
    read_status: str = "not_read"
    library_id: int
    user_id: int
    lib_address: str  # Из всплывающих окон
    room: str
    shelf: str


class BookUpdate(BaseModel):
    author: str
    title: str
    read_status: str
    lib_address: str  # Из всплывающих окон
    room: str
    shelf: str


class BookOut(BaseModel):
    pass
