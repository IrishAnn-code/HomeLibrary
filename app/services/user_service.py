from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from starlette.responses import RedirectResponse, HTMLResponse
from fastapi import status

from app.models import Book
from app.schemas.user import UserCreate
from app.utils.hashing import hash_password, verify_password
from app.models.user import User
from app.utils.jwt import create_access_token


async def get_all_users(db: AsyncSession):
    result = await db.scalars(select(User))
    return result.all()


async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def register(db: AsyncSession, username: str, email: str, password: str):
    existing_user = await db.scalar(
        select(User).where((User.email == email) | (User.username == username))
    )
    if existing_user:
        return None
    user = User(username=username, email=email, password_hash=hash_password(password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def login(db: AsyncSession, username: str, password: str):
    user = await db.scalar(select(User).where(User.username == username))
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    token = create_access_token(user.id)
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        secure=False,  # ✅ True Только HTTPS (в production обязательно!)
        samesite="strict",  # ✅ Защита от CSRF
        max_age=7 * 24 * 3600,
        # domain=None,  # Текущий домен
        path="/",
    )
    return response


async def user_info(db: AsyncSession, user_id: int):
    user = await db.get(User, user_id)
    return user


async def book_by_user_id(db: AsyncSession, user_id: int):
    user = await db.scalar(select(User).where(User.id == user_id))
    if not user:
        return None
    books = await db.scalars(select(Book).where(Book.user_id == user_id))
    if not books:
        return None
    return books.all()


async def update_user(
    db: AsyncSession, user_id: int, password: str, user_update: UserCreate
):
    user = await db.get(User, user_id)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None

    data = {}
    if user_update.firstname is not None:
        data["firstname"] = user_update.firstname
    if user_update.lastname is not None:
        data["lastname"] = user_update.lastname
    if user_update.password is not None:
        data["password_hash"] = hash_password(user_update.password)
    if data:
        await db.execute(update(User).where(User.id == user_id).values(**data))
        await db.commit()
        await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: int):
    user = await db.get(User, user_id)
    if not user:
        return None
    await db.delete(user)
    await db.commit()
    return True
