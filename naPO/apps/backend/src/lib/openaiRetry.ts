import OpenAI from 'openai';

/**
 * OpenAI API Retry Logic with Exponential Backoff
 * Handles 429 (Rate Limit) errors gracefully
 */

export interface RetryConfig {
  maxRetries?: number;
  initialDelayMs?: number;
  maxDelayMs?: number;
  backoffMultiplier?: number;
}

const DEFAULT_CONFIG: Required<RetryConfig> = {
  maxRetries: 3,
  initialDelayMs: 1000,
  maxDelayMs: 60000,
  backoffMultiplier: 2,
};

export class OpenAIRetryError extends Error {
  constructor(
    message: string,
    public readonly lastError: Error,
    public readonly attemptCount: number
  ) {
    super(message);
    this.name = 'OpenAIRetryError';
  }
}

/**
 * Retry wrapper for OpenAI API calls with exponential backoff
 */
export async function withRetry<T>(
  fn: () => Promise<T>,
  config: RetryConfig = {}
): Promise<T> {
  const cfg = { ...DEFAULT_CONFIG, ...config };
  let lastError: Error | null = null;
  let delay = cfg.initialDelayMs;

  for (let attempt = 0; attempt <= cfg.maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error: any) {
      lastError = error;

      // Check if it's a rate limit error
      const isRateLimit = error?.status === 429 || error?.code === 'rate_limit_exceeded';

      // Check if it's a retryable error
      const isRetryable =
        isRateLimit ||
        error?.status === 500 ||
        error?.status === 502 ||
        error?.status === 503 ||
        error?.status === 504 ||
        error?.code === 'ECONNRESET' ||
        error?.code === 'ETIMEDOUT';

      // Don't retry on last attempt or non-retryable errors
      if (attempt >= cfg.maxRetries || !isRetryable) {
        break;
      }

      // Extract Retry-After header if present (for 429 errors)
      let waitTime = delay;
      if (isRateLimit && error?.headers) {
        const retryAfter = error.headers['retry-after'];
        if (retryAfter) {
          const retryAfterMs = parseInt(retryAfter, 10) * 1000;
          if (!isNaN(retryAfterMs)) {
            waitTime = Math.min(retryAfterMs, cfg.maxDelayMs);
          }
        }
      }

      console.log(
        `[OpenAI Retry] Attempt ${attempt + 1}/${cfg.maxRetries} failed. ` +
          `Retrying in ${waitTime}ms... Error: ${error?.message || error}`
      );

      // Wait before retrying
      await sleep(waitTime);

      // Increase delay for next attempt (exponential backoff)
      delay = Math.min(delay * cfg.backoffMultiplier, cfg.maxDelayMs);
    }
  }

  // All retries exhausted
  throw new OpenAIRetryError(
    `OpenAI API call failed after ${cfg.maxRetries + 1} attempts`,
    lastError!,
    cfg.maxRetries + 1
  );
}

/**
 * Enhanced OpenAI wrapper with automatic retry
 */
export class OpenAIWithRetry {
  constructor(
    private openai: OpenAI,
    private retryConfig: RetryConfig = {}
  ) {}

  async chatCompletion(
    params: OpenAI.Chat.ChatCompletionCreateParamsNonStreaming
  ): Promise<OpenAI.Chat.ChatCompletion> {
    return withRetry(
      () => this.openai.chat.completions.create(params) as Promise<OpenAI.Chat.ChatCompletion>,
      this.retryConfig
    );
  }

  async embedding(
    params: OpenAI.EmbeddingCreateParams
  ): Promise<OpenAI.Embeddings.CreateEmbeddingResponse> {
    return withRetry(
      () => this.openai.embeddings.create(params),
      this.retryConfig
    );
  }

  // Pass through non-retried methods
  get images() {
    return this.openai.images;
  }

  get audio() {
    return this.openai.audio;
  }

  get files() {
    return this.openai.files;
  }

  get models() {
    return this.openai.models;
  }
}

/**
 * Helper function to sleep for a specified duration
 */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
