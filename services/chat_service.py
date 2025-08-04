from typing import List
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from schemas.models import ChatRequest, ChatResponse, ChatData, SourceInfo
from services.pdf_service import pdf_service
from config.settings import settings


class ChatService:
    def __init__(self):
        self.model_name = settings.MODEL_NAME
        self.temperature = settings.TEMPERATURE
    
    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """채팅 요청을 처리하고 응답을 생성합니다."""
        # 벡터스토어가 없으면 에러 반환
        if not pdf_service.has_vectorstore():
            return ChatResponse(
                success=False,
                message="PDF 파일을 먼저 업로드해주세요.",
                error="No PDF uploaded. Please upload a PDF first."
            )

        try:
            # LLM 모델 초기화
            llm = ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                openai_api_key=settings.OPENAI_API_KEY
            )

            # 검색기 생성
            vectorstore = pdf_service.get_vectorstore()
            retriever = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": settings.SEARCH_K}
            )

            # RetrievalQA 체인 생성
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True
            )

            # 질문에 대한 답변 생성
            result = qa_chain.invoke({"query": request.message})

            # 소스 문서 정보 추출
            source_info = self._extract_source_info(result.get("source_documents", []))

            chat_data = ChatData(
                answer=result["result"],
                sources=source_info,
                query=request.message
            )

            return ChatResponse(
                success=True,
                message="답변이 생성되었습니다.",
                data=chat_data.dict()
            )

        except Exception as e:
            return ChatResponse(
                success=False,
                message="답변 생성 중 오류가 발생했습니다.",
                error=str(e)
            )
    
    def _extract_source_info(self, source_documents) -> List[SourceInfo]:
        """소스 문서에서 정보를 추출합니다."""
        source_info = []
        for doc in source_documents:
            page = doc.metadata.get("page", "Unknown")
            source = doc.metadata.get("source", "Unknown")
            
            # page가 숫자인 경우 문자열로 변환
            if isinstance(page, int):
                page = str(page)
            elif page is None:
                page = "Unknown"
                
            source_info.append(SourceInfo(
                page=str(page),
                source=str(source)
            ))
        return source_info


# 전역 채팅 서비스 인스턴스
chat_service = ChatService()