import { GoogleGenerativeAI, GenerativeModel } from '@google/generative-ai';
import { withRetry, RetryConfig } from './openaiRetry';

/**
 * Gemini API Client with Retry Logic
 * OpenAI 호환 인터페이스 제공
 */

export interface GeminiChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface GeminiChatResponse {
  id: string;
  choices: Array<{
    message: {
      role: string;
      content: string | null;
    };
    finish_reason: string;
  }>;
  created: number;
  model: string;
  object: string;
}

export class GeminiClient {
  private genAI: GoogleGenerativeAI;
  private model: GenerativeModel;
  private retryConfig: RetryConfig;

  constructor(apiKey: string, retryConfig: RetryConfig = {}) {
    this.genAI = new GoogleGenerativeAI(apiKey);
    this.model = this.genAI.getGenerativeModel({
      model: 'gemini-2.5-flash',
      generationConfig: {
        temperature: 0.3,
        topP: 1,
        maxOutputTokens: 4096,
      },
    });
    this.retryConfig = { maxRetries: 3, initialDelayMs: 1000, maxDelayMs: 30000, ...retryConfig };
  }

  /**
   * Chat completion with OpenAI-compatible interface
   */
  async chatCompletion(params: {
    model?: string;
    messages: GeminiChatMessage[];
    temperature?: number;
  }): Promise<GeminiChatResponse> {
    return withRetry(async () => {
      // Gemini는 system/user/assistant를 구분하지 않으므로 메시지 병합
      const systemMessages = params.messages.filter((m) => m.role === 'system');
      const userMessages = params.messages.filter((m) => m.role !== 'system');

      let prompt = '';
      if (systemMessages.length > 0) {
        prompt += systemMessages.map((m) => m.content).join('\n\n') + '\n\n';
      }

      // 대화 기록을 하나의 프롬프트로 결합
      prompt += userMessages.map((m) => {
        const prefix = m.role === 'user' ? 'User: ' : 'Assistant: ';
        return prefix + m.content;
      }).join('\n\n');

      // Gemini API 호출
      const result = await this.model.generateContent(prompt);
      const response = result.response;
      const text = response.text();

      // OpenAI 형식으로 변환
      return {
        id: `gemini-${Date.now()}`,
        choices: [
          {
            message: {
              role: 'assistant',
              content: text,
            },
            finish_reason: 'stop',
          },
        ],
        created: Math.floor(Date.now() / 1000),
        model: 'gemini-pro',
        object: 'chat.completion',
      };
    }, this.retryConfig);
  }

  /**
   * Generate structured JSON response
   */
  async generateJSON(params: {
    messages: GeminiChatMessage[];
    temperature?: number;
  }): Promise<any> {
    const response = await this.chatCompletion(params);
    const content = response.choices[0]?.message?.content;

    if (!content) {
      throw new Error('Empty response from Gemini');
    }

    try {
      // Gemini가 ```json ... ``` 로 감싸서 반환할 경우 처리
      let jsonContent = content.trim();
      if (jsonContent.startsWith('```json')) {
        jsonContent = jsonContent.replace(/^```json\n?/, '').replace(/\n?```$/, '').trim();
      } else if (jsonContent.startsWith('```')) {
        jsonContent = jsonContent.replace(/^```\n?/, '').replace(/\n?```$/, '').trim();
      }

      // JSON 응답 파싱
      return JSON.parse(jsonContent);
    } catch (error) {
      // JSON 파싱 실패 시 로그 출력
      console.warn('Failed to parse JSON response, retrying...');
      console.warn('Raw response:', content);
      throw new Error('Failed to parse JSON response from Gemini');
    }
  }
}
