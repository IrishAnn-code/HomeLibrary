from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.db_depends import get_db
from app.core.exceptions import not_found, bad_request
from app.schemas.book import BookUpdate, BookCreate
from app.services.book_service import (
    get_all_books,
    get_book_by_id,
    create_book,
    delete_book,
    update_book,
)


router = APIRouter(prefix="/api/books", tags=["Books (API)"])
DBType = Annotated[AsyncSession, Depends(get_db)]


@router.get("/")
async def read_books(db: DBType):
    books = await get_all_books(db)
    if not books:
        not_found("Book was not found")
    return books


@router.get("/{book_id}")
async def get_users_book(db: DBType, book_id: int):
    book = await get_book_by_id(db, book_id)
    if not book:
        not_found("Book was not found")
    return book


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def add_book(db: DBType, create_b: BookCreate, user_id: int, lib_id: int):
    book = await create_book(db, create_b, user_id, lib_id)
    if book is not None:
        return {"status_code": status.HTTP_201_CREATED, "transaction": "Successful"}
    return bad_request("Book was not added")


@router.put("/update/{book_id}")
async def edit_book(db: DBType, user_id: int, book_id: int, book_update: BookUpdate):
    book = await update_book(db, user_id, book_id, book_update)
    if book is None:
        not_found("User or book was not found")
    return {
        "status_code": status.HTTP_200_OK,
        "transaction": "Book update is successful",
    }


@router.delete("/delete/{book_id}")
async def remove_book(db: DBType, book_id: int):
    deleted = await delete_book(db, book_id)
    if not deleted:
        not_found(f"Book: {get_book_by_id(db, book_id)} was not found")
    return {"status": "deleted"}
