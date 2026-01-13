import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # 專案資訊
    PROJECT_NAME: str = "Audiophile Proof"
    VERSION: str = "1.0.0"

    # Security
    SECRET_KEY: str = "secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # External APIs
    GEMINI_API_KEY: Optional[str] = None
    SPOTIFY_CLIENT_ID: Optional[str] = None
    SPOTIFY_CLIENT_SECRET: Optional[str] = None
    SPOTIFY_REDIRECT_URI: str = "http://127.0.0.1:8000/callback"

    # Database (這部分最重要！)
    # Pydantic 會自動去抓系統中同名的環境變數 (不分大小寫)
    DB_HOST: str = "postgres-service" # 預設給 K8s 的 Service 名
    DB_PORT: int = 5432
    DATABASE_URL: Optional[str] = None
    
    MONGO_HOST: str = "mongodb-service"
    MONGO_URL: Optional[str] = None
    
    REDIS_HOST: str = "redis-service"

    class Config:
        # 如果有 .env 就讀，沒有就讀系統變數
        # 且系統環境變數的優先權大於 .env 檔案
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False 

settings = Settings()