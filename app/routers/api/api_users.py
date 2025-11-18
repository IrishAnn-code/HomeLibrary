from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.auth import get_current_user
from app.database.db_depends import get_db
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

DBType = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/")
async def all_users(db: DBType):
    users = await get_all_users(db)
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No users found")
    return users


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with username, email and password",
)
async def register_user(db: DBType, data: UserCreate):
    user = await register(db, data.username, data.email, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists")
    return {"id": user.id, "username": user.username}


@router.post("/login")
async def login_user(db: DBType, data: UserLogin):
    user = await login(db, data.username, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials")
    return user


@router.get("/me")
async def get_profile(current_user=Depends(get_current_user)):
    return {
        "username": current_user.username,
        "email": current_user.email,
        "id": current_user.id}


@router.get("/books/me")
async def get_user_books(db: DBType, current_user: CurrentUser):
    """Просмотр книг только текущего пользователя"""
    books = await book_by_user_id(db, current_user.id)
    if books is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User or books was not found")
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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied")

    user = await update_user(db, user_id, password, user_update)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The password and login does not match")
    return {
        "status_code": status.HTTP_200_OK,
        "transaction": "The user has been updated successfully",
        "user": user,
    }


@router.delete("/delete/me")
async def delete_my_account(db: DBType, current_user: CurrentUser):
    deleted = await delete_user(db, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to delete {current_user.id}')
    return {
        "status_code": status.HTTP_200_OK,
        "transaction": "Account deleted successfully",
    }


@router.get("/{user_id}")
async def get_user_info(db: DBType, user_id: int):
    user = await user_info(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User: {user_id} not found")
    return user
