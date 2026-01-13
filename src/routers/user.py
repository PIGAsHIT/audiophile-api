from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from src.models import User
from src.services.auth_service import get_current_user
from src.mongo import favorites_collection, logs_collection
from src.mongo import db

router = APIRouter()
fav_col = db.favorites
log_col = db.logs

from pydantic import BaseModel
class FavoriteRequest(BaseModel):
    track_id: str
    title: str
    artist: str
    cover_url: str
    spotify_url: str

@router.post("/favorites")
async def add_favorite(fav: FavoriteRequest, user: User = Depends(get_current_user)):
    if await fav_col.find_one({"user_id": str(user.id), "track_id": fav.track_id}):
        return {"status": "exists"}
    data = fav.model_dump()
    data.update({"user_id": str(user.id), "added_at": datetime.utcnow()})
    await fav_col.insert_one(data)
    return {"status": "added"}

@router.get("/favorites")
async def get_favorites(user: User = Depends(get_current_user)):
    cursor = fav_col.find({"user_id": str(user.id)}).sort("added_at", -1)
    return [{"_id": str(doc["_id"]), **doc} async for doc in cursor] # 簡潔寫法

@router.delete("/favorites/{track_id}")
async def remove_favorite(track_id: str, user: User = Depends(get_current_user)):
    res = await fav_col.delete_one({"user_id": str(user.id), "track_id": track_id})
    if res.deleted_count == 0: raise HTTPException(404)
    return {"status": "removed"}

@router.get("/favorites/check/{track_id}")
async def check_fav(track_id: str, user: User = Depends(get_current_user)):
    exists = await fav_col.find_one({"user_id": str(user.id), "track_id": track_id})
    return {"is_favorited": bool(exists)}

@router.get("/history")
async def get_history(user: User = Depends(get_current_user)):
    cursor = log_col.find({"user_id": str(user.id), "event": "search_headphone"}).sort("timestamp", -1).limit(20)
    results = []
    async for doc in cursor:
        results.append({
            "brand": doc["data"].get("brand"),
            "model": doc["data"].get("model"),
            "result_song": doc["data"].get("result"),
            "timestamp": doc["timestamp"].strftime("%Y-%m-%d %H:%M")
        })
    return results