from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from gpt_dynamodb_action.routes import router
import uvicorn

app = FastAPI(
    title="GPT DynamoDB Scanner API",
    version="1.0.0",
    servers=[
        {
            "url": "https://abc1234.ngrok-free.app",  # ⚠️ 여기에 실제 ngrok 주소 넣기
            "description": "Ngrok tunnel for local development"
        }
    ]
)

# GZip 압축 미들웨어 추가 (최소 크기 1000바이트, 압축 레벨 9)
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=9)

app.include_router(router)

def main():    
    uvicorn.run("gpt_dynamodb_action.main:app", host="0.0.0.0", port=8000, reload=True)