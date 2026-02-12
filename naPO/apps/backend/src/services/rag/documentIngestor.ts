import fs from 'fs';
import path from 'path';
import readline from 'readline';
import crypto from 'crypto';
import pdfParse from 'pdf-parse';
import { getRagDb } from './ragDb';
import { chunkText } from './chunker';
import { EmbeddingService } from './embeddingService';
import { env } from '@/config/env';
import { logger } from '@/config/logger';

const DEFAULT_ROOT = '/home/naru/dev/naID/naPO_DB';
const SUPPORTED_EXTENSIONS = new Set(['.json', '.jsonl', '.html', '.htm', '.pdf', '.txt', '.md']);
const DEFAULT_MAX_FILE_MB = 50;
const DEFAULT_MAX_CHUNKS_PER_DOC = 200;

function parseList(value?: string) {
  if (!value) return [];
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

function classifyPath(filePath: string) {
  if (filePath.includes('1. 지방의회 회의록')) return 'LOCAL_COUNCIL_MINUTES';
  if (filePath.includes('2. 선거정보자료')) return 'ELECTION_INFO_HUMAN';
  if (filePath.includes('3. 선거정보자료')) return 'ELECTION_INFO_SERVER';
  if (filePath.includes('4. 지방정책보조자료')) return 'LOCAL_POLICY_SUPPORT';
  return 'OTHER';
}

interface IngestStats {
  documents: number;
  chunks: number;
  skipped: number;
}

function hashId(value: string): string {
  return crypto.createHash('sha1').update(value).digest('hex');
}

function stripHtml(html: string): string {
  return html.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
}

function buildSourceKey(filePath: string, suffix?: string): string {
  return suffix ? `${filePath}#${suffix}` : filePath;
}

function extractDocsFromJson(data: any, filePath: string) {
  const category = classifyPath(filePath);
  const docs: Array<{ sourceKey: string; title: string; content: string; metadata?: any }> = [];

  if (data?.chapters && Array.isArray(data.chapters)) {
    const lawName = data.name || path.basename(filePath);
    for (const chapter of data.chapters) {
      if (!chapter?.articles) continue;
      for (const article of chapter.articles) {
        const articleTitle = `${lawName} ${article.number || ''} ${article.title || ''}`.trim();
        const content = article.content || '';
        if (!content) continue;
        docs.push({
          sourceKey: buildSourceKey(filePath, article.joidfull || article.number || articleTitle),
          title: articleTitle,
          content,
          metadata: {
            lawName,
            chapter: chapter.title,
            articleNumber: article.number,
            articleTitle: article.title,
            sourceUrl: data.sourceUrl,
            effectiveDate: data.effectiveDate,
            category,
          },
        });
      }
    }
    return docs;
  }

  if (Array.isArray(data?.items)) {
    data.items.forEach((item: any, index: number) => {
      const title = item.eventNm || item.title || item.name || `항목 ${index + 1}`;
      const content =
        item.content ||
        item.summary ||
        item.description ||
        JSON.stringify(item, null, 2);
      docs.push({
        sourceKey: buildSourceKey(filePath, item.eventNum || item.eventNo || String(index)),
        title,
        content,
        metadata: { ...item, category },
      });
    });
    return docs;
  }

  if (Array.isArray(data)) {
    data.forEach((item, index) => {
      const title = item.title || item.name || `항목 ${index + 1}`;
      const content = item.content || item.text || JSON.stringify(item, null, 2);
      docs.push({
        sourceKey: buildSourceKey(filePath, String(index)),
        title,
        content,
        metadata: { ...item, category },
      });
    });
    return docs;
  }

  const singleTitle = data?.title || data?.name || path.basename(filePath);
  const singleContent =
    data?.content ||
    data?.text ||
    data?.description ||
    JSON.stringify(data, null, 2);
  docs.push({
    sourceKey: buildSourceKey(filePath),
    title: singleTitle,
    content: singleContent,
    metadata: { ...data, category },
  });

  return docs;
}

export class DocumentIngestor {
  private embedder: EmbeddingService;
  private includePaths: string[];
  private excludePaths: string[];
  private maxDocs?: number;
  private maxFileBytes: number;
  private maxChunksPerDoc: number;
  private chunkSize: number;
  private chunkOverlap: number;
  private skipPdf: boolean;

  constructor(embedder: EmbeddingService) {
    this.embedder = embedder;
    this.includePaths = parseList(env.RAG_INCLUDE_PATHS);
    this.excludePaths = parseList(env.RAG_EXCLUDE_PATHS);
    this.maxDocs = env.RAG_MAX_DOCS ? Number(env.RAG_MAX_DOCS) : undefined;
    this.maxFileBytes = Number(env.RAG_MAX_FILE_MB || DEFAULT_MAX_FILE_MB) * 1024 * 1024;
    this.maxChunksPerDoc = Number(env.RAG_MAX_CHUNKS_PER_DOC || DEFAULT_MAX_CHUNKS_PER_DOC);
    this.chunkSize = Number(env.RAG_CHUNK_SIZE || 800);
    this.chunkOverlap = Number(env.RAG_CHUNK_OVERLAP || 120);
    this.skipPdf = (env.RAG_SKIP_PDF || 'false') === 'true';
  }

  async ingestAll(rootPath = env.RAG_SOURCE_ROOT || DEFAULT_ROOT): Promise<IngestStats> {
    const db = getRagDb();
    const stats: IngestStats = { documents: 0, chunks: 0, skipped: 0 };
    const files = await this.walk(rootPath);

    let processedDocs = 0;
    for (const filePath of files) {
      if (this.maxDocs && processedDocs >= this.maxDocs) break;
      try {
        const ext = path.extname(filePath).toLowerCase();
        if (!SUPPORTED_EXTENSIONS.has(ext)) continue;
        if (!this.shouldInclude(filePath)) continue;
        if (this.skipPdf && ext === '.pdf') {
          stats.skipped += 1;
          continue;
        }
        const stat = await fs.promises.stat(filePath);
        if (stat.size > this.maxFileBytes) {
          stats.skipped += 1;
          continue;
        }
        const docStats = await this.ingestFile(db, filePath, ext);
        stats.documents += docStats.documents;
        stats.chunks += docStats.chunks;
        stats.skipped += docStats.skipped;
        processedDocs += docStats.documents;
      } catch (error) {
        logger.warn('RAG ingest failed', { filePath, error: (error as Error).message });
      }
    }

    return stats;
  }

  private async ingestFile(
    db: ReturnType<typeof getRagDb>,
    filePath: string,
    ext: string
  ): Promise<IngestStats> {
    const stats: IngestStats = { documents: 0, chunks: 0, skipped: 0 };
    if (filePath.endsWith(':Zone.Identifier')) {
      stats.skipped += 1;
      return stats;
    }

    if (ext === '.jsonl') {
      return await this.ingestJsonl(db, filePath);
    }

    if (ext === '.pdf') {
      const buffer = fs.readFileSync(filePath);
      const parsed = await pdfParse(buffer);
      const content = parsed.text.trim();
      if (!content) {
        stats.skipped += 1;
        return stats;
      }
      const doc = {
        sourceKey: buildSourceKey(filePath),
        title: path.basename(filePath),
        content,
        metadata: { source: 'pdf', pageCount: parsed.numpages, category: classifyPath(filePath) },
      };
      return await this.insertDocument(db, doc, filePath);
    }

    const raw = fs.readFileSync(filePath, 'utf-8');
    if (!raw.trim()) {
      stats.skipped += 1;
      return stats;
    }

    if (ext === '.html' || ext === '.htm') {
      const content = stripHtml(raw);
      if (!content) {
        stats.skipped += 1;
        return stats;
      }
      const doc = {
        sourceKey: buildSourceKey(filePath),
        title: path.basename(filePath),
        content,
        metadata: { source: 'html', category: classifyPath(filePath) },
      };
      return await this.insertDocument(db, doc, filePath);
    }

    if (ext === '.json') {
      const data = JSON.parse(raw);
      const docs = extractDocsFromJson(data, filePath);
      for (const doc of docs) {
        const result = await this.insertDocument(db, doc, filePath);
        stats.documents += result.documents;
        stats.chunks += result.chunks;
        stats.skipped += result.skipped;
      }
      return stats;
    }

      const doc = {
        sourceKey: buildSourceKey(filePath),
        title: path.basename(filePath),
        content: raw,
        metadata: { source: 'text', category: classifyPath(filePath) },
      };
      return await this.insertDocument(db, doc, filePath);
    }

  private async ingestJsonl(
    db: ReturnType<typeof getRagDb>,
    filePath: string
  ): Promise<IngestStats> {
    const stats: IngestStats = { documents: 0, chunks: 0, skipped: 0 };
    const stream = fs.createReadStream(filePath, { encoding: 'utf-8' });
    const rl = readline.createInterface({ input: stream, crlfDelay: Infinity });
    let index = 0;

    for await (const line of rl) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      index += 1;
      try {
        const record = JSON.parse(trimmed);
        const title =
          record.title ||
          record.meeting_type ||
          record.council_name ||
          `회의록 ${index}`;
        const content =
          record.full_content ||
          record.content ||
          record.html_content ||
          JSON.stringify(record, null, 2);
        const doc = {
          sourceKey: buildSourceKey(filePath, record.docid || String(index)),
          title,
          content,
          metadata: {
            councilId: record.council_id,
            councilName: record.council_name,
            meetingDate: record.meeting_date,
            meetingType: record.meeting_type,
            source: record.source,
          },
        };
        const result = await this.insertDocument(db, doc, filePath);
        stats.documents += result.documents;
        stats.chunks += result.chunks;
        stats.skipped += result.skipped;
      } catch (error) {
        logger.warn('JSONL parse failed', { filePath, index, error: (error as Error).message });
        stats.skipped += 1;
      }
    }

    return stats;
  }

  private async insertDocument(
    db: ReturnType<typeof getRagDb>,
    doc: { sourceKey: string; title: string; content: string; metadata?: any },
    sourcePath: string
  ): Promise<IngestStats> {
    const stats: IngestStats = { documents: 0, chunks: 0, skipped: 0 };
    const now = Date.now();
    const existsStmt = db.prepare('SELECT id FROM documents WHERE source_key = ?');
    const existing = existsStmt.get(doc.sourceKey) as { id: string } | undefined;
    if (existing) {
      stats.skipped += 1;
      return stats;
    }

    const docId = hashId(doc.sourceKey);
    const insertDoc = db.prepare(
      `
      INSERT INTO documents (id, source_key, source_path, source_type, title, content, metadata, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
      `
    );
    insertDoc.run(
      docId,
      doc.sourceKey,
      sourcePath,
      path.extname(sourcePath).toLowerCase().replace('.', ''),
      doc.title,
      doc.content,
      JSON.stringify(doc.metadata || {}),
      now,
      now
    );
    stats.documents += 1;

    const chunks = chunkText(doc.content, {
      chunkSize: this.chunkSize,
      overlap: this.chunkOverlap,
    }).slice(0, this.maxChunksPerDoc);
    const insertChunk = db.prepare(
      `
      INSERT INTO chunks (id, document_id, chunk_index, content, embedding, start_offset, end_offset, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `
    );
    const insertFts = db.prepare(
      `
      INSERT INTO chunks_fts (content, chunk_id, document_id, title)
      VALUES (?, ?, ?, ?)
      `
    );

    for (let i = 0; i < chunks.length; i++) {
      const chunk = chunks[i];
      const chunkId = hashId(`${doc.sourceKey}#chunk:${i}`);
      const embedding = await this.embedder.embed(chunk.text);
      insertChunk.run(
        chunkId,
        docId,
        i,
        chunk.text,
        JSON.stringify(embedding),
        chunk.startOffset,
        chunk.endOffset,
        now
      );
      insertFts.run(chunk.text, chunkId, docId, doc.title);
      stats.chunks += 1;
    }

    return stats;
  }

  private async walk(root: string): Promise<string[]> {
    const entries = await fs.promises.readdir(root, { withFileTypes: true });
    const files: string[] = [];
    for (const entry of entries) {
      const fullPath = path.join(root, entry.name);
      if (entry.isDirectory()) {
        files.push(...(await this.walk(fullPath)));
      } else {
        files.push(fullPath);
      }
    }
    return files;
  }

  private shouldInclude(filePath: string): boolean {
    if (this.excludePaths.some((pattern) => filePath.includes(pattern))) {
      return false;
    }
    if (this.includePaths.length === 0) return true;
    return this.includePaths.some((pattern) => filePath.includes(pattern));
  }
}
