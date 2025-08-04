from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class ChatRequest(BaseModel):
    message: str


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