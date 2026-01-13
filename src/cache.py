import os
import json
import redis
from dotenv import load_dotenv

load_dotenv()

# 讀取環境變數 (在 docker-compose 裡設為 redis://redis:6379/0)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 建立連線池 (Connection Pool) 
pool = redis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)
client = redis.Redis(connection_pool=pool)

# 設定快取存活時間 (TTL): 1小時 (3600秒)
# 這樣就算 Gemini 亂回答，1小時後也會自動刷新
CACHE_EXPIRE_SECONDS = 3600

def get_cached_recommendation(brand: str, model: str):
    """嘗試從 Redis 取得資料"""
    # 產生唯一的 Key，例如: "rec:Sony:WH-1000XM5"
    # 使用 lower() 避免大小寫視為不同查詢
    key = f"rec:{brand.lower()}:{model.lower()}"
    
    data = client.get(key)
    if data:
        print(f"⚡️ Cache HIT! 從 Redis 讀取: {key}")
        return json.loads(data) # 把字串變回 Dictionary
    return None

def set_cached_recommendation(brand: str, model: str, data: dict):
    """把資料寫入 Redis"""
    key = f"rec:{brand.lower()}:{model.lower()}"
    
    # 把 Dictionary 變成 JSON 字串存進去
    client.setex(key, CACHE_EXPIRE_SECONDS, json.dumps(data))
    print(f"💾 Cache SAVED! 已寫入 Redis: {key}")