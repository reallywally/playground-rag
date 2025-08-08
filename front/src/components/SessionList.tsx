import React, { useState, useEffect, forwardRef, useImperativeHandle } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';

interface SessionData {
  session_id: string;
  messages: Array<{
    role: string;
    content: string;
    timestamp: string;
  }>;
  created_at: string;
  updated_at: string;
}

interface SessionSummary {
  session_id: string;
  title: string;
  lastMessage: string;
  messageCount: number;
  updated_at: string;
}

interface SessionListProps {
  currentSessionId: string | null;
  onSessionSelect: (sessionId: string) => void;
  onNewSession: () => void;
}

interface SessionListRef {
  updateSessionList: (sessionId: string, lastMessage: string) => void;
  refreshSessions: () => void;
}

const SessionList = forwardRef<SessionListRef, SessionListProps>(({
  currentSessionId,
  onSessionSelect,
  onNewSession,
}, ref) => {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    setIsLoading(true);
    try {
      // 로컬 스토리지에서 세션 목록 가져오기
      const storedSessions = localStorage.getItem('chatSessions');
      if (storedSessions) {
        const sessionList = JSON.parse(storedSessions);
        setSessions(sessionList);
      }
    } catch (error) {
      console.error('세션 목록 로드 실패:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const updateSessionList = (sessionId: string, lastMessage: string) => {
    setSessions(prevSessions => {
      const existingIndex = prevSessions.findIndex(s => s.session_id === sessionId);
      let updatedSessions;

      if (existingIndex >= 0) {
        // 기존 세션 업데이트
        updatedSessions = [...prevSessions];
        const existingSession = updatedSessions[existingIndex];
        updatedSessions[existingIndex] = {
          ...existingSession,
          title: existingSession.messageCount === 0 
            ? (lastMessage.length > 30 ? lastMessage.substring(0, 30) + '...' : lastMessage)
            : existingSession.title, // 첫 메시지만 제목으로 사용
          lastMessage,
          messageCount: existingSession.messageCount + 1,
          updated_at: new Date().toISOString(),
        };
        
        // 최신 대화를 맨 위로 이동
        const updatedSession = updatedSessions.splice(existingIndex, 1)[0];
        updatedSessions.unshift(updatedSession);
      } else {
        // 새 세션 추가
        const newSession: SessionSummary = {
          session_id: sessionId,
          title: lastMessage.length > 30 ? lastMessage.substring(0, 30) + '...' : lastMessage,
          lastMessage,
          messageCount: 1,
          updated_at: new Date().toISOString(),
        };
        updatedSessions = [newSession, ...prevSessions];
      }

      // 로컬 스토리지에 저장
      localStorage.setItem('chatSessions', JSON.stringify(updatedSessions));
      return updatedSessions;
    });
  };

  const deleteSession = async (sessionId: string) => {
    if (!confirm('정말로 이 대화를 삭제하시겠습니까?')) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/sessions/${sessionId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        // 로컬 스토리지에서 세션 제거
        setSessions(prevSessions => {
          const updatedSessions = prevSessions.filter(s => s.session_id !== sessionId);
          localStorage.setItem('chatSessions', JSON.stringify(updatedSessions));
          return updatedSessions;
        });

        // 현재 선택된 세션이 삭제되는 경우 새 세션으로 전환
        if (currentSessionId === sessionId) {
          onNewSession();
        }
      } else {
        alert('세션 삭제에 실패했습니다. 다시 시도해주세요.');
      }
    } catch (error) {
      console.error('세션 삭제 실패:', error);
      alert('세션 삭제 중 오류가 발생했습니다.');
    }
  };

  // 외부에서 세션 업데이트를 위한 함수 노출
  useImperativeHandle(ref, () => ({
    updateSessionList,
    refreshSessions: loadSessions,
  }));

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 60) {
      return `${diffInMinutes}분 전`;
    } else if (diffInMinutes < 1440) {
      return `${Math.floor(diffInMinutes / 60)}시간 전`;
    } else {
      return date.toLocaleDateString();
    }
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            💬 대화 목록
          </CardTitle>
          <Button
            onClick={onNewSession}
            size="sm"
            className="text-xs"
          >
            ➕ 새 대화
          </Button>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col p-4">
        <ScrollArea className="flex-1">
          <div className="space-y-2">
            {isLoading ? (
              <div className="text-center text-gray-500 py-4">
                로딩 중...
              </div>
            ) : sessions.length === 0 ? (
              <div className="text-center text-gray-500 py-4">
                <p className="text-sm">대화 기록이 없습니다.</p>
                <p className="text-xs mt-1">새 대화를 시작해보세요!</p>
              </div>
            ) : (
              sessions.map((session) => (
                <div
                  key={session.session_id}
                  className={`p-3 rounded-lg border cursor-pointer hover:bg-gray-50 transition-colors ${
                    currentSessionId === session.session_id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200'
                  }`}
                  onClick={() => onSessionSelect(session.session_id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-medium text-gray-900 truncate">
                        {session.title}
                      </h4>
                      <p className="text-xs text-gray-500 mt-1">
                        {session.messageCount}개 메시지 · {formatDate(session.updated_at)}
                      </p>
                    </div>
                    <Button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteSession(session.session_id);
                      }}
                      variant="ghost"
                      size="sm"
                      className="ml-2 h-6 w-6 p-0 text-gray-400 hover:text-red-500"
                    >
                      🗑️
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
});

SessionList.displayName = 'SessionList';

export default SessionList;
export type { SessionSummary, SessionListRef };