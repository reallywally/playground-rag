import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import uuid

from services.chat_service import ChatService, chat_service
from schemas.models import ChatRequest, ChatResponse, ChatData, SourceInfo, ChatSession, ChatMessage
from config.settings import settings


class TestChatService:
    def setup_method(self):
        self.chat_service = ChatService()
    
    def test_init(self):
        assert self.chat_service.model_name == settings.MODEL_NAME
        assert self.chat_service.temperature == settings.TEMPERATURE
        assert self.chat_service.sessions == {}
    
    def test_get_or_create_session_new_session(self):
        session = self.chat_service.get_or_create_session()
        
        assert session.session_id is not None
        assert isinstance(session.session_id, str)
        assert session.messages == []
        assert session.session_id in self.chat_service.sessions
    
    def test_get_or_create_session_with_session_id(self):
        session_id = "test-session-123"
        session = self.chat_service.get_or_create_session(session_id)
        
        assert session.session_id == session_id
        assert session.messages == []
        assert session_id in self.chat_service.sessions
    
    def test_get_or_create_session_existing_session(self):
        session_id = "existing-session"
        first_session = self.chat_service.get_or_create_session(session_id)
        second_session = self.chat_service.get_or_create_session(session_id)
        
        assert first_session is second_session
        assert len(self.chat_service.sessions) == 1
    
    def test_add_message_to_session_new_session(self):
        session_id = "test-session"
        content = "안녕하세요"
        role = "user"
        
        self.chat_service.add_message_to_session(session_id, role, content)
        
        session = self.chat_service.sessions[session_id]
        assert len(session.messages) == 1
        assert session.messages[0].role == role
        assert session.messages[0].content == content
        assert isinstance(session.messages[0].timestamp, datetime)
    
    def test_add_message_to_session_existing_session(self):
        session_id = "test-session"
        self.chat_service.get_or_create_session(session_id)
        
        self.chat_service.add_message_to_session(session_id, "user", "첫 번째 메시지")
        self.chat_service.add_message_to_session(session_id, "assistant", "첫 번째 답변")
        self.chat_service.add_message_to_session(session_id, "user", "두 번째 메시지")
        
        session = self.chat_service.sessions[session_id]
        assert len(session.messages) == 3
        assert session.messages[0].content == "첫 번째 메시지"
        assert session.messages[1].content == "첫 번째 답변"
        assert session.messages[2].content == "두 번째 메시지"
    
    def test_get_conversation_context_no_session(self):
        context = self.chat_service.get_conversation_context("non-existent")
        assert context == ""
    
    def test_get_conversation_context_empty_session(self):
        session_id = "empty-session"
        self.chat_service.get_or_create_session(session_id)
        
        context = self.chat_service.get_conversation_context(session_id)
        assert context == ""
    
    def test_get_conversation_context_with_messages(self):
        session_id = "test-session"
        self.chat_service.add_message_to_session(session_id, "user", "안녕하세요")
        self.chat_service.add_message_to_session(session_id, "assistant", "안녕하세요! 무엇을 도와드릴까요?")
        
        context = self.chat_service.get_conversation_context(session_id)
        
        expected = "이전 대화:\n사용자: 안녕하세요\n어시스턴트: 안녕하세요! 무엇을 도와드릴까요?\n\n현재 질문: "
        assert context == expected
    
    def test_get_conversation_context_limit_messages(self):
        session_id = "test-session"
        
        for i in range(10):
            self.chat_service.add_message_to_session(session_id, "user", f"메시지 {i}")
            self.chat_service.add_message_to_session(session_id, "assistant", f"답변 {i}")
        
        context = self.chat_service.get_conversation_context(session_id)
        
        assert "메시지 0" not in context
        assert "메시지 1" not in context
        assert "메시지 2" not in context
        assert "메시지 3" not in context
        assert "메시지 6" in context
        assert "메시지 9" in context
    
    def test_extract_source_info_empty(self):
        source_info = self.chat_service._extract_source_info([])
        assert source_info == []
    
    def test_extract_source_info_with_documents(self):
        mock_doc1 = Mock()
        mock_doc1.metadata = {"page": 1, "source": "document1.pdf"}
        
        mock_doc2 = Mock()
        mock_doc2.metadata = {"page": "2", "source": "document2.pdf"}
        
        mock_doc3 = Mock()
        mock_doc3.metadata = {"page": None, "source": "document3.pdf"}
        
        source_info = self.chat_service._extract_source_info([mock_doc1, mock_doc2, mock_doc3])
        
        assert len(source_info) == 3
        assert source_info[0].page == "1"
        assert source_info[0].source == "document1.pdf"
        assert source_info[1].page == "2"
        assert source_info[1].source == "document2.pdf"
        assert source_info[2].page == "Unknown"
        assert source_info[2].source == "document3.pdf"
    
    @patch('services.chat_service.pdf_service')
    async def test_process_chat_no_vectorstore(self, mock_pdf_service):
        mock_pdf_service.has_vectorstore.return_value = False
        
        request = ChatRequest(message="안녕하세요")
        response = await self.chat_service.process_chat(request)
        
        assert response.success is False
        assert "PDF 파일을 먼저 업로드해주세요" in response.message
        assert "No PDF uploaded" in response.error
    
    @patch('services.chat_service.pdf_service')
    @patch('services.chat_service.ChatOpenAI')
    @patch('services.chat_service.RetrievalQA')
    async def test_process_chat_success(self, mock_retrieval_qa, mock_chat_openai, mock_pdf_service):
        mock_pdf_service.has_vectorstore.return_value = True
        
        mock_vectorstore = Mock()
        mock_retriever = Mock()
        mock_vectorstore.as_retriever.return_value = mock_retriever
        mock_pdf_service.get_vectorstore.return_value = mock_vectorstore
        
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        
        mock_qa_chain = Mock()
        mock_retrieval_qa.from_chain_type.return_value = mock_qa_chain
        
        mock_result = {
            "result": "테스트 답변입니다",
            "source_documents": [
                Mock(metadata={"page": 1, "source": "test.pdf"})
            ]
        }
        mock_qa_chain.invoke.return_value = mock_result
        
        request = ChatRequest(message="테스트 질문입니다", session_id="test-session")
        response = await self.chat_service.process_chat(request)
        
        assert response.success is True
        assert response.message == "답변이 생성되었습니다."
        assert response.data["answer"] == "테스트 답변입니다"
        assert response.data["query"] == "테스트 질문입니다"
        assert response.data["session_id"] == "test-session"
        assert len(response.data["sources"]) == 1
        
        session = self.chat_service.sessions["test-session"]
        assert len(session.messages) == 2
        assert session.messages[0].role == "user"
        assert session.messages[0].content == "테스트 질문입니다"
        assert session.messages[1].role == "assistant"
        assert session.messages[1].content == "테스트 답변입니다"
    
    @patch('services.chat_service.pdf_service')
    @patch('services.chat_service.ChatOpenAI')
    async def test_process_chat_exception(self, mock_chat_openai, mock_pdf_service):
        mock_pdf_service.has_vectorstore.return_value = True
        mock_pdf_service.get_vectorstore.side_effect = Exception("테스트 에러")
        
        request = ChatRequest(message="테스트 질문")
        response = await self.chat_service.process_chat(request)
        
        assert response.success is False
        assert "답변 생성 중 오류가 발생했습니다" in response.message
        assert "테스트 에러" in response.error
    
    @patch('services.chat_service.pdf_service')
    @patch('services.chat_service.ChatOpenAI')
    @patch('services.chat_service.RetrievalQA')
    async def test_process_chat_with_conversation_context(self, mock_retrieval_qa, mock_chat_openai, mock_pdf_service):
        mock_pdf_service.has_vectorstore.return_value = True
        
        mock_vectorstore = Mock()
        mock_retriever = Mock()
        mock_vectorstore.as_retriever.return_value = mock_retriever
        mock_pdf_service.get_vectorstore.return_value = mock_vectorstore
        
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        
        mock_qa_chain = Mock()
        mock_retrieval_qa.from_chain_type.return_value = mock_qa_chain
        
        mock_result = {
            "result": "두 번째 답변입니다",
            "source_documents": []
        }
        mock_qa_chain.invoke.return_value = mock_result
        
        session_id = "context-test-session"
        self.chat_service.add_message_to_session(session_id, "user", "첫 번째 질문")
        self.chat_service.add_message_to_session(session_id, "assistant", "첫 번째 답변")
        
        request = ChatRequest(message="두 번째 질문", session_id=session_id)
        response = await self.chat_service.process_chat(request)
        
        assert response.success is True
        
        called_query = mock_qa_chain.invoke.call_args[0][0]["query"]
        assert "이전 대화:" in called_query
        assert "첫 번째 질문" in called_query
        assert "첫 번째 답변" in called_query
        assert "두 번째 질문" in called_query
    
    @patch('services.chat_service.pdf_service')
    @patch('services.chat_service.ChatOpenAI')
    @patch('services.chat_service.RetrievalQA')
    @patch('uuid.uuid4')
    async def test_process_chat_auto_generate_session_id(self, mock_uuid, mock_retrieval_qa, mock_chat_openai, mock_pdf_service):
        mock_uuid.return_value = "auto-generated-session-id"
        mock_pdf_service.has_vectorstore.return_value = True
        
        mock_vectorstore = Mock()
        mock_retriever = Mock()
        mock_vectorstore.as_retriever.return_value = mock_retriever
        mock_pdf_service.get_vectorstore.return_value = mock_vectorstore
        
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        
        mock_qa_chain = Mock()
        mock_retrieval_qa.from_chain_type.return_value = mock_qa_chain
        
        mock_result = {
            "result": "자동 생성된 세션 답변",
            "source_documents": []
        }
        mock_qa_chain.invoke.return_value = mock_result
        
        request = ChatRequest(message="세션 ID 없는 질문")
        response = await self.chat_service.process_chat(request)
        
        assert response.success is True
        assert response.data["session_id"] == "auto-generated-session-id"
        assert "auto-generated-session-id" in self.chat_service.sessions


def test_global_chat_service_instance():
    assert chat_service is not None
    assert isinstance(chat_service, ChatService)