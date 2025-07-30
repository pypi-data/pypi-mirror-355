from dotenv import load_dotenv
import os
import uvicorn

# 환경변수(.env) 로드
load_dotenv()

if __name__ == "__main__":
    # 포트는 .env에서 설정하거나 기본값 8080 사용
    port = int(os.getenv("PORT", 8080))
    # server.py에 정의된 FastAPI 앱을 가리킵니다
    uvicorn.run(
        "server:app",  # "<모듈명>:<FastAPI 인스턴스 이름>"
        host="127.0.0.1",
        port=port,
        reload=True,
    )
