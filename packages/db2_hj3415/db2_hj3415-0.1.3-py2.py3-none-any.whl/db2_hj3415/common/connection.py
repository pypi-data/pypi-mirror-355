# MongoDB/Redis 연결
import os
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
from redis.asyncio.client import Redis

# 싱글톤 몽고 클라이언트 정의
MONGO_URI = os.getenv("MONGO_ADDR", "mongodb://localhost:27017")
client: AsyncIOMotorClient = None

def get_mongo_client() -> AsyncIOMotorClient:
    global client
    if client is None:
        client = AsyncIOMotorClient(MONGO_URI)
    return client

def close_mongo_client():
    if client:
        client.close()


async def get_redis() -> Redis:
    client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    try:
        await client.ping()
        return client
    except Exception as e:
        print("Redis connection failed:", e)
        return None