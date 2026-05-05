"""
Handles two concerns:
Password hashing / verification (bcrypt via passlib)
JWT creation / decoding (HS256 via python-jose)
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from core.config import settings
from core.redis import is_token_blocked

# Bcrypt context
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Return the bcrypt hash of a plain-text password."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*. Timing-safe."""
    return _pwd_context.verify(plain, hashed)


# Token payload schema 
class TokenPayload(BaseModel):
    sub: str # user UUID as string
    jti: str # JWT ID — used for Redis blocklisting on logout
    exp: datetime
    type: str # "access" | "refresh"


# Token creation 
def _create_token(user_id: UUID, token_type: str, expires_delta: timedelta) -> str:
    jti = str(uuid4())
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": str(user_id),
        "jti": jti,
        "exp": expire,
        "type": token_type,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: UUID) -> str:
    return _create_token(
        user_id,
        token_type="access",
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: UUID) -> str:
    return _create_token(
        user_id,
        token_type="refresh",
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


# Token decoding 
async def decode_token(token: str) -> TokenPayload:
    """
    Decode and validate a JWT.

    Raises:
        ValueError: on expired, malformed, or blocklisted tokens.
    """
    try:
        raw = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as exc:
        raise ValueError(f"Invalid token: {exc}") from exc

    payload = TokenPayload(**raw)

    if await is_token_blocked(payload.jti):
        raise ValueError("Token has been revoked.")

    return payload