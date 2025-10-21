# test_redis_connection.py
from config.redis import get_redis

redis_client = get_redis()
redis_client.set("test_key", {"status": "ok"})
print(redis_client.get("test_key"))
