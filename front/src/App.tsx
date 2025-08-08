import { useState, useRef } from 'react';
import PdfUploader from '@/components/PdfUploader';
import ChatBot from '@/components/ChatBot';
import SessionList from '@/components/SessionList';
import type { SessionListRef } from '@/components/SessionList';

function App() {
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const sessionListRef = useRef<SessionListRef>(null);

  const handleSessionSelect = (sessionId: string) => {
    setCurrentSessionId(sessionId);
  };

  const handleNewSession = () => {
    setCurrentSessionId(null);
  };

  const handleSessionUpdate = (sessionId: string, lastMessage: string) => {
    // SessionList 컴포넌트의 updateSessionList 함수 호출
    if (sessionListRef.current) {
      sessionListRef.current.updateSessionList(sessionId, lastMessage);
    }
    
    // 현재 세션 ID가 없다면 새로 설정
    if (!currentSessionId) {
      setCurrentSessionId(sessionId);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-center text-gray-800 mb-8">
          PDF 업로더 & 챗봇
        </h1>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-150px)]">
          <div className="lg:col-span-1">
            <div className="space-y-4 h-full">
              <div className="h-1/2">
                <PdfUploader />
              </div>
              <div className="h-1/2">
                <SessionList
                  ref={sessionListRef}
                  currentSessionId={currentSessionId}
                  onSessionSelect={handleSessionSelect}
                  onNewSession={handleNewSession}
                />
              </div>
            </div>
          </div>
          <div className="lg:col-span-2">
            <ChatBot 
              sessionId={currentSessionId}
              onSessionUpdate={handleSessionUpdate}
              onNewSession={handleNewSession}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App
