from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from typing import Annotated

from app.core.config import settings
from app.database.auth import get_current_user
from app.database.db_depends import get_db
from app.models import User
from app.schemas.user import UserUpdate
from app.services import user_service
from app.services.user_service import update_user
from app.utils.jwt import create_access_token
from app.utils.flash import flash, get_flashed_messages

router = APIRouter(prefix="/user", tags=["Users (HTML)"])
templates = Jinja2Templates(directory="app/templates")
limiter = Limiter(key_func=get_remote_address)

logger = logging.getLogger(__name__)

DBType = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """HTML Страница регистрации"""
    return templates.TemplateResponse(
        "users/register.html",
        {
            "request": request,
            "messages": get_flashed_messages(request),
        },
    )


@router.post("/register")
@limiter.limit("3/hour")
async def register_submit(
    request: Request,
    db: DBType,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    """Обработка HTML-страницы регистрации"""
    try:
        user = await user_service.create_user(db, username, email, password)

        token = create_access_token(user.id)

        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=settings.USE_SECURE_COOKIES,  # False для dev, True для prod
            samesite="strict",
            max_age=7 * 24 * 3600,
            path="/",
        )
        logger.info(f"✅ User registered and logged in: {user.id}")
        return response

    except Exception as e:
        # возвращаем страницу с ошибкой
        logger.error(f"Registration error: {e}")
        return templates.TemplateResponse(
            "users/register.html",
            {
                "request": request,
                "messages": get_flashed_messages(request),
                "error": str(e),
                "username": username,
                "email": email,
            },
        )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """HTML-страница входа"""
    return templates.TemplateResponse(
        "users/login.html",
        {
            "request": request,
            "messages": get_flashed_messages(request),
        },
    )


@router.post("/login")
@limiter.limit("5/minute")
async def login_submit(
    request: Request, db: DBType, username: str = Form(...), password: str = Form(...)
):
    """Обработка входа"""
    logger.info(f"🔐 Login attempt: {username}")
    user = await user_service.authenticate_user(db, username, password)

    if not user:
        logger.warning(f"❌ Invalid credentials for: {username}")
        # ❌ Ошибка - добавляем flash
        flash(request, "Неверное имя пользователя или пароль", "error")
        return RedirectResponse(url="/user/login", status_code=303)

    token = create_access_token(user.id)
    logger.info(f"✅ Token created for user {user.id}: {token[:20]}...")

    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.USE_SECURE_COOKIES,  # ✅ True Только HTTPS (в production обязательно!), False для localhost
        samesite="strict",  # ✅ Защита от CSRF
        max_age=7 * 24 * 3600,
        # domain=None,  # Текущий домен
        path="/",
    )

    logger.info(f"✅ Cookie set for user {user.id}")
    # ✅ Успех - добавляем flash
    flash(request, f"Добро пожаловать, {user.username}!", "success")
    return response


@router.get("/me", response_class=HTMLResponse)
async def profile_page(request: Request, user: CurrentUser):
    """Страница профиля"""
    return templates.TemplateResponse(
        "users/info.html",
        {"request": request, "messages": get_flashed_messages(request), "user": user},
    )


@router.get("/logout")
async def logout():
    """Выход из системы"""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token", path="/")
    return response


@router.get("/books/me", response_class=HTMLResponse)
async def my_books_page(request: Request, db: DBType, current_user: CurrentUser):
    books = await user_service.get_user_books(db, current_user.id)

    return templates.TemplateResponse(
        "books/user_books.html",
        {
            "request": request,
            "messages": get_flashed_messages(request),
            "books": books,
            "user": current_user,
            "title": "Мои книги",
        },
    )


@router.get("/edit", response_class=HTMLResponse)
async def edit_user_page(request: Request, db: DBType, current_user: CurrentUser):
    """Страница редактирования профиля"""
    return templates.TemplateResponse(
        "users/edit.html",
        {
            "request": request,
            "messages": get_flashed_messages(request),
            "user": current_user,
        },
    )


@router.post("/edit", response_class=HTMLResponse)
async def edit_user_submit(
    request: Request,
    db: DBType,
    current_user: CurrentUser,
    firstname: str = Form(None),
    lastname: str = Form(None),
    email: str = Form(None),
    password: str = Form(None),
    current_password: str = Form(...),
):
    user_update = UserUpdate(
        firstname=firstname, lastname=lastname, email=email, password=password
    )
    user = await update_user(db, current_user.id, current_password, user_update)

    if user:
        flash(request, "Профиль успешно обновлен!", "success")
        return RedirectResponse(url="/user/me", status_code=303)
    else:
        flash(request, "Ошибка при обновлении профиля", "error")
        return RedirectResponse(url="/update", status_code=303)


@router.delete("/delete", response_class=HTMLResponse)
async def delete(request: Request, db: DBType, user_id: int):
    user = await user_service.delete_user(db, user_id)
    if user is None:
        return templates.TemplateResponse("errors/404.html", {"request": request})
    return templates.TemplateResponse("books/delete.html", {"request": request})


# ✅ Admin эндпоинты
@router.get("/", response_class=HTMLResponse)
async def all_users_page(request: Request, db: DBType, current_user: CurrentUser):
    """Страница со списком всех пользователей"""
    users = await user_service.get_all_users(db)
    if not users:
        return templates.TemplateResponse("errors/404.html", {"request": request})
    return templates.TemplateResponse(
        "users/list.html",
        {
            "request": request,
            "messages": get_flashed_messages(request),
            "users": users,
            "title": "Список пользователей",
        },
    )
