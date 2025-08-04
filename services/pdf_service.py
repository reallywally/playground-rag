from typing import Optional
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from schemas.models import UploadResponse
from config.settings import settings


class PDFService:
    def __init__(self):
        self.vectorstore: Optional[FAISS] = None
    
    async def process_pdf(self, file_path: str, filename: str, file_size: int) -> UploadResponse:
        """PDF 파일을 처리하고 벡터스토어를 생성합니다."""
        try:
            # PDF 문서 로드 및 분할
            loader = PyMuPDFLoader(file_path)
            docs = loader.load()

            # 텍스트 분할
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP
            )
            split_documents = text_splitter.split_documents(docs)

            # 임베딩 생성 및 벡터스토어 구축
            embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
            self.vectorstore = FAISS.from_documents(
                documents=split_documents,
                embedding=embeddings
            )

            return UploadResponse(
                message="PDF uploaded and processed successfully",
                filename=filename,
                size=file_size,
                chunks=len(split_documents)
            )
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
    
    def get_vectorstore(self) -> Optional[FAISS]:
        """현재 벡터스토어를 반환합니다."""
        return self.vectorstore
    
    def has_vectorstore(self) -> bool:
        """벡터스토어가 존재하는지 확인합니다."""
        return self.vectorstore is not None


# 전역 PDF 서비스 인스턴스
pdf_service = PDFService()