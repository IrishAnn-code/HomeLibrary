from fastapi import Query, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from app.models import Book, User, Library
from app.schemas.book import BookCreate, BookUpdate
from app.services.book_status_service import update_user_book_status, add_read_status_to_book
from app.services.library_service import list_user_libraries, is_library_member
from app.services.user_service import get_user_by_id
from app.utils.helpers import make_slug, normalize_author_name
import logging

logger = logging.getLogger(__name__)


async def get_all_books(
    db: AsyncSession, skip: int = Query(0, ge=0), limit: int = Query(100, le=1000)
):
    result = await db.scalars(
        select(Book).offset(skip).limit(limit).order_by(Book.created_at.desc())
    )
    return result.all()


async def get_book_by_id(db: AsyncSession, book_id: int):
    return await db.get(Book, book_id)


async def get_username_by_book(db: AsyncSession, book_id: int):
    """
    Получаем информацию по пользователю, который добавил книгу
    """
    book = await get_book_by_id(db, book_id)
    if not book:
        return None
    user = await db.get(User, book.user_id)
    return user


async def create_book(
    db: AsyncSession, data: BookCreate, user_id: int, library_id: int
):
    try:
        # Проверяем, что библиотека существует
        library = await db.get(Library, library_id)
        if not library:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='f"Library {library_id} not found"')

        membership = await is_library_member(db, user_id, library_id)
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this library")

        slug = make_slug(f"{data.author}-{data.title}", unique=True)
        book = Book(
            author=data.author,
            title=data.title,
            description=data.description,
            genre=data.genre,
            color=data.color,
            lib_address=data.lib_address,
            room=data.room,
            shelf=data.shelf,
            user_id=user_id,
            library_id=library_id,
            slug=slug,
        )
        db.add(book)
        await db.commit()
        await db.refresh(book)
        logger.info(f"✅ Book created: {book.id} - {book.title}")
        logger.info(f"✅ Книга создана с ID: {book.id}")

        await update_user_book_status(db, user_id, book.id, data.read_status)
        logger.info(f"✅ Статус обновлен {data.read_status}")
        return book

    except HTTPException:
        raise
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"❌ IntegrityError creating book: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Book with this slug already exists")
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error creating book: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create book"
        )


async def update_book(db: AsyncSession, user_id: int, book_id: int, data: BookUpdate):
    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        return None
    book = (
        await db.execute(
            select(Book).where((Book.id == book_id) & (Book.user_id == user_id))
        )
    ).scalar_one_or_none()
    if not book:
        return None
    await db.execute(
        update(Book)
        .where((Book.id == book_id) & (Book.user_id == user_id))
        .values(
            author=data.author,
            title=data.title,
            description=data.description,
            genre=data.genre,
            color=data.color,
            lib_address=data.lib_address,
            room=data.room,
            shelf=data.shelf,
        )
    )
    read_status = await update_user_book_status(db, user_id, book_id, data.read_status)
    await db.commit()
    return True


async def get_popular_genres(db: AsyncSession, limit: int = 20):
    """
    Получить список популярных жанров.
    :return list[dict]: [{"genre": "Fantasy", "count": 15}, ...]
    """
    result = await db.execute(
        select(Book.genre, func.count(Book.id).label("count"))
        .where(Book.genre.isnot(None))
        .group_by(Book.genre)
        .order_by(func.count(Book.id).desc())
        .limit(limit)
    )

    genres = []
    for row in result:
        genres.append({"genre": row.genre, "count": row.count})

    return genres


async def delete_book(db: AsyncSession, book_id: int):
    book = await get_book_by_id(db, book_id)
    if not book:
        return None
    await db.delete(book)
    await db.commit()
    return True


async def get_popular_authors(db: AsyncSession, limit: int = 50):
    """
    Получаем список авторов из существующих книг
    :return: list[dict]: [{"author": "Leo Tolstoy", "count": 5}, ...]
    """
    result = await db.execute(
        select(Book.author, func.count(Book.id).label("count"))
        .where(Book.author.isnot(None))
        .group_by(Book.author)
        .order_by(func.count(Book.id).desc())
        .limit(limit)
    )

    authors = []
    for row in result:
        authors.append({"author": row.author, "count": row.count})
    return authors


async def get_all_accessible_books(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100):
    """
    Получить все книги из всех библиотек, где состоит пользователь.
    Включает как его собственные книги, так и книги других пользователей.

    Args:
        db: Сессия базы данных
        user_id: ID пользователя
        skip: Количество пропускаемых записей
        limit: Максимальное количество возвращаемых записей

    Returns:
        list[Book]: Список всех доступных книг
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь: {user_id} не был найден "
        )

    user_libraries = await list_user_libraries(db, user_id)
    if not user_libraries:
        return []

    library_ids = [library.id for library in user_libraries]

    books = await db.scalars(
        select(Book)
        .where(Book.library_id.in_(library_ids))
        .offset(skip)
        .limit(limit)
        .order_by(Book.created_at.desc())
    )
    return books.all()


async def get_all_accessible_book_with_status(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100):
    """Все доступные пользователю книги со статусами"""
    books = await get_all_accessible_books(db, user_id, skip, limit)
    books_with_status = await add_read_status_to_book(db, user_id, books)
    return books_with_status