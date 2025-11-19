from fastapi import Depends, Request, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, ExpiredSignatureError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.exceptions import authorization_error
from app.database.db_depends import get_db
from app.models import User
from app.utils.jwt import decode_access_token

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")


async def get_token_from_request(request: Request, token: str | None = Depends(oauth2_scheme)) -> str | None:
    # First try Authorization header (oauth2_scheme)
    if token:
        return token
    # Fallback to cookie
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        # cookie may be stored as "Bearer <token>" or token itself.
        if cookie_token.startswith("Bearer "):
            return cookie_token.split(" ", 1)[1]
        return cookie_token
    return None


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: str | None = Depends(get_token_from_request),
) -> User:
    """
        Получить текущего авторизованного пользователя.
        Проверяет токен из:
        1. Authorization header (Bearer token)
        2. Cookie (access_token)
        Raises:
            HTTPException 401: Если токен невалиден или пользователь не найден
    """
    if not token:
        logger.warning("No token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    try:
        data = decode_access_token(token)
        user_id = int(data.get("sub"))

        logger.debug(f"Token decoded: user_id={user_id}")

    except ExpiredSignatureError:
        logger.warning("Token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except JWTError as e:
        logger.error(f"JWT error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    except (ValueError, TypeError) as e:
        logger.error(f"Token format error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token format"
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"User {user_id} not found in database")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    logger.info(f"✅ User authenticated: {user.id} - {user.username}")
    return user
