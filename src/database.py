from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# 1. 載入 .env 變數
load_dotenv()

# --- 關鍵修改 ---
# 不要直接讀 DATABASE_URL (因為 .env 裡沒有這一行了)
# 我們要用 f-string 把零散的變數組裝起來
SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
# ----------------

# 2. 建立 Engine
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)

# 3. 建立 Session 工廠
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. 宣告 Base
Base = declarative_base()

# 5. Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()