import React from 'react';
import { Send, MessageCircle, Bot, User, ExternalLink, AlertCircle } from 'lucide-react';
import { BrutalButton } from '@/components/common/BrutalButton';
import apiService from '@/services/api';
import styles from './ChatPanel.module.css';

interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  citations?: Array<{
    documentId: string;
    title: string;
    excerpt: string;
    relevanceScore: number;
  }>;
  confidence?: number;
}

const SUGGESTED_QUESTIONS = [
  '후보자 선거운동 방법',
  '공무원 선거 관련 제한',
  '정당 정치자금 규정',
  '여론조사 관련 법규',
];

const WELCOME_MESSAGE: Message = {
  id: 'welcome',
  type: 'bot',
  content:
    '안녕하세요! 선거법 관련 질문에 답변해 드리는 선관위 안내 챗봇입니다.\n' +
    '궁금한 사항을 입력해 주세요.',
  timestamp: new Date(),
};

export function ChatPanel() {
  const [messages, setMessages] = React.useState<Message[]>([WELCOME_MESSAGE]);
  const [input, setInput] = React.useState('');
  const [isTyping, setIsTyping] = React.useState(false);
  const [sessionId, setSessionId] = React.useState<string | null>(null);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const query = input.trim();
    if (!query) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: query,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    try {
      const response = await apiService.post('/chat', {
        message: query,
        sessionId,
      });
      const data = response.data;
      setSessionId(data.sessionId);

      const botResponse: Message = {
        id: `bot-${Date.now()}`,
        type: 'bot',
        content: `${data.answer}\n\n${data.disclaimer || ''}`.trim(),
        timestamp: new Date(),
        citations: data.citations || [],
        confidence: typeof data.confidence === 'number' ? data.confidence : undefined,
      };
      setMessages((prev) => [...prev, botResponse]);
    } catch (error) {
      const botResponse: Message = {
        id: `bot-${Date.now()}`,
        type: 'bot',
        content:
          '답변 생성 중 오류가 발생했습니다.\n잠시 후 다시 시도해 주세요.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botResponse]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleSuggestedQuestion = (question: string) => {
    setInput(question);
    inputRef.current?.focus();
  };

  return (
    <div className={styles.panel}>
      <header className={styles.header}>
        <MessageCircle size={20} />
        <h2 className={styles.title}>선거법 챗봇</h2>
        <span className={styles.badge}>Beta</span>
      </header>

      <div className={styles.disclaimer}>
        <AlertCircle size={14} />
        <span>본 답변은 참고용이며, 법적 효력이 없습니다.</span>
      </div>

      <div className={styles.messages}>
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`${styles.message} ${styles[`message-${msg.type}`]}`}
          >
            <div className={styles.messageIcon}>
              {msg.type === 'user' ? <User size={16} /> : <Bot size={16} />}
            </div>
            <div className={styles.messageContent}>
              <p className={styles.messageText}>{msg.content}</p>
              {msg.citations && msg.citations.length > 0 && (
                <div className={styles.relatedItems}>
                  <p className={styles.relatedLabel}>근거 문서:</p>
                  {msg.citations.map((item) => (
                    <div key={item.documentId} className={styles.relatedItem}>
                      <div className={styles.relatedLink}>
                        <ExternalLink size={12} />
                        <span>{item.title}</span>
                      </div>
                      {item.excerpt && (
                        <p className={styles.relatedExcerpt}>
                          {item.excerpt}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
              <span className={styles.messageTime}>
                {msg.timestamp.toLocaleTimeString('ko-KR', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </span>
              {typeof msg.confidence === 'number' && (
                <span className={styles.confidence}>
                  신뢰도 {(msg.confidence * 100).toFixed(0)}%
                </span>
              )}
            </div>
          </div>
        ))}

        {isTyping && (
          <div className={`${styles.message} ${styles['message-bot']}`}>
            <div className={styles.messageIcon}>
              <Bot size={16} />
            </div>
            <div className={styles.typing}>
              <span />
              <span />
              <span />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {messages.length === 1 && (
        <div className={styles.suggestions}>
          <p className={styles.suggestionsLabel}>자주 묻는 질문:</p>
          <div className={styles.suggestionsList}>
            {SUGGESTED_QUESTIONS.map((q) => (
              <button
                key={q}
                type="button"
                className={styles.suggestionBtn}
                onClick={() => handleSuggestedQuestion(q)}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      <form className={styles.inputArea} onSubmit={handleSubmit}>
        <input
          ref={inputRef}
          type="text"
          className={styles.input}
          placeholder="질문을 입력하세요..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isTyping}
        />
        <BrutalButton
          type="submit"
          variant="primary"
          size="md"
          disabled={!input.trim() || isTyping}
          icon={<Send size={16} />}
        >
          전송
        </BrutalButton>
      </form>
    </div>
  );
}
