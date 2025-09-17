import os

import redis.asyncio

redis_client = redis.asyncio.StrictRedis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
