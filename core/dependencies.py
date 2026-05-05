"""
Reusable FastAPI dependencies injected into route handlers.
"""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import TokenPayload, decode_token

bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> UUID:
    """
    Validates the Bearer JWT and returns the authenticated user's UUID.

    Usage:
        @router.get("/me")
        async def get_me(user_id: UUID = Depends(get_current_user_id)):
            ...
    """
    try:
        payload: TokenPayload = await decode_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh tokens cannot be used for API access.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UUID(payload.sub)


# bundle db + user_id together for routes that need both
async def get_current_user_and_db(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> tuple[UUID, AsyncSession]:
    return user_id, db