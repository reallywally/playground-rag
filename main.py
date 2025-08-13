from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging
import traceback

from config.settings import settings
from schemas.models import ChatRequest, ChatResponse, ChatSession
from services.pdf_service import pdf_service
from services.chat_service import chat_service

app = FastAPI()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=settings.ALLOW_CREDENTIALS,
    allow_methods=settings.ALLOW_METHODS,
    allow_headers=settings.ALLOW_HEADERS,
)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    # PDF 파일 타입 검증
    if file.content_type not in settings.ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # 파일 크기 제한
    contents = await file.read()
    if len(contents) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Max size is {settings.MAX_FILE_SIZE // (1024*1024)}MB")

    # uploads 디렉토리 생성
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # 파일 저장
    file_path = f"{settings.UPLOAD_DIR}/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(contents)

    try:
        result = await pdf_service.process_pdf(file_path, file.filename, len(contents))
        return result.dict()
    except Exception as e:
        logger.error(f"PDF 업로드 실패 - 파일: {file.filename}, 크기: {len(contents)} bytes")
        logger.error(f"에러 위치: {traceback.format_exc()}")
        
        # 업로드된 파일 정리
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"실패한 파일 삭제: {file_path}")
            except Exception as cleanup_error:
                logger.error(f"파일 삭제 실패: {cleanup_error}")
        
        raise HTTPException(status_code=500, detail=f"PDF 처리 중 오류가 발생했습니다: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    return await chat_service.process_chat(request)


@app.post("/sessions", response_model=ChatSession)
async def create_session():
    """새로운 채팅 세션을 생성합니다."""
    session = chat_service.get_or_create_session()
    return session


@app.get("/sessions/{session_id}", response_model=ChatSession)
async def get_session(session_id: str):
    """특정 세션 정보를 가져옵니다."""
    if session_id not in chat_service.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return chat_service.sessions[session_id]


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """세션을 삭제합니다."""
    if session_id not in chat_service.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    del chat_service.sessions[session_id]
    return {"message": "Session deleted successfully"}


if __name__ == "__main__":
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
