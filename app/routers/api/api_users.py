from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.auth import get_current_user
from app.database.db_depends import get_db
from app.models import User
from app.schemas.user import UserCreate, UserOut, UserLogin, UserUpdate
from app.services.user_service import (
    create_user,
    get_all_users,
    update_user,
    delete_user,
    get_user_books,
)

router = APIRouter(prefix="/users", tags=["Users (API)"])
limiter = Limiter(key_func=get_remote_address)

DBType = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with username, email and password",
)
@limiter.limit("3/hours")
async def register_user(request: Request, db: DBType, data: UserCreate):
    """
    Зарегистрировать нового пользователя.

    - **username**: Уникальное имя пользователя (5-15 символов)
    - **email**: Email адрес
    - **password**: Пароль (минимум 8 символов)
    """
    # Сервис выбросит HTTPException если ошибка → FastAPI автоматически вернет JSON
    user = await create_user(db, data.username, data.email, data.password)
    return user


@router.get("/me",
            response_model=UserOut,
            summary='Get information about the current user')
async def get_my_profile(current_user: CurrentUser):
    """Получить профиль текущего авторизованного пользователя."""
    return current_user


@router.get("/me/books",
            summary='Get books from the current user')
async def get_my_books(db: DBType, current_user: CurrentUser, skip: int = 0, limit: int = 100):
    """
    Получить все книги текущего пользователя с пагинацией.

    - **skip**: Количество пропускаемых записей (по умолчанию: 0)
    - **limit**: Максимум записей в ответе (по умолчанию: 100)
    """
    books = await get_user_books(db, current_user.id, skip, limit)
    return books


@router.put("/me",
            response_model=UserOut,
            summary="Update the current user's profile" )
async def update_my_profile(
    db: DBType,
    password: str,
    user_update: UserUpdate,
    current_user: CurrentUser
):
    """
    Обновить данные своего профиля.

    - **current_password**: Текущий пароль (для подтверждения)
    - **firstname**: Новое имя (опционально)
    - **lastname**: Новая фамилия (опционально)
    - **email**: Новый email (опционально)
    - **password**: Новый пароль (опционально)
    """
    updated_user = await update_user(db, current_user.id, password, user_update)
    return updated_user


@router.delete("/me",
               status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete your account")
async def delete_my_account(db: DBType, current_user: CurrentUser):
    """Удалить свой аккаунт навсегда."""
    await delete_user(db, current_user.id)
    return None


# ✅ Admin эндпоинты
@router.get(
    "/",
    response_model=list[UserOut],
    summary="[Admin] Получить всех пользователей"
)
async def get_all_users(
    db: DBType,
    current_user: CurrentUser,  # TODO: добавить проверку is_admin
    skip: int = 0,
    limit: int = 100
):
    """Получить список всех пользователей (только для админов)."""
    # TODO: добавить проверку is_admin
    users = await get_all_users(db, skip, limit)
    return users
