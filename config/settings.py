import os
from typing import List
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()


class Settings:
    # API 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS 설정
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    ALLOW_CREDENTIALS: bool = True
    ALLOW_METHODS: List[str] = ["*"]
    ALLOW_HEADERS: List[str] = ["*"]
    
    # OpenAI 설정
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # 파일 업로드 설정
    MAX_FILE_SIZE: int = 20 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "uploads"
    ALLOWED_CONTENT_TYPES: List[str] = ["application/pdf"]
    
    # 텍스트 분할 설정
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # 검색 설정
    SEARCH_K: int = 3  # 상위 검색 결과 개수
    
    # LLM 설정
    MODEL_NAME: str = "gpt-4.1-mini"
    TEMPERATURE: float = 0.1


settings = Settings()