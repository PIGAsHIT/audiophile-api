import os
import pytest
from google import genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TEST_MODEL = "gemini-2.5-flash" 

@pytest.mark.skipif(not GEMINI_API_KEY, reason="Skipping: GEMINI_API_KEY not found")
def test_gemini_connection():
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Sennheiser HD800S 的經典音場測試
    headphone_model = "Sennheiser HD800S"
    test_prompt = f"Explain the soundstage of {headphone_model} in one short sentence."

    try:
        response = client.models.generate_content(
            model=TEST_MODEL, 
            contents=test_prompt
        )

        # 驗證回傳物件的結構與內容
        assert response and response.text, "API returned an empty response"
        assert len(response.text.strip()) > 0
        
        print(f"\n[Gemini Test Success] Response: {response.text.strip()}")

    except Exception as e:
        pytest.fail(f"Gemini API connection failed: {e}")