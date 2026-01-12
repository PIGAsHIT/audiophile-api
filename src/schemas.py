from pydantic import BaseModel
from typing import List, Optional

# 輸入維持不變
class HeadphoneRequest(BaseModel):
    brand: str
    model: str

# ✅ 輸出大升級：加入硬體規格 (Specs)
class TrackRecommendation(BaseModel):
    # 1. 硬體規格 (Specs)
    form_factor: str      # 例如：入耳式 (IEM)
    connection: str       # 例如：有線 (3.5mm/4.4mm)
    release_year: str     # 例如：2019
    price_range: str      # 例如：$1,600 USD
    driver_config: str    # 例如：1圈2鐵 (1DD + 2BA)
    
    # 2. 聲音特色 (Sound)
    sound_features: List[str] # 例如：["大編制", "高頻延伸"]
    
    # 3. 推薦歌曲 (Song)
    title: str
    artist: str
    
    # 4. 專業總結 (Summary)
    comment: str          # 專業客觀的評價
    
    # 系統欄位 (Spotify)
    cover_url: str
    spotify_url: str
    track_id: str
    preview_url: Optional[str] = None