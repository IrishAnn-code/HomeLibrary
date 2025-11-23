from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
import logging

from app.models import Book, User
from app.schemas.user import UserUpdate
from app.services.book_status_service import add_read_status_to_book
from app.utils.hashing import hash_password, verify_password


logger = logging.getLogger(__name__)


async def get_all_users(db: AsyncSession, skip: int = 0, limit: int = 100):
    """
    Получить список всех пользователей с пагинацией.

    Args:
        db: Сессия базы данных
        skip: Количество пропускаемых записей
        limit: Максимальное количество возвращаемых записей

    Returns:
        list[User]: Список пользователей
    """
    result = await db.scalars(
        select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
    )
    return result.all()


async def get_user_by_username(db: AsyncSession, username: str):
    """
    Найти пользователя по username

    Args:
        db: Сессия базы данных
        username: Имя пользователя

    Returns:
        User | None: Объект пользователя или None
    """
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int):
    """
    Получить пользователя по ID.

    Args:
        db: Сессия базы данных
        user_id: ID пользователя

    Returns:
        User | None: Объект пользователя или None
    """
    return await db.get(User, user_id)


async def create_user(db: AsyncSession, username: str, email: str, password: str):
    """
    Создать нового пользователя.

    Args:
        db: Сессия базы данных
        username: Имя пользователя (уникальное)
        email: Email (уникальный)
        password: Пароль в открытом виде (будет захеширован)

    Returns:
        User: Созданный пользователь

    Raises:
        HTTPException 409: Пользователь с таким username или email уже существует
        HTTPException 500: Ошибка создания пользователя
    """
    try:
        existing_user = await db.scalar(
            select(User).where((User.email == email) | (User.username == username))
        )
        if existing_user:
            logger.warning(f"⚠️ Attempt to create duplicate user: {username} / {email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this username or email already exists",
            )

        user = User(
            username=username, email=email, password_hash=hash_password(password)
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"✅ User created: {user.id} - {user.username}")
        return user

    except HTTPException:
        await db.rollback()
        raise  # Пробрасываем HTTPException дальше

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"❌ IntegrityError creating user {username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this username or email already exists",
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Unexpected error creating user {username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> User | None:
    """
    Проверить учетные данные пользователя.
    Args:
        db: Сессия базы данных
        username: Имя пользователя
        password: Пароль в открытом виде

    Returns:
        User | None: Объект пользователя, если учетные данные верны, иначе None
    """
    user = await db.scalar(select(User).where(User.username == username))

    if not user:
        logger.warning(f"Login attempt for non-existent user: {username}")
        return None

    if not verify_password(password, user.password_hash):
        logger.warning(f"Invalid password for user: {username}")
        return None

    logger.info(f"✅ User authenticated: {user.id} - {user.username}")
    return user


async def get_user_books(
    db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
):
    """
    Получить все книги добавленные пользователем с пагинацией.
    Args:
        db: Сессия базы данных
        user_id: ID пользователя
        skip: Количество пропускаемых записей
        limit: Максимальное количество возвращаемых записей

    Returns:
       list[Book]: Список книг пользователя

    Raises:
        HTTPException 404: Пользователь не найден
    """
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
        )

    books = await db.scalars(
        select(Book)
        .where(Book.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .order_by(Book.created_at.desc())
    )

    return books.all()


async def get_user_books_with_status(db: AsyncSession, user_id: int):
    """Получить книги добавленные пользователем со статусами чтения"""
    books = await get_user_books(db, user_id)
    books_with_status = await add_read_status_to_book(db, user_id, books)
    return books_with_status


async def update_user(
    db: AsyncSession, user_id: int, password: str, user_update: UserUpdate
):
    """
    Обновить данные пользователя.

    Args:
        db: Сессия базы данных
        user_id: ID пользователя
        password: Текущий пароль (для подтверждения)
        user_update: Новые данные пользователя

    Returns:
        User: Обновленный пользователь

    Raises:
        HTTPException 404: Пользователь не найден
        HTTPException 401: Неверный текущий пароль
        HTTPException 409: Email уже используется
        HTTPException 500: Ошибка обновления
    """
    try:
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found",
            )
        if not verify_password(password, user.password_hash):
            logger.warning(f"Invalid current password for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid current password",
            )
        data = {}
        if user_update.firstname is not None:
            data["firstname"] = user_update.firstname
        if user_update.lastname is not None:
            data["lastname"] = user_update.lastname
        if user_update.email is not None:
            data["email"] = user_update.email
        if user_update.password is not None:
            data["password_hash"] = hash_password(user_update.password)

        if data:
            await db.execute(update(User).where(User.id == user_id).values(**data))
            await db.commit()
            await db.refresh(user)
            logger.info(f"✅ User updated: {user.id} - {user.username}")
        return user

    except HTTPException:
        await db.rollback()
        raise

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"❌ IntegrityError updating user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already exists"
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error updating user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )


async def delete_user(db: AsyncSession, user_id: int):
    """
    Удалить пользователя.

    Args:
        db: Сессия базы данных
        user_id: ID пользователя

    Returns:
        bool: True если удаление успешно

    Raises:
        HTTPException 404: Пользователь не найден
        HTTPException 500: Ошибка удаления
    """
    try:
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found",
            )
        await db.delete(user)
        await db.commit()
        logger.info(f"✅ User deleted: {user_id}")
        return True
    except HTTPException:
        await db.rollback()
        raise

    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error deleting user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user",
        )
