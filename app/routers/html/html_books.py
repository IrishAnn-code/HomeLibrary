from typing import Annotated

from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db_depends import get_db
from app.schemas.book import BookUpdate, BookCreate
from app.services.book_service import (
    get_all_books,
    get_book_by_id,
    create_book,
    delete_book,
    update_book,
)


router = APIRouter(prefix="/books", tags=["Books (HTML)"])
templates = Jinja2Templates(directory="app/templates")

DBType = Annotated[AsyncSession, Depends(get_db)]


@router.get("/", response_class=HTMLResponse)
async def all_books_page(request: Request, db: DBType):
    books = await get_all_books(db)
    return templates.TemplateResponse(
        "books/list.html", {"request": request, "books": books}
    )


@router.get("/{book_id}", response_class=HTMLResponse)
async def detail_page(request: Request, db: DBType, book_id: int):
    book = await get_book_by_id(db, book_id)
    if not book:
        return templates.TemplateResponse("errors/404.html", {"request": request})
    return templates.TemplateResponse(
        "books/info.html", {"request": request, "book": book}
    )


@router.post("/create", response_class=HTMLResponse)
async def add_book(request: Request, db: DBType, cb: BookCreate):
    book = await create_book(db, cb)
    return templates.TemplateResponse(
        "books/create.html", {"request": request, "book": book}
    )


@router.put("/update", response_class=HTMLResponse)
async def edit_task(
    request: Request, db: DBType, user_id: int, task_id: int, update_b: BookUpdate
):
    book = await update_book(db, user_id, task_id, update_b)
    if not book:
        return templates.TemplateResponse("errors/404.html", {"request": request})
    return templates.TemplateResponse(
        "books/edit.html", {"request": request, "book": book}
    )


@router.get("/delete")
async def delete_index(request: Request):
    """Без указания id задачи"""
    return templates.TemplateResponse(
        "books/delete.html",
        {
            "request": request,
            "title": "Удаление книги",
            "message": "Укажите ID задачи для удаления",
        },
    )


@router.post("/delete/{task_id}", response_class=HTMLResponse)
async def delete_page(request: Request, db: DBType, task_id: int):
    task = await delete_book(db, task_id)
    if not task:
        return templates.TemplateResponse("errors/404.html", {"request": request})
    return templates.TemplateResponse("tasks/delete_id.html", {"request": request})
