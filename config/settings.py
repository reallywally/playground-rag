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
    
    # Semantic Chunking 설정
    USE_SEMANTIC_CHUNKING: bool = False  # 임시로 비활성화
    SEMANTIC_CHUNK_MIN_SIZE: int = 100  # 최소 청크 크기
    SEMANTIC_CHUNK_MAX_SIZE: int = 1500  # 최대 청크 크기
    SENTENCE_SIMILARITY_THRESHOLD: float = 0.7  # 문장 유사도 임계값
    
    # 문서 전처리 설정
    REMOVE_HEADERS_FOOTERS: bool = True
    EXTRACT_TABLES: bool = True
    EXTRACT_IMAGES: bool = True
    MIN_TEXT_LENGTH: int = 50  # 최소 텍스트 길이
    
    # 검색 설정
    SEARCH_K: int = 3  # 상위 검색 결과 개수
    HYBRID_SEARCH_WEIGHT: float = 0.7  # 유사도 검색 가중치 (1-weight는 키워드 검색)
    
    # 임베딩 설정
    EMBEDDING_MODEL: str = "text-embedding-3-large"  # OpenAI 임베딩 모델
    EMBEDDING_DIMENSIONS: int = 3072  # text-embedding-3-large 차원수
    
    # LLM 설정
    MODEL_NAME: str = "gpt-4.1-mini"
    TEMPERATURE: float = 0.1


settings = Settings()