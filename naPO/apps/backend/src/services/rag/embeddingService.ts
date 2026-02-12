import { GoogleGenerativeAI, GenerativeModel } from '@google/generative-ai';
import { pipeline } from '@xenova/transformers';
import { env } from '@/config/env';
import { logger } from '@/config/logger';

type EmbedProvider = 'gemini' | 'local';

const DEFAULT_EMBED_MODEL = 'models/text-embedding-004';
const FALLBACK_EMBED_MODEL = 'models/embedding-001';
const DEFAULT_API_VERSION = 'v1';
const DEFAULT_LOCAL_MODEL = 'Xenova/all-MiniLM-L6-v2';

let localPipelinePromise: ReturnType<typeof pipeline> | null = null;

export class EmbeddingService {
  private provider: EmbedProvider;
  private geminiModel?: GenerativeModel;
  private geminiModelName?: string;
  private genAI?: GoogleGenerativeAI;
  private maxRetries = 3;
  private initialDelayMs = 1000;
  private maxDelayMs = 20000;

  constructor(apiKey?: string, modelName?: string) {
    this.provider = (env.RAG_EMBED_PROVIDER as EmbedProvider) || 'gemini';

    if (this.provider === 'local') {
      // Local provider does lazy init inside embed()
      return;
    }

    if (!apiKey) {
      throw new Error('GEMINI_API_KEY is required for embeddings');
    }
    this.genAI = new GoogleGenerativeAI(apiKey);
    this.geminiModelName = this.normalizeModelName(modelName || env.GEMINI_EMBED_MODEL || DEFAULT_EMBED_MODEL);
    this.geminiModel = this.genAI.getGenerativeModel(
      { model: this.geminiModelName },
      { apiVersion: env.GEMINI_API_VERSION || DEFAULT_API_VERSION }
    );
  }

  async embed(text: string): Promise<number[]> {
    if (this.provider === 'local') {
      return this.embedLocal(text);
    }
    return this.embedGemini(text);
  }

  private async embedGemini(text: string): Promise<number[]> {
    if (!this.genAI || !this.geminiModel || !this.geminiModelName) {
      throw new Error('Gemini embedding not initialized');
    }

    let delay = this.initialDelayMs;
    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
      try {
        const result = await this.geminiModel.embedContent(text);
        return result.embedding.values || [];
      } catch (error) {
        lastError = error as Error;
        if (this.shouldFallbackModel(lastError) && this.geminiModelName !== FALLBACK_EMBED_MODEL) {
          logger.warn('Gemini embedding model not found, falling back', {
            from: this.geminiModelName,
            to: FALLBACK_EMBED_MODEL,
          });
          this.geminiModelName = FALLBACK_EMBED_MODEL;
          this.geminiModel = this.genAI.getGenerativeModel(
            { model: this.geminiModelName },
            { apiVersion: env.GEMINI_API_VERSION || DEFAULT_API_VERSION }
          );
          continue;
        }
        logger.warn(`Gemini embedding attempt ${attempt}/${this.maxRetries} failed`, {
          error: lastError.message,
        });
        if (attempt < this.maxRetries) {
          await new Promise((resolve) => setTimeout(resolve, delay));
          delay = Math.min(delay * 2, this.maxDelayMs);
        }
      }
    }

    throw new Error(`Gemini embedding failed: ${lastError?.message}`);
  }

  private async embedLocal(text: string): Promise<number[]> {
    const pipe = await this.getLocalPipeline();
    const output = await pipe(text, {
      pooling: 'mean',
      normalize: true,
    });
    return Array.from(output.data);
  }

  private async getLocalPipeline() {
    if (!localPipelinePromise) {
      const modelId = env.RAG_EMBED_MODEL_LOCAL || DEFAULT_LOCAL_MODEL;
      localPipelinePromise = pipeline('feature-extraction', modelId, { quantized: true });
    }
    return localPipelinePromise;
  }

  private shouldFallbackModel(error: Error): boolean {
    const message = error.message.toLowerCase();
    return message.includes('404') || message.includes('not found');
  }

  private normalizeModelName(name: string): string {
    if (!name) return DEFAULT_EMBED_MODEL;
    return name.startsWith('models/') ? name : `models/${name}`;
  }
}
