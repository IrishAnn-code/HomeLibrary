from typing import Annotated
from fastapi import APIRouter, Depends, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.auth import get_current_user
from app.database.db_depends import get_db
from app.core.exceptions import not_found, bad_request, authorization_error, forbidden
from app.main import limiter
from app.models import User
from app.schemas.user import UserCreate, UserOut, UserLogin
from app.services.user_service import (
    register,
    login,
    get_all_users,
    user_info,
    update_user,
    delete_user,
    book_by_user_id,
)
from app.utils.hashing import verify_password, hash_password

router = APIRouter(prefix="/users", tags=["Users (API)"])
limiter = Limiter(key_func=get_remote_address())

DBType = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/")
async def all_users(db: DBType):
    users = await get_all_users(db)
    if not users:
        not_found("No users found")
    return users


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with username, email and password",
)
@limiter.limit("3/hour")
async def register_user(db: DBType, data: UserCreate):
    user = await register(db, data.username, data.email, data.password)
    if not user:
        raise bad_request("User with this email or username already exists")
    return {"id": user.id, "username": user.username}


@router.post("/login")
@limiter.limit("5/minute")
async def login_user(db: DBType, data: UserLogin):
    user = await login(db, data.username, data.password)
    if not user:
        authorization_error("Invalid credentials")
    return user


@router.get("/me")
async def get_profile(current_user=Depends(get_current_user)):
    return {"username": current_user.username, "email": current_user.email}


@router.get("/books/me")
async def get_user_books(db: DBType, current_user: CurrentUser):
    """Просмотр книг только текущего пользователя"""
    books = await book_by_user_id(db, current_user.id)
    if books is None:
        not_found("User or books was not found")
    return books


@router.put("/update")
async def edit_user_info(
    db: DBType,
    user_id: int,
    password: str,
    user_update: UserCreate,
    current_user: CurrentUser,
):
    if current_user.id != user_id:
        forbidden("Access denied")

    user = await update_user(db, user_id, password, user_update)
    if not user:
        authorization_error("The password and login does not match")
    return {
        "status_code": status.HTTP_200_OK,
        "transaction": "The user has been updated successfully",
        "user": user,
    }


@router.delete("/delete/{user_id}")
async def remove_task(db: DBType, user_id: int):
    deleted = await delete_user(db, user_id)
    if not deleted:
        not_found(f"Book: {user_info(db, user_id)} was not found")
    return {
        "status_code": status.HTTP_200_OK,
        "transaction": "User delete is successful",
    }


@router.get("/{user_id}")
async def get_user_info(db: DBType, user_id: int):
    user = await user_info(db, user_id)
    if not user:
        not_found(f"User: {user_id} not found")
    return user

