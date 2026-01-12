# tests/test_main.py
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.database import Base, get_db

# 1. 建立一個「假」的記憶體資料庫 (SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite://" # 使用記憶體模式

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. 建立資料表 (在記憶體裡)
Base.metadata.create_all(bind=engine)

# 3. 覆蓋依賴 (Dependency Override)
# 告訴 FastAPI：測試的時候，不要用真的 get_db，改用這個 override_get_db
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# --- 開始寫測試 ---

def test_read_root():
    """測試首頁是否活著"""
    response = client.get("/")
    assert response.status_code == 200

def test_register_user():
    """測試註冊功能 (使用記憶體資料庫)"""
    response = client.post(
        "/register",
        json={"email": "test_ci@example.com", "password": "password123"},
    )
    # 第一次註冊應該成功 (200)
    assert response.status_code == 200
    assert response.json()["email"] == "test_ci@example.com"

def test_register_duplicate_user():
    """測試重複註冊 (應該失敗)"""
    # 先註冊一次
    client.post(
        "/register",
        json={"email": "duplicate@example.com", "password": "password123"},
    )
    # 再註冊一次
    response = client.post(
        "/register",
        json={"email": "duplicate@example.com", "password": "password123"},
    )
    # 應該要報錯 400
    assert response.status_code == 400