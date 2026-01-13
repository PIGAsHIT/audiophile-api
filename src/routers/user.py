from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from pydantic import BaseModel
from src.models import User
from src.services.auth_service import get_current_user
from src.mongo import db # 確保 src.mongo 裡有 export db

router = APIRouter()

# --- 統一在這裡定義 Collection ---
fav_col = db.favorites
log_col = db.logs

# --- Request Schema ---
class FavoriteRequest(BaseModel):
    track_id: str
    title: str
    artist: str
    cover_url: str
    spotify_url: str

# --- Endpoints ---

@router.post("/favorites")
async def add_favorite(fav: FavoriteRequest, user: User = Depends(get_current_user)):
    # 使用 str(user.id) 確保格式一致
    if await fav_col.find_one({"user_id": str(user.id), "track_id": fav.track_id}):
        return {"status": "exists"}
    
    data = fav.model_dump()
    data.update({"user_id": str(user.id), "added_at": datetime.utcnow()})
    
    await fav_col.insert_one(data)
    return {"status": "added"}

@router.get("/favorites")
async def get_favorites(user: User = Depends(get_current_user)):
    """取得收藏清單，並修復 ObjectId 問題"""
    # 直接用 fav_col
    cursor = fav_col.find({"user_id": str(user.id)})
    favorites = await cursor.to_list(length=100)

    # 手動轉 ObjectId
    for fav in favorites:
        if "_id" in fav:
            fav["_id"] = str(fav["_id"])
    return favorites

@router.delete("/favorites/{track_id}")
async def remove_favorite(track_id: str, user: User = Depends(get_current_user)):
    res = await fav_col.delete_one({"user_id": str(user.id), "track_id": track_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Favorite not found")
    return {"status": "removed"}

@router.get("/favorites/check/{track_id}")
async def check_fav(track_id: str, user: User = Depends(get_current_user)):
    exists = await fav_col.find_one({"user_id": str(user.id), "track_id": track_id})
    return {"is_favorited": bool(exists)}

@router.get("/history")
async def get_history(user: User = Depends(get_current_user)):
    # 這裡邏輯沒問題，保持原樣
    cursor = log_col.find({"user_id": str(user.id), "event": "search_headphone"}).sort("timestamp", -1).limit(20)
    results = []
    async for doc in cursor:
        results.append({
            "brand": doc["data"].get("brand"),
            "model": doc["data"].get("model"),
            "result_song": doc["data"].get("result"),
            # 加上防呆，避免萬一 timestamp 欄位不存在或格式錯誤
            "timestamp": doc.get("timestamp", datetime.utcnow()).strftime("%Y-%m-%d %H:%M")
        })
    return results