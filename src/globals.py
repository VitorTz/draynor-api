import redis.asyncio as redis
from dotenv import load_dotenv
import os


load_dotenv()


redis_client = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)


def globals_get_redis_client():
    global redis_client
    return redis_client