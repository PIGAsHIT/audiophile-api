import os
from google import genai
from dotenv import load_dotenv

# 1. 載入金鑰
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ 錯誤：找不到 GEMINI_API_KEY")
    exit(1)

client = genai.Client(api_key=api_key)

print("🔍 正在查詢您的 API Key 可用的模型清單...\n")

try:
    # 列出所有模型
    # 注意：這裡會列出很多，我們只抓出跟 generateContent 有關的
    for m in client.models.list():
        # 過濾出支援 "generateContent" (生成文字) 的模型
        if "generateContent" in m.supported_actions:
            print(f"✅ 可用模型: {m.name}")
            # 順便印出它的顯示名稱，確認版本
            print(f"   (ID: {m.name.split('/')[-1]})") 
            
except Exception as e:
    print(f"❌ 查詢失敗: {e}")