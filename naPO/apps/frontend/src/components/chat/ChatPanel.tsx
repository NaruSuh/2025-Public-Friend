import React from 'react';
import { Send, Bot, User, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import apiService from '@/services/api';
import styles from './ChatPanel.module.css';

interface Citation {
  documentId: string;
  title: string;
  excerpt: string;
  relevanceScore: number;
}

interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  citations?: Citation[];
  confidence?: number;
}

const SUGGESTED_QUESTIONS = [
  '사전투표는 어디서 할 수 있나요?',
  '선거운동 기간은 언제부터인가요?',
  '공무원의 선거관여 제한은?',
  '정치자금 후원금 한도는?',
  '18세 선거권 기준은?',
  '여론조사 공표 제한은?',
];

const WELCOME_MESSAGE: Message = {
  id: 'welcome',
  type: 'bot',
  content:
    '안녕하세요! **선거법 AI 챗봇**입니다.\n\n' +
    '선거법, 정치자금법, 선관위 가이드라인 등에 대해 질문해 주세요.\n' +
    '4,500여 건의 선관위 공식 문서를 기반으로 답변합니다.',
  timestamp: new Date(),
};

function CitationBlock({ citations }: { citations: Citation[] }) {
  const [expanded, setExpanded] = React.useState(false);
  const shown = expanded ? citations : citations.slice(0, 2);

  return (
    <div className={styles.citations}>
      <button className={styles.citationToggle} onClick={() => setExpanded(!expanded)}>
        <FileText size={12} />
        <span>근거 문서 {citations.length}건</span>
        {citations.length > 2 && (expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />)}
      </button>
      {shown.map((c, i) => (
        <div key={`${c.documentId}-${i}`} className={styles.citationItem}>
          <span className={styles.citationTitle}>{c.title}</span>
          {expanded && c.excerpt && (
            <p className={styles.citationExcerpt}>{c.excerpt.slice(0, 200)}</p>
          )}
        </div>
      ))}
    </div>
  );
}

function formatBotText(text: string) {
  return text.split('\n').map((line, i) => {
    const parts = line.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/).map((part, j) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={j}>{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith('*') && part.endsWith('*')) {
        return <em key={j}>{part.slice(1, -1)}</em>;
      }
      return <React.Fragment key={j}>{part}</React.Fragment>;
    });
    return (
      <React.Fragment key={i}>
        {i > 0 && <br />}
        {parts}
      </React.Fragment>
    );
  });
}

export function ChatPanel() {
  const [messages, setMessages] = React.useState<Message[]>([WELCOME_MESSAGE]);
  const [input, setInput] = React.useState('');
  const [isTyping, setIsTyping] = React.useState(false);
  const [sessionId, setSessionId] = React.useState<string | null>(null);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const inputRef = React.useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  React.useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 120) + 'px';
    }
  }, [input]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const query = input.trim();
    if (!query || isTyping) return;

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
        content: data.answer,
        timestamp: new Date(),
        citations: data.citations || [],
        confidence: typeof data.confidence === 'number' ? data.confidence : undefined,
      };
      setMessages((prev) => [...prev, botResponse]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: `bot-${Date.now()}`,
          type: 'bot',
          content: '답변 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.',
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsTyping(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleSuggestion = (q: string) => {
    setInput(q);
    inputRef.current?.focus();
  };

  const isWelcome = messages.length === 1;

  return (
    <div className={styles.container}>
      <div className={styles.chatArea}>
        <div className={styles.messages}>
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`${styles.msgRow} ${msg.type === 'user' ? styles.msgRowUser : styles.msgRowBot}`}
            >
              <div className={`${styles.msgAvatar} ${msg.type === 'user' ? styles.avatarUser : styles.avatarBot}`}>
                {msg.type === 'user' ? <User size={16} /> : <Bot size={16} />}
              </div>
              <div className={styles.msgBubble}>
                <div className={`${styles.msgText} ${msg.type === 'user' ? styles.msgTextUser : styles.msgTextBot}`}>
                  {msg.type === 'bot' ? formatBotText(msg.content) : msg.content}
                </div>
                {msg.citations && msg.citations.length > 0 && (
                  <CitationBlock citations={msg.citations} />
                )}
              </div>
            </div>
          ))}

          {isTyping && (
            <div className={`${styles.msgRow} ${styles.msgRowBot}`}>
              <div className={`${styles.msgAvatar} ${styles.avatarBot}`}>
                <Bot size={16} />
              </div>
              <div className={styles.typing}>
                <span /><span /><span />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {isWelcome && (
          <div className={styles.suggestions}>
            {SUGGESTED_QUESTIONS.map((q) => (
              <button key={q} className={styles.suggestionBtn} onClick={() => handleSuggestion(q)}>
                {q}
              </button>
            ))}
          </div>
        )}

        <form className={styles.inputArea} onSubmit={handleSubmit}>
          <div className={styles.inputWrap}>
            <textarea
              ref={inputRef}
              className={styles.input}
              placeholder="선거법에 대해 질문하세요..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isTyping}
              rows={1}
            />
            <button
              type="submit"
              className={styles.sendBtn}
              disabled={!input.trim() || isTyping}
            >
              <Send size={18} />
            </button>
          </div>
          <p className={styles.disclaimer}>
            본 답변은 참고용이며 법적 효력이 없습니다.
          </p>
        </form>
      </div>
    </div>
  );
}
