from db2_hj3415.common import connection
import json

async def get_or_set_cache(key, ttl, fetch_func, force_refresh=False):
    redis = await connection.get_redis()
    if not force_refresh:
        cached = await redis.get(key)
        if cached:
            return json.loads(cached)

    result = await fetch_func()
    if result:
        await redis.setex(key, ttl, json.dumps(result))
    return result


