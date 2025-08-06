from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.schema import HumanMessage, AIMessage
from schemas.models import ChatRequest, ChatResponse, ChatData, SourceInfo, ChatSession, ChatMessage
from services.pdf_service import pdf_service
from config.settings import settings
import uuid
from datetime import datetime


class ChatService:
    def __init__(self):
        self.model_name = settings.MODEL_NAME
        self.temperature = settings.TEMPERATURE
        self.sessions: Dict[str, ChatSession] = {}
    
    def get_or_create_session(self, session_id: str = None) -> ChatSession:
        """세션을 가져오거나 새로 생성합니다."""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        if session_id not in self.sessions:
            self.sessions[session_id] = ChatSession(session_id=session_id)
        
        return self.sessions[session_id]
    
    def add_message_to_session(self, session_id: str, role: str, content: str):
        """세션에 메시지를 추가합니다."""
        session = self.get_or_create_session(session_id)
        message = ChatMessage(role=role, content=content, timestamp=datetime.now())
        session.messages.append(message)
        session.updated_at = datetime.now()
    
    def get_conversation_context(self, session_id: str) -> str:
        """대화 히스토리를 컨텍스트로 만듭니다."""
        if session_id not in self.sessions:
            return ""
        
        session = self.sessions[session_id]
        if not session.messages:
            return ""
        
        context = "이전 대화:\n"
        for msg in session.messages[-6:]:  # 최근 6개 메시지만 포함
            role_name = "사용자" if msg.role == "user" else "어시스턴트"
            context += f"{role_name}: {msg.content}\n"
        context += "\n현재 질문: "
        return context
    
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
            # 세션 ID 생성 또는 기존 세션 사용
            session_id = request.session_id or str(uuid.uuid4())
            
            # 사용자 메시지를 세션에 추가
            self.add_message_to_session(session_id, "user", request.message)
            
            # 대화 컨텍스트 생성
            conversation_context = self.get_conversation_context(session_id)
            
            # 컨텍스트를 포함한 질문 생성
            contextual_query = conversation_context + request.message
            
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

            # 컨텍스트가 포함된 질문으로 답변 생성
            result = qa_chain.invoke({"query": contextual_query})
            
            # 어시스턴트 응답을 세션에 추가
            self.add_message_to_session(session_id, "assistant", result["result"])

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
                data={**chat_data.dict(), "session_id": session_id}
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