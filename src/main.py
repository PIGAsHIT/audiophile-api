import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.database import engine, Base

# 匯入拆分出去的 Routers
from src.routers import auth, recommendation, user

# 初始化 DB (Postgres)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Audiophile Proof API (Refactored)")

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
