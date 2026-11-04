import logging

from redis.asyncio.sentinel import Sentinel
from redis.exceptions import RedisError

from app.config import CACHE_TTL_SECONDS, REDIS_MASTER_NAME, REDIS_SENTINELS

log = logging.getLogger("flight.cache")

_sentinel = Sentinel(REDIS_SENTINELS, socket_timeout=0.5)
_redis = _sentinel.master_for(REDIS_MASTER_NAME, socket_timeout=0.5, decode_responses=True)


def flight_key(flight_id: int) -> str:
    return f"flight:{flight_id}"


def search_key(origin: str, destination: str, day: str | None) -> str:
    return f"search:{origin}:{destination}:{day or 'all'}"


async def get(key: str) -> str | None:
    try:
        value = await _redis.get(key)
    except RedisError as exc:
        log.warning("cache unavailable key=%s error=%s", key, exc)
        return None
    log.info("cache %s key=%s", "hit" if value is not None else "miss", key)
    return value


async def put(key: str, value: str) -> None:
    try:
        await _redis.set(key, value, ex=CACHE_TTL_SECONDS)
    except RedisError as exc:
        log.warning("cache write failed key=%s error=%s", key, exc)


async def invalidate_flight(flight_id: int, origin: str, destination: str) -> None:
    try:
        keys = [flight_key(flight_id)]
        async for key in _redis.scan_iter(match=f"search:{origin}:{destination}:*"):
            keys.append(key)
        await _redis.delete(*keys)
        log.info("cache invalidated keys=%s", keys)
    except RedisError as exc:
        log.warning("cache invalidation failed flight_id=%s error=%s", flight_id, exc)


async def close() -> None:
    await _redis.aclose()
