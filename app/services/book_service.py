from http.client import HTTPException

from fastapi import Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update

from app.core.exceptions import not_found, forbidden, conflict, server_error
from app.models import Book, User, Library
from app.schemas.book import BookCreate, BookUpdate
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


async def create_book(db: AsyncSession, data: BookCreate, user_id: int, library_id: int):
    try:
        # Проверяем, что библиотека существует
        library = await db.get(Library, library_id)
        if not library:
            raise not_found('f"Library {library_id} not found"')

        # Проверяем, что пользователь состоит в библиотеке
        from app.models.user_library import UserLibrary
        membership = await db.scalar(select(UserLibrary).where(
                (UserLibrary.user_id == user_id) &
                (UserLibrary.library_id == library_id)))
        if not membership:
            raise forbidden("You are not a member of this library")

        slug = make_slug(f"{data.author}-{data.title}", unique=True)
        book = Book(
            author=data.author,
            title=data.title,
            description=data.description,
            genre=data.genre,
            color=data.color,
            read_status=data.read_status,
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
        return book
    except HTTPException:
        raise
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"❌ IntegrityError creating book: {e}")
        raise conflict("Book with this slug already exists")
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error creating book: {e}")
        raise server_error("Failed to create book")


async def update_book(
    db: AsyncSession, user_id: int, book_id: int, update_b: BookUpdate
):
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
            author=update_b.author,
            title=update_b.title,
            read_status=update_b.read_status,
            lib_address=update_b.lib_address,
            room=update_b.room,
            shelf=update_b.shelf,
        )
    )
    await db.commit()
    return True


async def delete_book(db: AsyncSession, book_id: int):
    book = await get_book_by_id(db, book_id)
    if not book:
        return None
    await db.delete(book)
    await db.commit()
    return True
