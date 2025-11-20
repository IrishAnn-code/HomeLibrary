from typing import Annotated

from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.auth import get_current_user
from app.database.db_depends import get_db
from app.models import User
from app.schemas.book import BookUpdate, BookCreate
from app.services.book_service import (
    get_all_books,
    get_book_by_id,
    create_book,
    delete_book,
    update_book,
)
from app.services.library_service import list_user_libraries
from app.services.user_service import get_user_books
from app.utils.flash import get_flashed_messages

router = APIRouter(prefix="/book", tags=["Books (HTML)"])
templates = Jinja2Templates(directory="app/templates")

DBType = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

@router.get("/", response_class=HTMLResponse)
async def books_list(
    request: Request,
    db: DBType,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 50
):
    """Список всех книг"""
    books = await get_all_books(db, skip, limit)
    return templates.TemplateResponse(
        "books/list.html",
        {"request": request, "books": books, "user": current_user}
    )

@router.get("/", response_class=HTMLResponse)  #admin
async def all_books_page(request: Request, db: DBType):
    books = await get_all_books(db)
    return templates.TemplateResponse(
        "books/list.html", {"request": request, "books": books}
    )


@router.get("/my", response_class=HTMLResponse)
async def my_books(request: Request, db: DBType, current_user: CurrentUser):
    """Мои книги"""
    books = await get_user_books(db, current_user.id)
    return templates.TemplateResponse(
        "books/user_books.html",
        {"request": request, "books": books, "user": current_user}
    )


@router.get("/{book_id}", response_class=HTMLResponse)
async def book_detail(
        request: Request,
        db: DBType,
        book_id: int,
        current_user: CurrentUser
):
    """Страница книги"""
    book = await get_book_by_id(db, book_id)
    if not book:
        return templates.TemplateResponse("errors/404.html", {"request": request})

    return templates.TemplateResponse(
        "books/info.html",
        {"request": request, "book": book, "user": current_user}
    )

@router.get("/create", response_class=HTMLResponse)
async def create_book_page(request: Request, db: DBType, current_user: CurrentUser):
    """Страница добавления книги"""
    libraries = await list_user_libraries(db, current_user.id)
    return templates.TemplateResponse(
        "books/create.html",
        {"request": request, "libraries": libraries, "user": current_user}
    )


@router.post("/create")
async def create_book_submit(
    request: Request,
    db: DBType,
    current_user: CurrentUser,
    author: str = Form(...),
    title: str = Form(...),
    description: str = Form(None),
    genre: str = Form(None),
    library_id: int = Form(...)
):
    """Обработка добавления книги"""
    try:
        book_data = BookCreate(
            author=author,
            title=title,
            description=description,
            genre=genre,
            color="#3498db",
            read_status="not_read",
            lib_address="",
            room="",
            shelf=""
        )
        book = await create_book(db, book_data, current_user.id, library_id)
        return RedirectResponse(url=f"/books/{book.id}", status_code=303)
    except Exception as e:
        libraries = await list_user_libraries(db, current_user.id)
        return templates.TemplateResponse(
            "books/create.html",
            {"request": request, "error": str(e), "libraries": libraries, "user": current_user}
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


@router.get("/search", response_class=HTMLResponse)
async def search_books(
        request: Request,
        db: DBType,
        q: str,
        current_user: CurrentUser
):
    """Поиск книг"""
    books = await search_books(db, q)
    return templates.TemplateResponse(
        "books/search_results.html",
        {"request": request, "books": books, "query": q, "user": current_user}
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


@router.post("/delete/{book_id}", response_class=HTMLResponse)
async def delete_page(request: Request, db: DBType, book_id: int):
    task = await delete_book(db, book_id)
    if not task:
        return templates.TemplateResponse("errors/404.html", {"request": request})
    return templates.TemplateResponse("books/delete_id.html", {"request": request})
