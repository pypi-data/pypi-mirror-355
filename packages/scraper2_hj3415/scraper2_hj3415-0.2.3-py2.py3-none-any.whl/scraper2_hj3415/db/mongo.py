from motor.motor_asyncio import AsyncIOMotorClient

# 싱글톤 몽고 클라이언트 정의
MONGO_URI = "mongodb://localhost:27017"
client: AsyncIOMotorClient = None

def get_client() -> AsyncIOMotorClient:
    global client
    if client is None:
        client = AsyncIOMotorClient(MONGO_URI)
    return client

def close_client():
    if client:
        client.close()