import logging
from typing import Annotated

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.auth import get_current_user
from app.database.db_depends import get_db
from app.models import User, Library
from app.models.enum import GenreStatus, ReadStatus
from app.schemas.book import BookUpdate, BookCreate
from app.services.book_service import (
    get_all_books,
    get_book_by_id,
    create_book,
    delete_book,
    update_book,
    get_popular_genres,
    get_username_by_book, get_popular_authors, get_all_accessible_book_with_status,
)
from app.services.book_status_service import get_user_book_status
from app.services.library_service import list_user_libraries
from app.services.user_service import get_user_books, get_user_books_with_status
from app.utils.flash import get_flashed_messages, flash

router = APIRouter(prefix="/book", tags=["Books (HTML)"])
templates = Jinja2Templates(directory="app/templates")

logger = logging.getLogger(__name__)

DBType = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/", response_class=HTMLResponse)
async def books_list(
    request: Request,
    db: DBType,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 50,
):
    """Список всех книг"""
    books_with_status = await get_all_accessible_book_with_status(db, current_user.id)
    return templates.TemplateResponse(
        "books/list.html", {
            "request": request,
            "books_with_status": books_with_status,
            "user": current_user
        }
    )


@router.get("/", response_class=HTMLResponse)  # admin
async def all_books_page(request: Request, db: DBType):
    books = await get_all_books(db)
    return templates.TemplateResponse(
        "books/list.html", {"request": request, "books": books}
    )


@router.get("/my", response_class=HTMLResponse)
async def my_books(request: Request, db: DBType, current_user: CurrentUser):
    """Мои книги"""
    books_with_status = await get_user_books_with_status(db, current_user.id)
    return templates.TemplateResponse(
        "books/user_books.html",
        {"request": request, "books_with_status": books_with_status, "user": current_user},
    )


@router.get("/create", response_class=HTMLResponse)
async def create_book_page(request: Request, db: DBType, current_user: CurrentUser):
    """Страница добавления книги"""
    libraries = await list_user_libraries(db, current_user.id)
    popular_genres = await get_popular_genres(db)
    popular_authors = await get_popular_authors(db)

    return templates.TemplateResponse(
        "books/create.html",
        {
            "request": request,
            "libraries": libraries,
            "popular_genres": popular_genres,
            "popular_authors": popular_authors,
            "user": current_user,
        },
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
    color: str = Form(None),
    read_status: str = Form(...),
    room: str = Form(None),
    shelf: str = Form(None),
    library_id: int = Form(...),
):
    """Обработка добавления книги"""
    logger.info(f" ✅1 {read_status}")
    try:
        logger.info(f" ✅2 {read_status}")
        library = await db.get(Library, library_id)
        if not library:
            raise HTTPException(status_code=404, detail="Библиотека не найдена")
        book_data = BookCreate(
            author=author.title(),
            title=title.capitalize(),
            description=description,
            genre=genre,
            color=color,
            read_status=read_status,
            lib_address=library.name,
            room=room.capitalize(),
            shelf=shelf.capitalize(),
        )
        book = await create_book(db, book_data, current_user.id, library_id)
        flash(request, "Книга успешно добавлена", "success")
        return RedirectResponse(url=f"/book/{book.id}", status_code=303)
    except Exception as e:
        flash(request, "Не удалось добавить книгу", "error")
        libraries = await list_user_libraries(db, current_user.id)
        return templates.TemplateResponse(
            "books/create.html",
            {
                "request": request,
                "error": str(e),
                "libraries": libraries,
                "user": current_user
            },
        )


