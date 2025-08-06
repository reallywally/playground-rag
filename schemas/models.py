from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class SourceInfo(BaseModel):
    page: str
    source: str


class ChatData(BaseModel):
    answer: str
    sources: List[SourceInfo]
    query: str


class UploadResponse(BaseModel):
    message: str
    filename: str
    size: int
    chunks: int


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = datetime.now()


class ChatSession(BaseModel):
    session_id: str = str(uuid.uuid4())
    messages: List[ChatMessage] = []
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()