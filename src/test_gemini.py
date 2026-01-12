import os
from google import genai
from dotenv import load_dotenv

# 1. 載入 .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ 錯誤：找不到 GEMINI_API_KEY，請檢查 .env 檔案！")
    exit(1)

# 2. 初始化 Client (新版寫法)
client = genai.Client(api_key=api_key)

# 3. 準備發燒友 Prompt
headphone_model = "Sennheiser HD800S"
features = "超大音場, 解析力強"

prompt = f"""
你是一位嚴苛的耳機發燒友。
使用者有一支 {headphone_model}，他覺得這支耳機聽起來跟路邊攤差不多。
這支耳機的特點是：{features}。

請推薦 1 首最能展現這些特點的「發燒測試曲」，並用簡短、犀利、帶點優越感的語氣，
告訴他要聽這首歌的哪個細節（例如幾分幾秒的什麼聲音），來證明他錯了。
請直接給出歌名和歌手，以及那一針見血的評論。
"""

print(f"🤖 正在詢問 Gemini (使用新版 SDK)...")

# 4. 發送請求 (新版模型名稱)
try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    print("\n=== Gemini 的毒舌評論 ===")
    print(response.text)
    print("========================")

except Exception as e:
    print(f"\n❌ 連線失敗: {e}")
    # 印出更多除錯資訊
    if "404" in str(e):
        print("💡 提示：請確認你的 API Key 是否有效，或者嘗試使用 'gemini-1.5-pro'")