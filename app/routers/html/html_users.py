from typing import Annotated

from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db_depends import get_db
from app.core.exceptions import not_found
from app.schemas.user import UserCreate, UserLogin
from app.services.user_service import (
    get_all_users,
    user_info,
    book_by_user_id,
    update_user,
    delete_user,
    register,
    login,
)

router = APIRouter(prefix="/user", tags=["Users (HTML)"])
templates = Jinja2Templates(directory="app/templates")
limiter = Limiter(key_func=get_remote_address)

DBType = Annotated[AsyncSession, Depends(get_db)]


@router.get("/", response_class=HTMLResponse)
async def all_users(request: Request, db: DBType):
    users = await get_all_users(db)
    if not users:
        return templates.TemplateResponse("errors/404.html", {"request": request})
    return templates.TemplateResponse(
        "users/list.html",
        {"request": request, "users": users, "title": "Список пользователей"},
    )


# ---- HTML Форма регистрации ----
@router.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse("users/register.html", {"request": request})


# ---- POST: Отправка формы регистрации ----
@router.post("/register")
@limiter.limit("3/hour")
async def register_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    await register(db, username, email, password)
    return RedirectResponse(url="/user/login", status_code=303)


# ---- HTML Форма входа ----
@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("users/login.html", {"request": request})


# ---- POST: Отправка формы входа ----
@router.post("/login")
@limiter.limit("1/minute")
async def login_user(
    request: Request,
    data: UserLogin = Depends(UserLogin.as_form),
    db: AsyncSession = Depends(get_db),
):
    result = await login(db, data.username, data.password)
    if result is None:
        return templates.TemplateResponse(
            "errors/404.html", {"request": request, "error": "Invalid credentials"}
        )

    return RedirectResponse(url="/library", status_code=303)


@router.get("/books/{user_id}", response_class=HTMLResponse)
async def user_books(request: Request, db: DBType, user_id: int):
    books = await book_by_user_id(db, user_id)
    user = await user_info(db, user_id)
    if books or user is None:
        return templates.TemplateResponse("errors/404.html", {"request": request})

    return templates.TemplateResponse(
        "books/user_books.html",
        {"request": request, "books": books, "user": user, "title": "Список книг"},
    )


@router.put("/update", response_class=HTMLResponse)
async def edit_user(
    request: Request, db: DBType, user_id: int, update_u: UserCreate, password: str
):
    user = await update_user(db, user_id, password, update_u)
    if user is None:
        return templates.TemplateResponse("errors/404.html", {"request": request})
    return templates.TemplateResponse(
        "users/info.html", {"request": request, "user": user}
    )


@router.delete("/delete", response_class=HTMLResponse)
async def delete(request: Request, db: DBType, user_id: int):
    user = await delete_user(db, user_id)
    if user is None:
        return templates.TemplateResponse("errors/404.html", {"request": request})
    return templates.TemplateResponse("books/delete.html", {"request": request})


