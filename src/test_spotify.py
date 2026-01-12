import os
import httpx
import asyncio
import base64
from dotenv import load_dotenv

# 1. 載入金鑰
load_dotenv()
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    print("❌ 錯誤：找不到 Spotify ID 或 Secret，請檢查 .env 檔案！")
    exit(1)

async def get_access_token():
    """
    跟 Spotify 拿通行證 (Client Credentials Flow)
    這展示了標準的 OAuth 2.0 Server-to-Server 認證。
    """
    auth_url = "https://accounts.spotify.com/api/token"
    
    # Spotify 要求把 ID:Secret 做 Base64 編碼
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()

    headers = {
        "Authorization": f"Basic {b64_auth_str}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}

    async with httpx.AsyncClient() as client:
        resp = await client.post(auth_url, headers=headers, data=data)
        
        if resp.status_code != 200:
            print(f"❌ 認證失敗: {resp.text}")
            return None
        
        return resp.json()["access_token"]

async def search_track(query: str):
    """
    搜尋歌曲並回傳詳細資料
    """
    print(f"🔑 正在取得 Access Token...")
    token = await get_access_token()
    if not token:
        return

    print(f"🔍 正在搜尋歌曲: {query} ...")
    search_url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "q": query,
        "type": "track",
        "limit": 1,  # 我們只要第一名
        "market": "TW" # 限定台灣區 (避免搜到奇怪的版本)
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(search_url, headers=headers, params=params)
        
        if resp.status_code != 200:
            print(f"❌ 搜尋失敗: {resp.text}")
            return

        data = resp.json()
        tracks = data.get("tracks", {}).get("items", [])

        if not tracks:
            print("❌ 找不到這首歌！")
            return

        # 抓出我們需要的資料 (Evidence)
        track = tracks[0]
        name = track["name"]
        artist = track["artists"][0]["name"]
        album_img = track["album"]["images"][0]["url"] # 大圖
        preview_url = track["preview_url"]
        spotify_url = track["external_urls"]["spotify"]

        print("\n=== 🎵 找到證據了！ ===")
        print(f"歌名: {name}")
        print(f"歌手: {artist}")
        print(f"封面: {album_img}")
        print(f"試聽連結: {preview_url}")
        print(f"完整連結: {spotify_url}")
        
        if preview_url:
            print("\n✅ 成功取得 30秒 試聽檔！(這就是我們要給使用者聽的)")
        else:
            print("\n⚠️ 注意：這首歌 Spotify 沒提供試聽檔 (版權限制)，前端可能要改顯示完整連結。")

# 執行非同步程式
if __name__ == "__main__":
    # 測試搜尋一首發燒金曲
    asyncio.run(search_track("Hotel California - Live"))
