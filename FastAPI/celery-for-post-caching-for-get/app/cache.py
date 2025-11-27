import json
import redis.asyncio as redis

REDIS_URL = "redis://redis:6379"


async def get_redis():
    # Create a Redis client using redis-py asyncio
    return redis.Redis.from_url(REDIS_URL, decode_responses=True)


async def get_cache(key: str):
    """
    Input:
        key (str): The cache key used to look up a value in Redis.
        >>> example: "items:limit=100"

    Output:
        - dict / list / str / int (depending on what was stored)
        - None if the key does not exist or Redis returns empty.

    Explanation:
        1) Opens a Redis connection via `get_redis()`.
        2) Reads the raw stored value using `redis.get(key)`.
        3) Redis stores values as bytes → if present, the code JSON-decodes it.
        4) If nothing exists (cache miss), returns None.
    """
    redis = await get_redis()
    data = await redis.get(key)
    if data:
        # convert => "[{\"id\":1,\"name\":\"Book\"},{\"id\":2,\"name\":\"Pen\"}]"
        # to => [ {"id": 1, "name": "Book"} , {"id": 2, "name": "Pen"} ]
        return json.loads(data)
    return None


async def set_cache(key: str, value, ttl: int = 60):
    """
    Store a Python object in Redis cache under a given key with TTL (seconds).

    Input:
      key: str → the Redis key to store the value
      value: any JSON-serializable Python object (dict, list, etc.)
      ttl: int → time-to-live in seconds (default: 60)

    Output:
      None → the value is stored in Redis

     Example:
     Suppose we previously cached the following:
     await set_cache(
         "items:limit=100",
         [{"id": 1, "name": "Item1"} , {"id": 2, "name": "Pen"}]
         )

     Calling:
     items = await get_cache("items:limit=100")
     items → [{"id": 1, "name": "Item1"} , {"id": 2, "name": "Pen"}]
    """
    redis = await get_redis()
    await redis.set(key, json.dumps(value), ex=ttl)


async def delete_cache(key: str):
    """
    Delete a key from Redis cache.

    Input:
      key: str → the Redis key to delete

    Output:
      None → the key is removed from Redis if it exists

    Example:
      await delete_cache("items:limit=100")
    """
    redis = await get_redis()
    await redis.delete(key)
