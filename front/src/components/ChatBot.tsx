import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
  sources?: Array<{
    page: string;
    source: string;
  }>;
}

interface ChatResponse {
  success: boolean;
  message: string;
  data?: {
    answer: string;
    sources: Array<{
      page: string;
      source: string;
    }>;
    query: string;
    session_id?: string;
  };
  error?: string;
}

interface ChatSession {
  session_id: string;
  messages: Array<{
    role: string;
    content: string;
    timestamp: string;
  }>;
  created_at: string;
  updated_at: string;
}

const ChatBot: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  // 컴포넌트 마운트 시 새 세션 생성
  useEffect(() => {
    createNewSession();
  }, []);

  const createNewSession = async () => {
    try {
      const response = await fetch('http://localhost:8000/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const session: ChatSession = await response.json();
        setSessionId(session.session_id);
        setMessages([{
          id: '1',
          text: '안녕하세요! PDF와 관련하여 궁금한 점이 있으시면 언제든 물어보세요. 대화를 이어가며 더 자세한 질문도 하실 수 있습니다.',
          isUser: false,
          timestamp: new Date(),
        }]);
      }
    } catch (error) {
      console.error('세션 생성 실패:', error);
      // 세션 생성에 실패해도 기본 메시지는 표시
      setMessages([{
        id: '1',
        text: '안녕하세요! PDF와 관련하여 궁금한 점이 있으시면 언제든 물어보세요.',
        isUser: false,
        timestamp: new Date(),
      }]);
    }
  };

  const startNewConversation = () => {
    setMessages([]);
    setSessionId(null);
    createNewSession();
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputValue,
      isUser: true,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    const messageToSend = inputValue;
    setInputValue('');
    setIsLoading(true);

    try {
      const requestBody = sessionId 
        ? { message: messageToSend, session_id: sessionId }
        : { message: messageToSend };
        
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error('서버 응답 오류');
      }

      const data: ChatResponse = await response.json();
      console.log(data)
      
      if (data.success && data.data) {
        // 세션 ID 업데이트 (새 세션이 생성된 경우)
        if (data.data.session_id && !sessionId) {
          setSessionId(data.data.session_id);
        }
        
        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: data.data.answer,
          isUser: false,
          timestamp: new Date(),
          sources: data.data.sources
        };
        setMessages(prev => [...prev, botMessage]);
      } else {
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: data.message || data.error || '응답을 받지 못했습니다.',
          isUser: false,
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: '죄송합니다. 서버와의 연결에 문제가 발생했습니다.',
        isUser: false,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };


  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            🤖 챗봇
          </CardTitle>
          <div className="flex items-center gap-2">
            {sessionId && (
              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                세션: {sessionId.slice(0, 8)}...
              </span>
            )}
            <Button
              onClick={startNewConversation}
              variant="outline"
              size="sm"
              className="text-xs"
            >
              🔄 새 대화
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col p-4">
        <ScrollArea className="flex-1 mb-4" ref={scrollAreaRef}>
          <div className="space-y-4 pr-2">
            {messages.length === 0 && !isLoading && (
              <div className="flex justify-center items-center h-full">
                <div className="text-center text-gray-500">
                  <p className="text-sm">새로운 대화를 시작해보세요!</p>
                  <p className="text-xs mt-1">PDF를 업로드한 후 질문하실 수 있습니다.</p>
                </div>
              </div>
            )}
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-3 ${
                    message.isUser
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-800'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.text}</p>
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-gray-300">
                      <p className="text-xs opacity-70 mb-1">참고 문서:</p>
                      {message.sources.map((source, index) => (
                        <p key={index} className="text-xs opacity-70">
                          페이지 {source.page}
                        </p>
                      ))}
                    </div>
                  )}
                  <p className="text-xs opacity-70 mt-1">
                    {message.timestamp.toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-200 text-gray-800 rounded-lg p-3">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
        <div className="flex gap-2">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="메시지를 입력하세요..."
            onKeyPress={handleKeyPress}
            disabled={isLoading}
          />
          <Button 
            onClick={handleSendMessage} 
            disabled={!inputValue.trim() || isLoading}
            size="sm"
          >
            📤
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default ChatBot;