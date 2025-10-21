"""
Redis configuration and connection management.
"""

import redis
import json
from typing import Any, Optional
from config.settings import get_settings

settings = get_settings()


class RedisClient:
    """Redis client wrapper."""

    def __init__(self):
        self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        value = self.client.get(key)
        if value:
            return json.loads(value)
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis."""
        ttl = ttl or settings.REDIS_TTL
        return self.client.setex(key, ttl, json.dumps(value))

    def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        return self.client.delete(key) > 0

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        return self.client.exists(key) > 0


def get_redis() -> RedisClient:
    """Get Redis client instance."""
    return RedisClient()
