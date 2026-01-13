import os
import base64
import pytest
import httpx
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

AUTH_URL = "https://accounts.spotify.com/api/token"
SEARCH_URL = "https://api.spotify.com/v1/search"

@pytest.mark.skipif(not CLIENT_ID or not CLIENT_SECRET, reason="Spotify Credentials missing")
@pytest.mark.asyncio
async def test_spotify_search_flow():
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()

    headers_auth = {
        "Authorization": f"Basic {b64_auth_str}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data_auth = {"grant_type": "client_credentials"}

    async with httpx.AsyncClient() as client:
        # 1. 取得 Access Token
        token_resp = await client.post(AUTH_URL, headers=headers_auth, data=data_auth)
        assert token_resp.status_code == 200
        
        access_token = token_resp.json().get("access_token")
        assert access_token is not None

        # 2. 執行歌曲搜尋
        headers_search = {"Authorization": f"Bearer {access_token}"}
        params_search = {
            "q": "Hotel California - Live",
            "type": "track",
            "limit": 1,
            "market": "TW"
        }

        search_resp = await client.get(SEARCH_URL, headers=headers_search, params=params_search)
        assert search_resp.status_code == 200
        
        results = search_resp.json().get("tracks", {}).get("items", [])
        assert len(results) > 0
        
        track = results[0]
        assert "name" in track
        assert track["artists"][0]["name"] is not None
        
        print(f"\n[Spotify Test Success] Found: {track['name']} - {track['external_urls']['spotify']}")