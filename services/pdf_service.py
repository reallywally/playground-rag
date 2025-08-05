import os
import re
from typing import Optional, Dict
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from schemas.models import UploadResponse
from config.settings import settings


class PDFService:
    def __init__(self):
        self.vectorstores: Dict[str, Chroma] = {}
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
    
    async def process_pdf(self, file_path: str, filename: str, file_size: int) -> UploadResponse:
        """PDF 파일을 처리하고 벡터스토어를 생성합니다."""
        try:
            # 파일명에서 확장자 제거하고 안전한 컬렉션명 생성
            collection_name = self._get_collection_name(filename)
            
            # 이미 처리된 파일인지 확인
            if collection_name in self.vectorstores:
                return UploadResponse(
                    message=f"PDF '{filename}' already exists in database",
                    filename=filename,
                    size=file_size,
                    chunks=0
                )
            
            # PDF 문서 로드 및 분할
            loader = PyMuPDFLoader(file_path)
            docs = loader.load()

            # 텍스트 분할
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP
            )
            split_documents = text_splitter.split_documents(docs)

            # 벡터스토어 구축 (파일명별 컬렉션)
            vectorstore = Chroma.from_documents(
                documents=split_documents,
                embedding=self.embeddings,
                persist_directory="./chroma_db",
                collection_name=collection_name
            )
            
            # 메모리에 저장
            self.vectorstores[collection_name] = vectorstore

            return UploadResponse(
                message="PDF uploaded and processed successfully",
                filename=filename,
                size=file_size,
                chunks=len(split_documents)
            )
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
    
    def get_vectorstore(self, filename: str = None) -> Optional[Chroma]:
        """벡터스토어를 반환합니다. filename이 없으면 첫 번째 벡터스토어를 반환합니다."""
        if filename:
            collection_name = self._get_collection_name(filename)
            return self.vectorstores.get(collection_name)
        
        # filename이 없으면 첫 번째 벡터스토어 반환
        if self.vectorstores:
            return next(iter(self.vectorstores.values()))
        return None
    
    def has_vectorstore(self, filename: str = None) -> bool:
        """벡터스토어가 존재하는지 확인합니다."""
        if filename:
            collection_name = self._get_collection_name(filename)
            return collection_name in self.vectorstores
        return len(self.vectorstores) > 0
    
    def get_all_collections(self) -> list:
        """모든 컬렉션 이름을 반환합니다."""
        return list(self.vectorstores.keys())
    
    def load_existing_collections(self):
        """기존 컬렉션들을 로드합니다."""
        chroma_dir = "./chroma_db"
        if os.path.exists(chroma_dir):
            try:
                # Chroma 디렉토리에서 기존 컬렉션들을 찾아서 로드
                for item in os.listdir(chroma_dir):
                    if os.path.isdir(os.path.join(chroma_dir, item)) and item != "chroma.sqlite3":
                        try:
                            vectorstore = Chroma(
                                persist_directory=chroma_dir,
                                embedding_function=self.embeddings,
                                collection_name=item
                            )
                            self.vectorstores[item] = vectorstore
                        except Exception:
                            continue
            except Exception:
                pass
    
    def _get_collection_name(self, filename: str) -> str:
        """파일명을 안전한 컬렉션명으로 변환합니다."""
        # 확장자 제거
        name = os.path.splitext(filename)[0]
        # 특수문자를 언더스코어로 변경
        name = re.sub(r'[^a-zA-Z0-9가-힣]', '_', name)
        # 연속된 언더스코어 제거
        name = re.sub(r'_+', '_', name)
        # 앞뒤 언더스코어 제거
        name = name.strip('_')
        # 빈 문자열이면 기본값 사용
        if not name:
            name = "default"
        return name


# 전역 PDF 서비스 인스턴스
pdf_service = PDFService()
# 시작 시 기존 컬렉션들 로드
pdf_service.load_existing_collections()