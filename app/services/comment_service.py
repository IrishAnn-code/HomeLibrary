from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload

from app.models import Comments
from app.services.book_service import get_book_by_id

import logging

logger = logging.getLogger(__name__)


async def create_comment(db: AsyncSession, book_id: int, user_id: int, message: str):
    """Сохранение комментария в БД"""
    comment = Comments(book_id=book_id, user_id=user_id, message=message)
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


async def get_comments_by_book(
    db: AsyncSession, book_id: int, skip: int = 0, limit: int = 50
):
    """Получить все комментарии по книге"""
    try:
        comments = await db.scalars(
            select(Comments)
            .options(joinedload(Comments.user))
            .where(Comments.book_id == book_id)
            .order_by(Comments.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(comments)
    except Exception as e:
        logger.error(f"Ошибка получения комментариев: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при загрузке комментариев",
        )


async def edit_comment(db: AsyncSession, comment_id: int, user_id: int, message: str):
    """Редактировать комментарий"""
    try:
        comment = await db.get(Comments, comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Комментарий не найден"
            )

        if comment.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав"
            )

        comment.message = message
        await db.commit()
        return comment

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка редактирования комментария: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при загрузке комментариев",
        )


async def delete_comment(db: AsyncSession, comment_id: int, user_id: int):
    """Удалить комментарий"""
    try:
        comment = await db.get(Comments, comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="Комментарий не найден")

        if comment.user_id != user_id:
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        await db.delete(comment)
        await db.commit()
        return True

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка удаления комментария: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении",
        )
