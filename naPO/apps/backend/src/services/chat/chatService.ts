import crypto from 'crypto';
import { env } from '@/config/env';
import { getRagDb } from '@/services/rag/ragDb';
import { EmbeddingService } from '@/services/rag/embeddingService';
import { VectorSearchService } from '@/services/rag/vectorSearch';
import { GeminiChatClient } from './geminiChatClient';

const DISCLAIMER =
  '⚠️ 본 답변은 참고용이며 법적 효력이 없습니다. 정확한 해석은 선관위 공식 안내 또는 전문가 상담을 권장합니다.';

const SYSTEM_PROMPT = `
당신은 중앙선거관리위원회 관련 법령/가이드를 안내하는 AI입니다.

[역할]
- 선거법, 정치자금법, 선관위 가이드 기반 답변
- 답변마다 관련 근거를 명시
- 불확실한 경우 "정확한 확인이 필요"라고 안내
- 정치적 중립 유지

[응답 형식]
1. 핵심 답변 (1~2문장)
2. 상세 설명
3. 관련 근거 (조항/문서)
4. 주의사항 (필요 시)

[참고 문서]
{CONTEXT}
`.trim();

interface ChatResult {
  answer: string;
  sessionId: string;
  citations: Array<{
    documentId: string;
    title: string;
    excerpt: string;
    relevanceScore: number;
  }>;
  confidence: number;
  disclaimer: string;
}

export class ChatService {
  private embedder: EmbeddingService;
  private vectorSearch: VectorSearchService;
  private chatClient: GeminiChatClient;

  constructor() {
    this.embedder = new EmbeddingService(env.GEMINI_API_KEY);
    this.vectorSearch = new VectorSearchService(this.embedder);
    this.chatClient = new GeminiChatClient(env.GEMINI_API_KEY);
  }

  async chat(message: string, sessionId?: string): Promise<ChatResult> {
    const db = getRagDb();
    const session = sessionId || this.createSession(db);
    const history = this.getRecentHistory(db, session, 6);

    const topK = Number(env.RAG_TOP_K || 5);
    const searchResults = await this.vectorSearch.search(message, { topK });
    if (searchResults.length === 0) {
      const fallbackAnswer =
        '관련 정보를 찾지 못했습니다. 질문 범위를 구체화하거나 선관위 공식 안내를 확인해 주세요.';
      this.insertMessage(db, session, 'user', message);
      this.insertMessage(db, session, 'assistant', fallbackAnswer);
      return {
        answer: fallbackAnswer,
        sessionId: session,
        citations: [],
        confidence: 0,
        disclaimer: DISCLAIMER,
      };
    }
    const contextLimit = Number(env.RAG_CONTEXT_MAX || 6000);
    const context = searchResults
      .map((item) => `- ${item.title}\n${item.content}`)
      .join('\n\n')
      .slice(0, contextLimit);

    const prompt = SYSTEM_PROMPT.replace('{CONTEXT}', context || '관련 문서를 찾지 못했습니다.');
    const answer = await this.chatClient.generateAnswer(prompt, history, message);

    this.insertMessage(db, session, 'user', message);
    const assistantMessageId = this.insertMessage(db, session, 'assistant', answer);

    const confidence =
      searchResults.length > 0
        ? Math.min(
            1,
            searchResults.reduce((sum, item) => sum + item.score, 0) / searchResults.length
          )
        : 0;

    const citations = searchResults.map((item) => {
      this.insertCitation(db, assistantMessageId, item.documentId, item.chunkId, item.score, item.content);
      return {
        documentId: item.documentId,
        title: item.title,
        excerpt: item.content.slice(0, 320),
        relevanceScore: item.score,
      };
    });

    return {
      answer,
      sessionId: session,
      citations,
      confidence,
      disclaimer: DISCLAIMER,
    };
  }

  private createSession(db: ReturnType<typeof getRagDb>): string {
    const id = crypto.randomUUID();
    const now = Date.now();
    db.prepare(
      `INSERT INTO chat_sessions (id, created_at, updated_at) VALUES (?, ?, ?)`
    ).run(id, now, now);
    return id;
  }

  private getRecentHistory(
    db: ReturnType<typeof getRagDb>,
    sessionId: string,
    limit: number
  ) {
    const rows = db
      .prepare(
        `
        SELECT role, content
        FROM chat_messages
        WHERE session_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        `
      )
      .all(sessionId, limit) as Array<{ role: string; content: string }>;
    return rows
      .reverse()
      .map((row) => ({ role: row.role === 'assistant' ? 'assistant' : 'user', content: row.content }));
  }

  private insertMessage(
    db: ReturnType<typeof getRagDb>,
    sessionId: string,
    role: 'user' | 'assistant',
    content: string
  ): string {
    const id = crypto.randomUUID();
    const now = Date.now();
    db.prepare(
      `INSERT INTO chat_messages (id, session_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)`
    ).run(id, sessionId, role, content, now);
    db.prepare(`UPDATE chat_sessions SET updated_at = ? WHERE id = ?`).run(now, sessionId);
    return id;
  }

  private insertCitation(
    db: ReturnType<typeof getRagDb>,
    messageId: string,
    documentId: string,
    chunkId: string,
    score: number,
    excerpt: string
  ) {
    db.prepare(
      `
      INSERT INTO citations (id, message_id, document_id, chunk_id, relevance, excerpt, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?)
      `
    ).run(crypto.randomUUID(), messageId, documentId, chunkId, score, excerpt.slice(0, 1000), Date.now());
  }
}
