from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.models.enum import ReadStatus
from app.models.user_book_status import UserBookStatus


logger = logging.getLogger(__name__)


async def user_status(db: AsyncSession, user_id: int, book_id: int):
    """
     Получить статус книги для пользователя без обработчиков
    """
    status = await db.scalar(
        select(UserBookStatus)
        .where(
            (UserBookStatus.user_id == user_id) &
            (UserBookStatus.book_id == book_id)
        )
    )
    return status


async def get_user_book_status(
        db: AsyncSession,
        user_id: int,
        book_id: int
) -> str:
    """
    Получить статус книги для пользователя
    :return: 'not_read', 'reading' или 'read'
    """
    status = await user_status(db, user_id, book_id)
    return status.read_status if status else 'not_read'


async def update_user_book_status(
        db: AsyncSession,
        user_id: int,
        book_id: int,
        new_status: str
) -> None:
    """
    Обновить статус книги для пользователя
    """
    status = await user_status(db, user_id, book_id)
    if status:
        status.read_status = new_status
    else:
        status = UserBookStatus(
            user_id=user_id,
            book_id=book_id,
            read_status=new_status
        )
        db.add(status)
    await db.commit()


async def add_read_status_to_book(db: AsyncSession, user_id: int, books: Any):
    """Вспомогательная функция для добавления статусов"""
    books_with_status = []
    for book in books:
        status_value = await get_user_book_status(db, user_id,book.id)
        read_status = ReadStatus(status_value)
        books_with_status.append({
            "book": book,
            "read_status": read_status
        })
    return books_with_status

