import pytest
from sqlalchemy import create_all
from src.db.postgres import engine, Base
from src.models.user import User # 確保 model 有被載入

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # 🚀 在 CI 測試開始前，自動建立所有資料表
    Base.metadata.create_all(bind=engine)
    yield
    