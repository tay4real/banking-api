import redis.asyncio as aioredis
from app.config import get_settings

settings = get_settings()

redis_client = aioredis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True
)


async def blacklist_token(jti: str, expires_in_seconds: int) -> None:
    """Store a jti in Redis with TTL matching token expiry."""
    await redis_client.setex(
        name=f"blacklist:{jti}",
        time=expires_in_seconds,
        value="1"
    )


async def is_token_blacklisted(jti: str) -> bool:
    """Returns True if the token has been blacklisted."""
    result = await redis_client.get(f"blacklist:{jti}")
    return result is not None