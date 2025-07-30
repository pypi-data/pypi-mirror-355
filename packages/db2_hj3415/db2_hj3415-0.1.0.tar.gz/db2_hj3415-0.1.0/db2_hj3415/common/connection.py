# MongoDB/Redis 연결
import os
from motor.motor_asyncio import AsyncIOMotorClient

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