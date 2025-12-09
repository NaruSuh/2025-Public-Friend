import dotenv from 'dotenv';
import { z } from 'zod';

dotenv.config();

const envSchema = z.object({
  // Server
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.string().default('3001'),
  FRONTEND_URL: z.string().default('http://localhost:5173'),

  // Database
  DATABASE_URL: z.string().default('postgresql://localhost:5432/napo_dev'),
  DATABASE_PROVIDER: z.enum(['supabase', 'local']).default('local'),

  // AI APIs
  OPENAI_API_KEY: z.string().optional(),
  GEMINI_API_KEY: z.string().optional(),

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
});

export const env = envSchema.parse(process.env);

export type Env = z.infer<typeof envSchema>;
