import { getRagDb } from './ragDb';
import { EmbeddingService } from './embeddingService';
import { env } from '@/config/env';

interface SearchResult {
  chunkId: string;
  documentId: string;
  title: string;
  content: string;
  score: number;
}

const DEFAULT_TOP_K = 5;
const DEFAULT_FTS_LIMIT = 60;

function cosineSimilarity(a: number[], b: number[]): number {
  if (a.length === 0 || b.length === 0 || a.length !== b.length) return 0;
  let dot = 0;
  let normA = 0;
  let normB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  if (normA === 0 || normB === 0) return 0;
  return dot / (Math.sqrt(normA) * Math.sqrt(normB));
}

interface SearchOptions {
  topK?: number;
  category?: string;
}

export class VectorSearchService {
  private embedder: EmbeddingService;

  constructor(embedder: EmbeddingService) {
    this.embedder = embedder;
  }

  async search(query: string, options: SearchOptions = {}): Promise<SearchResult[]> {
    const db = getRagDb();
    const queryEmbedding = await this.embedder.embed(query);
    const ftsLimit = Number(env.RAG_FTS_LIMIT || DEFAULT_FTS_LIMIT);
    const candidates = this.fetchCandidates(db, query, ftsLimit, options.category);
    const topK = options.topK ?? DEFAULT_TOP_K;

    const scored = candidates
      .map((row) => {
        const embedding = row.embedding ? (JSON.parse(row.embedding) as number[]) : [];
        const score = cosineSimilarity(queryEmbedding, embedding);
        return { ...row, score };
      })
      .filter((row) => row.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, topK);

    return scored.map((row) => ({
      chunkId: row.id,
      documentId: row.document_id,
      title: row.title || '문서',
      content: row.content,
      score: row.score,
    }));
  }

  private fetchCandidates(
    db: ReturnType<typeof getRagDb>,
    query: string,
    limit: number,
    category?: string
  ) {
    const safeQuery = query
      .replace(/[^\w가-힣\s]/g, ' ')
      .split(/\s+/)
      .filter(Boolean)
      .join(' ');

    let rows: Array<{
      id: string;
      document_id: string;
      title: string;
      content: string;
      embedding: string | null;
    }> = [];

    try {
      const ftsStmt = db.prepare(
        `SELECT chunk_id as id FROM chunks_fts WHERE chunks_fts MATCH ? LIMIT ?`
      );
      const ftsRows = ftsStmt.all(safeQuery || query, limit) as Array<{ id: string }>;
      if (ftsRows.length > 0) {
        const placeholders = ftsRows.map(() => '?').join(', ');
        const ids = ftsRows.map((row) => row.id);
        const stmt = db.prepare(
          `
          SELECT c.id, c.document_id, d.title, c.content, c.embedding
          FROM chunks c
          JOIN documents d ON d.id = c.document_id
          WHERE c.id IN (${placeholders})
          ${category ? 'AND d.metadata LIKE ?' : ''}
          `
        );
        rows = category
          ? (stmt.all(...ids, `%\"category\":\"${category}\"%`) as typeof rows)
          : (stmt.all(...ids) as typeof rows);
      }
    } catch {
      rows = [];
    }

    if (rows.length === 0) {
      const stmt = db.prepare(
        `
        SELECT c.id, c.document_id, d.title, c.content, c.embedding
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        ${category ? 'WHERE d.metadata LIKE ?' : ''}
        ORDER BY c.created_at DESC
        LIMIT ?
        `
      );
      rows = category
        ? (stmt.all(`%\"category\":\"${category}\"%`, limit) as typeof rows)
        : (stmt.all(limit) as typeof rows);
    }

    return rows;
  }
}
