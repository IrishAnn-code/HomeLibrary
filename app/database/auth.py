from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, ExpiredSignatureError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import authorization_error
from app.database.db_depends import get_db
from app.models import User
from app.utils.jwt import decode_access_token


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
        authorization_error("Not authenticated")
    try:
        data = decode_access_token(token)
        user_id = int(data.get("sub"))
        if not user_id:
            raise ValueError("Missing subject in token")
        user_id = int(user_id)

    except ExpiredSignatureError:
        authorization_error("Token has expired")
    except JWTError:
        authorization_error("Could not validate credentials")
    except (ValueError, TypeError) as e:
        authorization_error(f"Invalid token format: {str(e)}")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        authorization_error("User not found")

    return user
