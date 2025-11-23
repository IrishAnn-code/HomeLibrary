from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db_depends import get_db
from app.database.auth import get_current_user
from app.models import User
from app.schemas.library import LibraryCreate
from app.services.library_service import (
    create_library,
    list_user_libraries,
    all_books_in_lib,
    join_library,
    get_library_by_slug,
    update_name,
)


router = APIRouter(prefix="/libraries", tags=["Library (API)"])

DBType = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/", response_model=None)
async def get_my_libraries(db: DBType, current_user: CurrentUser):
    """
    Получить все библиотеки текущего пользователя.
    Требуется авторизация (токен в cookie или Authorization header).
    """
    libs = await list_user_libraries(db, current_user.id)
    return libs


@router.post("/", response_model=None)
async def create_new_library(
    db: DBType, data: LibraryCreate, current_user: CurrentUser
):
    """Создать новую библиотеку."""
    library = await create_library(db, data.name, data.password, current_user.id)
    return library


@router.post("/join", response_model=None)
async def join_to_library(
    db: DBType, data: str, password: str, current_user: CurrentUser
):
    """Пользователь подключается к существующей библиотеке"""
    return await join_library(db, data, password, current_user.id)


@router.get("/{slug}", response_model=None)
async def get_lib(db: DBType, slug: str):
    """Найти библиотеку по slug"""
    lib = await get_library_by_slug(db, slug)
    if not lib:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Library not found"
        )
    return lib


@router.get("/{lib_id}", response_model=None)
async def library_books(db: DBType, lib_id: int):
    """Книги, которые лежат в библиотеке"""
    books = await all_books_in_lib(db, lib_id)
    if not books:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Books not found"
        )
    return books


@router.put("/edit_name")
async def edit_lib_name(
    db: DBType, new_name: str, lib_id: int, current_user: CurrentUser
):
    """Обновить название библиотеки"""
    return await update_name(db, new_name, lib_id, current_user.id)
