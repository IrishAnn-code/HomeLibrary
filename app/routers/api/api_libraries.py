from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db_depends import get_db
from app.database.auth import get_current_user
from app.core.exceptions import not_found, bad_request, forbidden
from app.models import User
from app.schemas.library import LibraryCreate
from app.services.library_service import (
    get_library,
    create_library,
    list_user_libraries,
    all_books_in_lib,
    join_library,
    get_library_by_slug,
    update_name,
)


router = APIRouter(prefix="/library", tags=["Library (API)"])

DBType = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/", response_model=None)
async def libraries_list(db: DBType, user_id: CurrentUser):
    """Все библиотеки пользователя"""
    lib = await get_library(db, user_id.id)
    if lib is None:
        not_found("Libraries not found")
    return lib


@router.post("/create", response_model=None)
async def create_new_library(
    db: DBType, data: LibraryCreate, current_user: CurrentUser
):
    return await create_library(db, data.name, data.password, current_user.id)


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
        not_found("Library not found")
    return lib


@router.get("/{lib_id}", response_model=None)
async def library_books(db: DBType, lib_id: int):
    """Книги, которые лежат в библиотеке"""
    books = await all_books_in_lib(db, lib_id)
    if books is None:
        not_found("Books not found")
    return books


@router.get("/user/{user_id}", response_model=None)
async def libraries_by_user(db: DBType, user_id: int):
    libs = await list_user_libraries(db, user_id)
    return libs


@router.put("/edit_name")
async def edit_lib_name(
    db: DBType, new_name: str, lib_id: int, current_user: CurrentUser
):
    """Обновить название библиотеки"""
    return await update_name(db, new_name, lib_id, current_user.id)