@router.get("/search", response_class=HTMLResponse)
async def search_books(request: Request, db: DBType, q: str, current_user: CurrentUser):
    """Поиск книг"""
    books = await search_books(db, q)
    return templates.TemplateResponse(
        "books/search_results.html",
        {"request": request, "books": books, "query": q, "user": current_user},
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


@router.post("/{book_id}/delete", response_class=HTMLResponse)
async def delete_page(
    request: Request, db: DBType, book_id: int, current_user: CurrentUser
):
    """Удалить книгу"""
    book = await get_book_by_id(db, book_id)

    if not book:
        flash(request, "Книга не найдена", "error")
        return RedirectResponse(url="/book", status_code=303)

    # Проверка прав (только владелец или админ)
    # if book.user_id != current_user.id and not current_user.is_admin:
    if book.user_id != current_user.id:
        flash(request, "У вас нет прав на удаление этой книги", "error")
        return RedirectResponse(url=f"/book/{book_id}", status_code=303)

    await delete_book(db, book_id)

    flash(request, f"Книга '{book.title}' удалена", "success")
    return RedirectResponse(url="/book", status_code=303)


@router.get("/{book_id}/edit", response_class=HTMLResponse)
async def edit_book_page(
    request: Request, db: DBType, book_id: int, current_user: CurrentUser
):
    """Страница редактирования книги"""
    book = await get_book_by_id(db, book_id)

    if not book:
        flash(request, "Книга не найдена", "error")
        return RedirectResponse(url="/book/", status_code=303)

    if book.user_id != current_user.id:
        flash(request, "У вас недостаточно прав на редактирование этой книги", "error")
        return RedirectResponse(url=f"/book/{book_id}", status_code=303)

    # Получаем библиотеки пользователя
    libraries = await list_user_libraries(db, current_user.id)
    popular_genres = await get_popular_genres(db)
    popular_authors = await get_popular_authors(db)

    return templates.TemplateResponse(
        "books/edit.html",
        {
            "request": request,
            "book": book,
            "libraries": libraries,
            "popular_genres": popular_genres,
            "popular_authors": popular_authors,
            "user": current_user,
        },
    )


@router.post("/{book_id}/edit")
async def edit_book_submit(
    request: Request,
    db: DBType,
    book_id: int,
    current_user: CurrentUser,
    author: str = Form(...),
    title: str = Form(...),
    description: str = Form(None),
    genre: str = Form(None),
    color: str = Form(None),
    read_status: str = Form(...),
    lib_address: str = Form(None),
    room: str = Form(None),
    shelf: str = Form(None),
):
    """Обработка редактирования книги"""
    try:
        book = await get_book_by_id(db, book_id)

        if not book or book.user_id != current_user.id:
            flash(request, "Книга не найдена или нет прав", "error")
            return RedirectResponse(url="/book/", status_code=303)

        update_data = BookUpdate(
            author=author,
            title=title,
            description=description,
            genre=genre,
            color=color,
            read_status=read_status,
            lib_address=lib_address,
            room=room,
            shelf=shelf,
        )
        logger.info(f" ✅ {update_data}")
        result = await update_book(db, current_user.id, book_id, update_data)

        if result:
            flash(request, f"Книга '{title}' обновлена!", "success")
            return RedirectResponse(url=f"/book/{book_id}", status_code=303)
        else:
            flash(request, "Ошибка обновления книги", "error")
            return RedirectResponse(url=f"book/{book_id}", status_code=303)

    except Exception as e:
        logger.error(f"Error updating book: {e}")
        flash(request, f"Ошибка обновления: {str(e)}", "error")
        return RedirectResponse(url=f"/books/{book_id}/edit", status_code=303)


@router.get("/{book_id}", response_class=HTMLResponse)
async def book_detail(
    request: Request, db: DBType, book_id: int, current_user: CurrentUser
):
    """Страница книги"""
    book = await get_book_by_id(db, book_id)
    if not book:
        flash(request, f"Книга не найдена", "error")
        return templates.TemplateResponse("errors/404.html", {"request": request})
    user = await get_username_by_book(db, book_id)
    read_status = ReadStatus(await get_user_book_status(db, current_user.id, book_id))

    return templates.TemplateResponse(
        "books/info.html",
        {"request": request,
         "book": book,
         "user": user,
         "current_user": current_user,
         "read_status": read_status.russian_name
         },
    )
