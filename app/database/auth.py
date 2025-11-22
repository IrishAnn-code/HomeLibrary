from fastapi import Depends, Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, ExpiredSignatureError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.database.db_depends import get_db
from app.models import User
from app.utils.jwt import decode_access_token

logger = logging.getLogger(__name__)
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")
security = HTTPBearer(auto_error=False)


async def get_token_from_request(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str | None:
    """
    Извлечь JWT токен из запроса.

    Проверяет в следующем порядке:
    1. Authorization header: "Bearer <token>"
    2. Cookie: "access_token"
    """

    # 1. Пробуем Authorization header
    if credentials:
        logger.debug(
            f"Token from Authorization header: {credentials.credentials[:20]}..."
        )
        return credentials.credentials

    # 2. Пробуем cookie
    cookie_token = request.cookies.get("access_token")
    logger.error(f"🔍 DEBUG: cookie_token = {cookie_token}")
    if cookie_token:
        logger.debug(f"✅ Token from cookie: {cookie_token[:20]}...")
        return cookie_token

    logger.debug("⚠️ No token found in request")
    return None


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: str | None = Depends(get_token_from_request),
) -> User:
    """
    Получить текущего авторизованного пользователя.

    Извлекает токен из Authorization header или cookie,
    декодирует его и достает пользователя из БД.
    """
    if not token:
        logger.warning("❌ Authentication failed: no token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        data = decode_access_token(token)
        user_id = data.get("sub")

        if not user_id:
            raise ValueError("Missing 'sub' in token")

        user_id = int(user_id)
        logger.debug(f"✅ Token decoded successfully: user_id={user_id}")

    except ExpiredSignatureError:
        logger.warning("❌ Token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        logger.error(f"❌ JWT error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (ValueError, TypeError) as e:
        logger.error(f"❌ Token format error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"❌ User {user_id} not found in database")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.info(f"✅ User authenticated: {user.id} - {user.username}")
    return user


async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: str | None = Depends(get_token_from_request),
) -> User | None:
    """
    Получить текущего пользователя (опционально).
    Не выбрасывает исключение если токен отсутствует.
    """
    if not token:
        return None

    try:
        return await get_current_user(request, db, token)
    except HTTPException:
        return None
