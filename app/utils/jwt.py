from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def create_access_token(
    subject: str | int, expires_delta: timedelta | None = None
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": str(subject),
        "exp": datetime.now(timezone.utc) + expires_delta,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    logger.debug(f"✅ JWT created: sub={subject}, exp={to_encode['exp']}")
    logger.debug(f"Token: {token[:30]}...")

    return token


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
