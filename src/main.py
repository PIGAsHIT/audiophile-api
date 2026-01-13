import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware  # 1. 新增 CORS 模組
from src.database import engine, Base
# 匯入拆分出去的 Routers
from prometheus_fastapi_instrumentator import Instrumentator
from src.routers import auth, recommendation, user

# 初始化 DB (Postgres)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Audiophile Proof API (Refactored)")

# --- 2. 新增 CORS 設定 (建議加入，避免前後端分離時報錯) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允許所有來源連線 (開發階段方便)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. 新增 Prometheus 監控 (關鍵步驟) ---
#這行會自動掛載 /metrics 路由
Instrumentator().instrument(app).expose(app)

# 掛載靜態檔案 (前端)
os.makedirs("src/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# 註冊 Routers (把功能掛上去)
app.include_router(auth.router, tags=["Authentication"])
app.include_router(recommendation.router, tags=["Recommendation"])
app.include_router(user.router, tags=["User Data"])

@app.get("/")
def read_root():
    return FileResponse('src/static/index.html')

@app.get("/health")
def health_check():
    return {"status": "ok"}