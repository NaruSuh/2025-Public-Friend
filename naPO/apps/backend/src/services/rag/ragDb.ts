import Database from 'better-sqlite3';
import fs from 'fs';
import path from 'path';
import { env } from '@/config/env';

let dbInstance: Database.Database | null = null;

const DEFAULT_DB_PATH = path.resolve(process.cwd(), 'data', 'rag.sqlite');

function ensureDirectory(filePath: string): void {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function initSchema(db: Database.Database): void {
  db.exec(`
    CREATE TABLE IF NOT EXISTS documents (
      id TEXT PRIMARY KEY,
      source_key TEXT UNIQUE,
      source_path TEXT,
      source_type TEXT,
      title TEXT,
      content TEXT,
      metadata TEXT,
      created_at INTEGER,
      updated_at INTEGER
    );

    CREATE TABLE IF NOT EXISTS chunks (
      id TEXT PRIMARY KEY,
      document_id TEXT,
      chunk_index INTEGER,
      content TEXT,
      embedding TEXT,
      start_offset INTEGER,
      end_offset INTEGER,
      created_at INTEGER,
      FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS chat_sessions (
      id TEXT PRIMARY KEY,
      created_at INTEGER,
      updated_at INTEGER
    );

    CREATE TABLE IF NOT EXISTS chat_messages (
      id TEXT PRIMARY KEY,
      session_id TEXT,
      role TEXT,
      content TEXT,
      created_at INTEGER,
      FOREIGN KEY(session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS citations (
      id TEXT PRIMARY KEY,
      message_id TEXT,
      document_id TEXT,
      chunk_id TEXT,
      relevance REAL,
      excerpt TEXT,
      created_at INTEGER,
      FOREIGN KEY(message_id) REFERENCES chat_messages(id) ON DELETE CASCADE
    );

    CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts
    USING fts5(content, chunk_id UNINDEXED, document_id UNINDEXED, title UNINDEXED);

    CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
    CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
  `);
}

export function getRagDb(): Database.Database {
  if (dbInstance) {
    return dbInstance;
  }

  const dbPath = env.RAG_DB_PATH || DEFAULT_DB_PATH;
  ensureDirectory(dbPath);

  const db = new Database(dbPath);
  db.pragma('journal_mode = WAL');
  db.pragma('synchronous = NORMAL');

  initSchema(db);
  dbInstance = db;
  return db;
}
