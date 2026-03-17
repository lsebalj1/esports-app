import json
import redis.asyncio as aioredis
from app.core.config import settings

_redis: aioredis.Redis | None = None

async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis

async def publish_event(channel: str, event_type: str, data: dict):
    r = await get_redis()
    message = json.dumps({"event_type": event_type, "data": data})
    await r.publish(channel, message)
    print(f"Published [{channel}] {event_type}")
