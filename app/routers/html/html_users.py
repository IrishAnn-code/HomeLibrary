from typing import Annotated

from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.database.auth import get_current_user
from app.database.db_depends import get_db
from app.models import User
from app.schemas.user import UserCreate, UserLogin
from app.services.user_service import (
    get_all_users,
    get_user_by_id,
    get_user_books,
    update_user,
    delete_user,
    create_user,
    authenticate_user,
)
from app.utils.jwt import create_access_token

router = APIRouter(prefix="/user", tags=["Users (HTML)"])
templates = Jinja2Templates(directory="app/templates")
limiter = Limiter(key_func=get_remote_address)

logger = logging.getLogger(__name__)
DBType = Annotated[AsyncSession, Depends(get_db)]


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """HTML Страница регистрации"""
    return templates.TemplateResponse("users/register.html", {"request": request})


@router.post("/register")
@limiter.limit("1/hour")
async def register_submit(
    request: Request,
    db: AsyncSession = Depends(get_db),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),

):
    """Обработка HTML-страницы регистрации"""
    try:
        user = await create_user(db, username, email, password)

        token = create_access_token(user.id)
        response = RedirectResponse(url="/user/profile", status_code=303)
        response.set_cookie(
            key="access_token",
            value=f"Bearer {token}",
            httponly=True,
            # secure=True,
            samesite="strict",
            max_age=7 * 24 * 3600,
            path="/"
        )
        return response

    except Exception as e:
        # Для HTML возвращаем страницу с ошибкой
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": str(e),
                "username": username,
                "email": email
            }
        )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """HTML-страница входа"""
    return templates.TemplateResponse("users/login.html", {"request": request})


@router.post("/login")
@limiter.limit("1/minute")
async def login_submit(
    request: Request,
    db: AsyncSession = Depends(get_db),
    data: UserLogin = Depends(UserLogin.as_form),
):
    """Обработка входа"""
    logger.info(f"🔐 Login attempt: {data.username}")
    user = await authenticate_user(db, data.username, data.password)

    if not user:
        logger.warning(f"❌ Invalid credentials for: {data.username}")
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Invalid username or password",
                "username": data.username
            }
        )

    token = create_access_token(user.id)
    logger.info(f"✅ Token created for user {user.id}: {token[:20]}...")

    response = RedirectResponse(url="/library", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        secure=False,  # ✅ True Только HTTPS (в production обязательно!)
        samesite="lax",  # ✅ Защита от CSRF
        max_age=7 * 24 * 3600,
        # domain=None,  # Текущий домен
        path="/"
    )

    logger.info(f"✅ Cookie set for user {user.id}")
    return response


@router.get("/me", response_class=HTMLResponse)
async def profile_page(request: Request, current_user: User = Depends(get_current_user)):
    """Страница профиля"""
    return templates.TemplateResponse(
        "users/info.html",
        {
            "request": request,
            "user": current_user
        }
    )


@router.get("/books/{user_id}", response_class=HTMLResponse)
async def user_books(request: Request, db: DBType, user_id: int):
    books = await get_user_books(db, user_id)
    user = await get_user_by_id(db, user_id)
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

@router.get("/logout")
async def logout():
    """Выход из системы"""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response


# ✅ Admin эндпоинты
@router.get("/", response_class=HTMLResponse)
async def all_users(request: Request, db: DBType):
    users = await get_all_users(db)
    if not users:
        return templates.TemplateResponse("errors/404.html", {"request": request})
    return templates.TemplateResponse(
        "users/list.html",
        {"request": request, "users": users, "title": "Список пользователей"},
    )