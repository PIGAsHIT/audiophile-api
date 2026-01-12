import os
import httpx
import base64
import json
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext

# ✅ 匯入我們寫好的模組 (確保 src/database.py, src/models.py, src/schemas.py 都存在)
from src.database import engine, get_db, Base
from src.models import User
from src.schemas import HeadphoneRequest, TrackRecommendation
from src.cache import get_cached_recommendation, set_cached_recommendation

# 1. 初始化與建立資料表
load_dotenv()
# 這行會自動在 Postgres 建立 users 表格 (如果不存在)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Audiophile Proof API")

# 設定靜態檔案
os.makedirs("src/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# 2. 安全性設定 (JWT)
SECRET_KEY = os.getenv("SECRET_KEY", "secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- 資料庫連線 (MongoDB & Gemini & Spotify) ---
MONGO_URL = os.getenv("MONGO_URL")
mongo_client = AsyncIOMotorClient(MONGO_URL)
db_mongo = mongo_client.audiophile_db
favorites_collection = db_mongo.favorites

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=GEMINI_KEY)
SPOTIFY_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# --- 輔助函式 (Auth: 密碼與 Token) ---

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# --- 輔助函式 (Spotify) ---
async def get_spotify_token():
    auth_str = f"{SPOTIFY_ID}:{SPOTIFY_SECRET}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    async with httpx.AsyncClient() as client:
        resp = await client.post("https://accounts.spotify.com/api/token", headers={"Authorization": f"Basic {b64_auth}"}, data={"grant_type": "client_credentials"})
        return resp.json()["access_token"]

async def search_spotify(query: str, token: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://api.spotify.com/v1/search", headers={"Authorization": f"Bearer {token}"}, params={"q": query, "type": "track", "limit": 1, "market": "TW"})
        items = resp.json().get("tracks", {}).get("items", [])
        return items[0] if items else None

# --- API Endpoints (路由) ---

@app.get("/")
def read_root():
    return FileResponse('src/static/index.html')

# ✅ 註冊 API (寫入 Postgres)
class UserCreate(BaseModel):
    email: str
    password: str

@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    # 檢查是否重複註冊
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 建立新使用者
    hashed_password = get_password_hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"email": new_user.email, "msg": "User created successfully"}

# ✅ 登入 API (驗證並發放 JWT)
@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# ✅ 測試驗證 API (只有登入者能看)
@app.get("/users/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    return {"email": current_user.email, "id": current_user.id}

# ✅ 核心功能：AI 推薦 (整合你最新的詳細 Prompt)
# 這裡暫時不鎖權限 (沒加 Depends)，讓首頁能直接用。如果你想鎖，加上 dependencies=[Depends(get_current_user)] 即可
@app.post("/recommend", response_model=TrackRecommendation)
async def get_recommendation(request: HeadphoneRequest):
    print(f"🎧 專業分析請求：{request.brand} {request.model}")

    # 先查 Redis 快取
    cached_data = get_cached_recommendation(request.brand, request.model)
    if cached_data:
        # 如果有快取，直接回傳 (不用煩勞 Gemini 和 Spotify)
        return TrackRecommendation(**cached_data)
    
    # 如果沒快取，才開始跑原本的 AI 邏輯
    print("無紀錄 ... 正在呼叫 Gemini + Spotify...")

    # 使用你指定的詳細 Prompt
    prompt = f"""
    你是一位資深音響工程師與耳機百科全書。
    使用者正在查詢 {request.brand} {request.model}。
    請精準提取這支耳機的規格與特性，並推薦一首測試曲。
    
    請嚴格回傳符合以下 JSON 格式的純文字 (不要 Markdown)：
    {{
        "specs": {{
            "form_factor": "佩戴形式 (例如：入耳式 IEM, 開放式耳罩)",
            "connection": "連線方式 (例如：有線, 藍牙 5.2)",
            "year": "上市年份 (估計)",
            "price": "參考價位 (美金或台幣)",
            "driver": "單體配置 (例如：1動圈+2動鐵, 40mm 鍍鈹單體)"
        }},
        "sound_features": ["特色1", "特色2", "特色3"],
        "song_query": "歌名 - 歌手",
        "summary": "一段約 50 字的專業總結。客觀描述其聲音走向（例如：暖聲、監聽向、V型調音），適合聽什麼類型的音樂。語氣要專業、沈穩，不要毒舌。"
    }}
    """
    
    try:
        # 呼叫 Gemini
        ai_resp = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        
        # 解析 AI 回傳的 JSON
        ai_data = json.loads(ai_resp.text)
        specs = ai_data.get("specs", {})
        
        print(f"分析完成：{ai_data.get('song_query')}")

    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        # Fallback (萬一 AI 掛了)
        specs = {"form_factor": "未知", "connection": "未知", "year": "N/A", "price": "N/A", "driver": "未知"}
        ai_data = {
            "sound_features": ["解析度", "音場"], 
            "song_query": "Hotel California - Eagles",
            "summary": "暫時無法取得 AI 分析數據，請稍後再試。"
        }

    # 找 Spotify
    try:
        token = await get_spotify_token()
        track_data = await search_spotify(ai_data["song_query"], token)
    except Exception as e:
        print(f"❌ Spotify Error: {e}")
        track_data = None

    if not track_data:
        # 如果 Spotify 找不到，丟出 404，或者你可以選擇回傳一個預設物件
        raise HTTPException(status_code=404, detail="Song not found on Spotify")

    result = {
        "form_factor": specs.get("form_factor", "未知"),
        "connection": specs.get("connection", "未知"),
        "release_year": specs.get("year", "未知"),
        "price_range": specs.get("price", "未知"),
        "driver_config": specs.get("driver", "未知"),
        "sound_features": ai_data.get("sound_features", []),
        "title": track_data["name"],
        "artist": track_data["artists"][0]["name"],
        "comment": ai_data.get("summary", "無評論"),
        "cover_url": track_data["album"]["images"][0]["url"],
        "spotify_url": track_data["external_urls"]["spotify"],
        "track_id": track_data["id"],
        "preview_url": track_data["preview_url"]
    }

    # 寫入 Redis 快取 (關鍵一步！)
    set_cached_recommendation(request.brand, request.model, result)

    # 回傳 Pydantic 物件
    return TrackRecommendation(**result)

# ✅ 收藏 API (存入 MongoDB，且必須登入)
class FavoriteRequest(BaseModel):
    track_id: str
    title: str
    artist: str
    cover_url: str
    spotify_url: str

@app.post("/favorites")
async def add_favorite(fav: FavoriteRequest, current_user: User = Depends(get_current_user)):
    # 檢查是否已收藏
    existing = await favorites_collection.find_one({
        "user_id": str(current_user.id), 
        "track_id": fav.track_id
    })
    
    if existing:
        return {"message": "Already favorited", "status": "exists"}

    # 寫入 MongoDB
    fav_data = fav.model_dump()
    fav_data["user_id"] = str(current_user.id) # 強制寫入真實 User ID
    fav_data["added_at"] = datetime.utcnow()
    
    await favorites_collection.insert_one(fav_data)
    return {"message": "Added to favorites", "status": "added"}

# ✅ 檢查收藏狀態 API (必須登入)
@app.get("/favorites/check/{track_id}")
async def check_favorite(track_id: str, current_user: User = Depends(get_current_user)):
    existing = await favorites_collection.find_one({
        "user_id": str(current_user.id), 
        "track_id": track_id
    })
    return {"is_favorited": bool(existing)}