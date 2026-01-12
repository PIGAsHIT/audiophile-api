from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# 這裡會讀取 docker-compose.yml 傳進來的環境變數
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# 建立連線引擎
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 建立 Session 工廠
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 宣告基底
Base = declarative_base()

# 依賴注入用：確保每次請求都有獨立的 DB 連線，且用完會關閉
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()