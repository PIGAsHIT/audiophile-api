# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 設定環境變數，讓 Python 輸出更即時
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安裝系統依賴 (Postgres 的驅動 psycopg2 有時需要這些)
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# 安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製程式碼
COPY . .

# 開放 8000 port
EXPOSE 8000

# 啟動指令 (開發模式用 reload)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]