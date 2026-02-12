import { GoogleGenerativeAI, GenerativeModel } from '@google/generative-ai';
import { env } from '@/config/env';
import { logger } from '@/config/logger';

const DEFAULT_CHAT_MODEL = 'models/gemini-2.5-flash';
const DEFAULT_API_VERSION = 'v1';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export class GeminiChatClient {
  private model: GenerativeModel;

  constructor(apiKey?: string) {
    if (!apiKey) {
      throw new Error('GEMINI_API_KEY is required for chat');
    }
    const genAI = new GoogleGenerativeAI(apiKey);
    const modelName = this.normalizeModelName(env.GEMINI_CHAT_MODEL || DEFAULT_CHAT_MODEL);
    this.model = genAI.getGenerativeModel(
      { model: modelName },
      { apiVersion: env.GEMINI_API_VERSION || DEFAULT_API_VERSION }
    );
  }

  async generateAnswer(systemPrompt: string, history: ChatMessage[], message: string) {
    const historyText = history
      .map((msg) => `${msg.role === 'user' ? '사용자' : '답변'}: ${msg.content}`)
      .join('\n');

    const prompt = [
      systemPrompt,
      historyText ? `\n[대화 기록]\n${historyText}\n` : '',
      `[질문]\n${message}`,
    ]
      .filter(Boolean)
      .join('\n');

    try {
      const result = await this.model.generateContent({
        contents: [{ role: 'user', parts: [{ text: prompt }] }],
        generationConfig: { temperature: 0.2 },
      });
      const response = result.response.text();
      return response.trim();
    } catch (error) {
      logger.error('Gemini chat generation failed', { error: (error as Error).message });
      throw error;
    }
  }

  private normalizeModelName(name: string): string {
    if (!name) return DEFAULT_CHAT_MODEL;
    return name.startsWith('models/') ? name : `models/${name}`;
  }
}
