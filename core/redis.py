from redis.asyncio import Redis, from_url

from core.config import settings

# Module-level client — initialised on startup, closed on shutdown
_redis_client: Redis | None = None


async def init_redis() -> None:
    """Call once during app startup."""
    global _redis_client
    _redis_client = await from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )


async def close_redis() -> None:
    """Call once during app shutdown."""
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None


def get_redis() -> Redis:
    """FastAPI dependency — yields the shared Redis client."""
    if _redis_client is None:
        raise RuntimeError("Redis has not been initialised. Call init_redis() first.")
    return _redis_client


# Convenience helpers 

async def blocklist_token(jti: str, ttl_seconds: int) -> None:
    """Add a JWT ID to the Redis blocklist with an automatic expiry."""
    client = get_redis()
    await client.setex(f"blocklist:{jti}", ttl_seconds, "1")


async def is_token_blocked(jti: str) -> bool:
    client = get_redis()
    return await client.exists(f"blocklist:{jti}") == 1