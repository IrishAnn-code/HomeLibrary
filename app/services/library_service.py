from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
import logging

from app.models import Book, Library, UserLibrary, User
from app.models.enum import LibraryRole
from app.services.book_status_service import add_read_status_to_book
from app.utils.hashing import hash_password, verify_password
from app.utils.helpers import make_slug

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


async def get_username_by_lib_id(db: AsyncSession, library_id: int):
    """Получить username владельца библиотеки, по id библиотеки"""
    result = await db.scalar(
        select(User)
        .join(UserLibrary, UserLibrary.user_id == User.id)
        .where(
            (UserLibrary.library_id == library_id)
            & (UserLibrary.role == LibraryRole.OWNER)
        )
    )
    owner_username = result.username
    return owner_username


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
    """
    Все книги в одной библиотеке
    return: Список книг
    """
    books = await db.scalars(select(Book).where(Book.library_id == lib_id))
    return books.all()


async def get_library_books_with_status(db: AsyncSession, lib_id: int, user_id: int):
    """Получить книги в библиотеке со статусами чтения для текущего пользователя"""
    books = await all_books_in_lib(db, lib_id)
    books_with_status = await add_read_status_to_book(db, user_id, books)
    logger.info(f"🔍 {books_with_status}")
    return books_with_status


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
        slug = make_slug(name, unique=True)
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
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Библиотека с таким именем уже существует")


async def join_library(
    db: AsyncSession, lib_id_or_name: str | int, password: str, user_id: int
):
    """Присоединиться к библиотеке по имени или id"""
    lib = None
    if isinstance(lib_id_or_name, int) or (
        isinstance(lib_id_or_name, str) and str(lib_id_or_name).isdigit()
    ):
        lib = await db.scalar(
            select(Library).where(
                (Library.id == int(lib_id_or_name)) | (Library.name == lib_id_or_name)
            )
        )

    if not lib:
        lib = await db.scalar(select(Library).where(Library.name == lib_id_or_name))

    if not lib:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Library not found"
        )

    if lib.password_hash:
        if not verify_password(password, lib.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password"
            )
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Library not found"
        )

    if user_id != library.owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к библиотеке"
        )

    await db.execute(
        update(Library).where(Library.id == lib_id).values(name=new_name.strip())
    )
    await db.commit()
    return True


async def search_libraries_to_join(db: AsyncSession, user_id: int, query: str = ""):
    """
    Поиск библиотек по названию (регистронезависимый для латиницы и кириллицы).
    Список библиотек для присоединения, в которых пользователь не OWNER и не MEMBER.
    """
    query = query.lower().strip()
    if not query:
        return []

    my_lib_ids = [lib.id for lib in await list_user_libraries(db, user_id)]

    result = await db.execute(
        select(Library).where(Library.id.notin_(my_lib_ids)).order_by(Library.name)
    )
    all_libraries = result.scalars().all()
    matching = [lib for lib in all_libraries if query in lib.name.lower()]

    logger.info(f"🔍 Поиск библиотек: запрос='{query}'")
    logger.info(f"📚 Всего библиотек для поиска: {len(all_libraries)}")
    logger.info(f"✅ Найдено совпадений: {len(matching)}")

    return matching


async def leave_library(
    db: AsyncSession, library_id: int, user_id: int
) -> tuple[bool, str]:
    """
    Выйти из библиотеки
    :return: tuple: (success: bool, message: str)
    """
    library = await get_library(db, library_id)
    if not library:
        return False, "Библиотека не найдена."

    if library.owner_id == user_id:
        return (
            False,
            "Создатель не может выйти из библиотеки. Воспользуйтесь удалением.",
        )

    membership = await is_library_member(db, user_id, library_id)
    if not membership:
        return False, "Вы не состоите в этой библиотеке"

    await db.delete(membership)
    await db.commit()

    logger.info(f"Пользователь {user_id} покинул библиотеку - '{library.name}'")
    return True, "Вы покинули библиотеку"


async def delete_library(
    db: AsyncSession, library_id: int, user_id: int, is_admin: bool = False
) -> tuple[bool, str]:
    """
    Удалить библиотеку (только owner или admin)
    :return: tuple: (success: bool, message: str)
    """
    library = await get_library(db, library_id)
    if not library:
        return False, "Библиотека не найдена."

    if library.owner_id != user_id and not is_admin:
        return False, "Только владелец библиотеки или админ могут удалить библиотеку"

    await db.delete(library)
    await db.commit()
    logger.info(f"Библиотека '{library.name}' была удалена пользователем {user_id}")
    return True, f"Библиотека '{library.name}' удалена."
