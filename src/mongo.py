import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# 資料庫連線設定
MONGO_USER = os.getenv("MONGO_USER", "admin")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "secret_mongo")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_URL = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin"

# 建立連線
client = AsyncIOMotorClient(MONGO_URL)
db = client.audiophile_db

# 定義好所有的 Collection，讓大家來這裡拿
logs_collection = db.logs
favorites_collection = db.favorites

async def log_request(event_type: str, data: dict, user_id: str = None):
    try:
        log_entry = {
            "event": event_type,
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "data": data
        }
        await logs_collection.insert_one(log_entry)
    except Exception as e:
        print(f"❌ [Log Error] {e}")