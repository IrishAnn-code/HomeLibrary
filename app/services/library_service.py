from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update

from app.core.exceptions import not_found, authorization_error, bad_request
from app.models import Book, User, Library, UserLibrary
from app.utils.hashing import hash_password, verify_password
from app.utils.helpers import make_slug
import logging

logger = logging.getLogger(__name__)


async def get_libraries(db: AsyncSession):
    """Список всех библиотек"""
    libraries = await db.scalars(select(Library))
    return libraries.all()


async def get_library(db: AsyncSession, lib_id: int):
    """Получить библиотеку по id"""
    return await db.get(Library, lib_id)


async def get_library_by_name(db: AsyncSession, name: str):
    """Поиск по имени библиотеки"""
    library = await db.scalar(select(Library).where(Library.name == name))
    return library


async def list_user_libraries(db: AsyncSession, user_id: int):
    """Список библиотек пользователя"""
    result = await db.execute(
        select(Library).join(UserLibrary).where(UserLibrary.user_id == user_id)
    )
    return result.scalars().all()


async def is_library_member(db: AsyncSession, user_id: int, library_id: int):
    """Является ли пользователь участником библиотеки"""
    logger.info(f"🔍 Checking membership: user_id={user_id}, library_id={library_id}")
    is_member = await db.scalar(
        select(UserLibrary).where(
            (UserLibrary.user_id == user_id) & (UserLibrary.library_id == library_id)
        )
    )
    return is_member


async def all_books_in_lib(db: AsyncSession, lib_id: int):
    """Все книги в одной библиотеке"""
    books = await db.scalars(select(Book).where(Book.library_id == lib_id))
    return books.all()


async def books_in_address(db: AsyncSession, lib_id: int, lib_address: str):
    """Все книги библиотеки, которые лежат по одному адресу"""
    books = await db.scalars(
        select(Book).where(
            (Book.library_id == lib_id) & (Book.lib_address == lib_address)
        )
    )
    return books.all()


async def create_library(
    db: AsyncSession, name: str, password: str | None, owner_id: int
):
    """Создать новую библиотеку, связь с UserLibrary"""
    if not name:
        raise HTTPException(status_code=400, detail="Library name cannot be empty")
    try:
        slug = make_slug(name)
        hashed = hash_password(password) if password else None

        lib = Library(name=name, password_hash=hashed, slug=slug, owner_id=owner_id)
        db.add(lib)
        await db.flush()  # Получаем lib.id без commit

        # Добавляем владельца как участника
        membership = UserLibrary(user_id=owner_id, library_id=lib.id, role="owner")
        db.add(membership)
        await db.commit()
        await db.refresh(lib)
        logger.info(
            f"✅ Библиотека с названием {name} для пользователя {owner_id} успешно создана!"
        )
        return lib
    except Exception as e:
        await db.rollback()
        raise


async def join_library(
    db: AsyncSession, lib_id_or_name: str | int, password: str, user_id: int
):
    """Присоединиться к библиотеке по имени или id"""
    lib = None
    if isinstance(lib_id_or_name, int) or (
        isinstance(lib_id_or_name, str) and str(lib_id_or_name).isdigit()
    ):
        lib = await db.get(Library, int(lib_id_or_name))
    if not lib:
        lib = await db.scalar(select(Library).where(Library.name == lib_id_or_name))
    if not lib:
        not_found("Library not found")
    if lib.password_hash:
        if not verify_password(password, lib.password_hash):
            authorization_error("Incorrect password")
    # Проверяем, не состоит ли уже пользователь
    existing = await db.scalar(
        select(UserLibrary).where(
            (UserLibrary.user_id == user_id) & (UserLibrary.library_id == lib.id)
        )
    )
    if existing:
        return lib
    link = UserLibrary(user_id=user_id, library_id=lib.id, role="member")
    db.add(link)
    await db.commit()
    return lib


async def get_library_by_slug(db: AsyncSession, slug: str):
    """Найти библиотеку по slug"""
    library = await db.scalar(select(Library).where(Library.slug == slug))
    return library


async def update_name(db: AsyncSession, new_name: str, lib_id: int, user_id: int):
    """Обновить название библиотеки"""
    library = await db.scalar(
        select(Library).where((Library.id == lib_id) & (Library.owner_id == user_id))
    )
    if not library:
        bad_request("Library not found")
    await db.execute(update(Library).where(Library.id == lib_id).values(name=new_name))
    await db.commit()
    return True


async def list_of_libs_to_join(db: AsyncSession, user_id: int, query: str = ""):
    """
    Список библиотек для присоединения, которые не принадлежат пользователю
    """
    if query:
        my_lib_ids = [lib.id for lib in await list_user_libraries(db, user_id)]
        search_query = f"%{query}%"

        result = await db.execute(
            select(Library)
            .where(Library.name.ilike(search_query))
            .where(Library.id.notin_(my_lib_ids))
            .order_by(Library.name)
        )
        logger.info(f"ASDFGHJKL:{result}")
        return result.scalars().all()
    else:
        return []
