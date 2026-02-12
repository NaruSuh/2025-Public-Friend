import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';
import { z } from 'zod';

const envCandidates = [
  process.env.DOTENV_PATH,
  path.resolve(process.cwd(), '.env'),
  path.resolve(process.cwd(), '..', '..', '..', '.env'),
].filter((p): p is string => Boolean(p));

for (const envPath of envCandidates) {
  if (fs.existsSync(envPath)) {
    dotenv.config({ path: envPath });
  }
}

const envSchema = z.object({
  // Server
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.string().default('3001'),
  FRONTEND_URL: z.string().default('http://localhost:5173'),

  // Database
  DATABASE_URL: z.string(),
  DATABASE_PROVIDER: z.enum(['supabase', 'local']).default('local'),

  // AI APIs
  OPENAI_API_KEY: z.string().optional(),
  GEMINI_API_KEY: z.string().optional(),
  GEMINI_CHAT_MODEL: z.string().optional(),
  GEMINI_EMBED_MODEL: z.string().optional(),
  GEMINI_API_VERSION: z.string().optional(),

  // YouTube
  YOUTUBE_API_KEY: z.string().optional(),

  // Public Data Portal APIs
  PUBLIC_DATA_API_KEY: z.string().optional(),
  NABOSTATS_API_KEY: z.string().optional(),
  NEC_MANIFESTO_API_KEY: z.string().optional(),
  RONE_API_KEY: z.string().optional(),

  // Clova OCR
  CLOVA_OCR_API_URL: z.string().optional(),
  CLOVA_OCR_SECRET_KEY: z.string().optional(),

  // Google Cloud
  GOOGLE_APPLICATION_CREDENTIALS: z.string().optional(),

  // Dolphin Parser Service
  DOLPHIN_SERVICE_URL: z.string().optional(),

  // Feature Flags
  ENABLE_NL_QUERY: z
    .string()
    .transform((v) => v === 'true')
    .default('true'),
  ENABLE_OCR_PARSING: z
    .string()
    .transform((v) => v === 'true')
    .default('true'),
  ENABLE_CRAWLING: z
    .string()
    .transform((v) => v === 'true')
    .default('true'),

  // RAG (SQLite)
  RAG_DB_PATH: z.string().optional(),
  RAG_SOURCE_ROOT: z.string().optional(),
  RAG_TOP_K: z.string().optional(),
  RAG_FTS_LIMIT: z.string().optional(),
  RAG_CHUNK_SIZE: z.string().optional(),
  RAG_CHUNK_OVERLAP: z.string().optional(),
  RAG_MAX_DOCS: z.string().optional(),
  RAG_MAX_FILE_MB: z.string().optional(),
  RAG_MAX_CHUNKS_PER_DOC: z.string().optional(),
  RAG_CONTEXT_MAX: z.string().optional(),
  RAG_INCLUDE_PATHS: z.string().optional(),
  RAG_EXCLUDE_PATHS: z.string().optional(),
  RAG_SKIP_PDF: z.string().optional(),
  RAG_EMBED_PROVIDER: z.string().optional(),
  RAG_EMBED_MODEL_LOCAL: z.string().optional(),
});

export const env = envSchema.parse(process.env);

export type Env = z.infer<typeof envSchema>;
