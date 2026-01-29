import { GoogleGenerativeAI, GenerativeModel } from '@google/generative-ai';
import { logger } from '@/config/logger';

interface GeminiClientOptions {
  maxRetries?: number;
  initialDelayMs?: number;
  maxDelayMs?: number;
}

interface Message {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

interface GenerateOptions {
  messages: Message[];
  temperature?: number;
}

export class GeminiClient {
  private genAI: GoogleGenerativeAI;
  private model: GenerativeModel;
  private maxRetries: number;
  private initialDelayMs: number;
  private maxDelayMs: number;

  constructor(apiKey: string, options: GeminiClientOptions = {}) {
    this.genAI = new GoogleGenerativeAI(apiKey);
    this.model = this.genAI.getGenerativeModel({ model: 'gemini-1.5-flash' });
    this.maxRetries = options.maxRetries ?? 3;
    this.initialDelayMs = options.initialDelayMs ?? 1000;
    this.maxDelayMs = options.maxDelayMs ?? 30000;
  }

  /**
   * Generate JSON response from Gemini
   */
  async generateJSON(options: GenerateOptions): Promise<Record<string, unknown>> {
    const { messages, temperature = 0.3 } = options;

    // Build prompt from messages
    let prompt = '';
    for (const msg of messages) {
      if (msg.role === 'system') {
        prompt += `Instructions:\n${msg.content}\n\n`;
      } else if (msg.role === 'user') {
        prompt += `User Query: ${msg.content}\n`;
      }
    }

    let lastError: Error | null = null;
    let delay = this.initialDelayMs;

    for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
      try {
        const result = await this.model.generateContent({
          contents: [{ role: 'user', parts: [{ text: prompt }] }],
          generationConfig: {
            temperature,
            responseMimeType: 'application/json',
          },
        });

        const response = result.response;
        const text = response.text();

        // Parse JSON response
        const parsed = JSON.parse(text);
        return parsed;
      } catch (error) {
        lastError = error as Error;
        logger.warn(`Gemini API attempt ${attempt}/${this.maxRetries} failed:`, {
          error: lastError.message,
        });

        if (attempt < this.maxRetries) {
          await this.sleep(delay);
          delay = Math.min(delay * 2, this.maxDelayMs);
        }
      }
    }

    throw new Error(`Gemini API failed after ${this.maxRetries} attempts: ${lastError?.message}`);
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
