import uuid
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200

def test_user_registration_lifecycle():
    # 使用 UUID 確保每次測試 Email 絕對唯一
    unique_email = f"test_{uuid.uuid4()}@example.com"
    user_data = {"email": unique_email, "password": "password123"}

    # 1. 測試首次註冊 (預期成功)
    res_create = client.post("/register", json=user_data)
    assert res_create.status_code == 200
    assert res_create.json()["msg"] == "Created successfully"

    # 2. 測試重複註冊 (預期失敗)
    res_duplicate = client.post("/register", json=user_data)
    assert res_duplicate.status_code == 400
    assert res_duplicate.json()["detail"] == "Email already registered"

def test_invalid_registration():
    # 測試格式錯誤的請求
    invalid_data = {"email": "not-an-email"}
    response = client.post("/register", json=invalid_data)
    assert response.status_code == 422 # FastAPI 預設的驗證錯誤碼