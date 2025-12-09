/**
 * Prompt Generator
 * Uses Gemini to generate diverse test prompts for naPO
 * Supports model fallback: 2.0 Flash (primary) → 2.5 Flash (fallback)
 */

import { GoogleGenerativeAI, GenerativeModel } from '@google/generative-ai';
import { GeneratedPrompt, PromptCategory, PromptDifficulty, GeminiModelConfig, GeminiModelId, GEMINI_MODELS } from './types';
import { PROMPT_GENERATION_SYSTEM, DEFAULT_GEMINI_CONFIG } from './config';
import { RateLimiter } from './RateLimiter';

export class PromptGenerator {
  private genAI: GoogleGenerativeAI;
  private primaryModel: GenerativeModel;
  private fallbackModel: GenerativeModel;
  private currentModel: 'primary' | 'fallback' = 'primary';
  private modelConfig: GeminiModelConfig;
  private rateLimiter: RateLimiter;
  private promptCounter: number = 0;
  private verbose: boolean;

  // Quota tracking
  private primaryQuotaExhausted: boolean = false;
  private primaryCooldownUntil: number = 0;
  private modelStats = {
    primaryCalls: 0,
    fallbackCalls: 0,
    primaryErrors: 0,
    fallbackErrors: 0,
  };

  constructor(
    apiKey: string,
    rateLimiter: RateLimiter,
    options: { verbose?: boolean; modelConfig?: Partial<GeminiModelConfig> } = {}
  ) {
    this.genAI = new GoogleGenerativeAI(apiKey);
    this.modelConfig = { ...DEFAULT_GEMINI_CONFIG, ...options.modelConfig };

    // Initialize primary model (2.0 Flash - lower token usage)
    this.primaryModel = this.genAI.getGenerativeModel({
      model: this.modelConfig.primaryModel,
      generationConfig: {
        temperature: 0.8,
        topP: 0.95,
        maxOutputTokens: 2048,
      },
    });

    // Initialize fallback model (2.5 Flash - higher capability)
    this.fallbackModel = this.genAI.getGenerativeModel({
      model: this.modelConfig.fallbackModel,
      generationConfig: {
        temperature: 0.8,
        topP: 0.95,
        maxOutputTokens: 2048,
      },
    });

    this.rateLimiter = rateLimiter;
    this.verbose = options.verbose ?? false;

    if (this.verbose) {
      console.log(`[PromptGenerator] Initialized with models:`);
      console.log(`  Primary: ${GEMINI_MODELS[this.modelConfig.primaryModel].name}`);
      console.log(`  Fallback: ${GEMINI_MODELS[this.modelConfig.fallbackModel].name}`);
    }
  }

  /**
   * Get the current active model based on quota status
   */
  private getActiveModel(): GenerativeModel {
    // Check if primary cooldown has expired
    if (this.primaryQuotaExhausted && Date.now() > this.primaryCooldownUntil) {
      this.primaryQuotaExhausted = false;
      this.currentModel = 'primary';
      if (this.verbose) {
        console.log(`[PromptGenerator] Primary model cooldown expired, switching back to ${this.modelConfig.primaryModel}`);
      }
    }

    return this.currentModel === 'primary' ? this.primaryModel : this.fallbackModel;
  }

  /**
   * Handle quota exceeded error - switch to fallback model
   */
  private handleQuotaExceeded(): void {
    if (!this.modelConfig.enableFallback) {
      throw new Error('Gemini quota exceeded and fallback is disabled');
    }

    this.primaryQuotaExhausted = true;
    this.primaryCooldownUntil = Date.now() + this.modelConfig.primaryCooldownMs;
    this.currentModel = 'fallback';

    if (this.verbose) {
      const cooldownSec = Math.round(this.modelConfig.primaryCooldownMs / 1000);
      console.log(`[PromptGenerator] ⚠️ Primary model quota exceeded!`);
      console.log(`[PromptGenerator] Switching to fallback: ${this.modelConfig.fallbackModel}`);
      console.log(`[PromptGenerator] Will retry primary in ${cooldownSec}s`);
    }
  }

  /**
   * Check if an error is a quota/rate limit error
   */
  private isQuotaError(error: any): boolean {
    const message = error.message?.toLowerCase() || '';
    return (
      message.includes('quota') ||
      message.includes('rate limit') ||
      message.includes('resource exhausted') ||
      message.includes('429') ||
      error.status === 429
    );
  }

  /**
   * Get current model statistics
   */
  getModelStats(): typeof this.modelStats & { currentModel: string } {
    return {
      ...this.modelStats,
      currentModel: this.currentModel === 'primary'
        ? this.modelConfig.primaryModel
        : this.modelConfig.fallbackModel,
    };
  }

  /**
   * Generate test prompts using Gemini with automatic model fallback
   * @param count Number of prompts to generate
   * @param categories Categories to focus on
   */
  async generatePrompts(
    count: number = 4,
    categories?: PromptCategory[]
  ): Promise<GeneratedPrompt[]> {
    // Wait for rate limit
    await this.rateLimiter.acquire();

    const categoryHint = categories?.length
      ? `이번에는 특히 ${categories.join(', ')} 카테고리에 집중해주세요.`
      : '다양한 카테고리를 골고루 포함해주세요.';

    const userPrompt = `${count}개의 테스트 질문을 생성해주세요.
${categoryHint}
난이도도 다양하게 섞어주세요. 특히 edge_case는 최소 1개 포함해주세요.`;

    // Try with current model (with fallback support)
    return this.generateWithFallback(userPrompt, count);
  }

  /**
   * Generate content with automatic fallback to secondary model
   */
  private async generateWithFallback(userPrompt: string, count: number): Promise<GeneratedPrompt[]> {
    const model = this.getActiveModel();
    const modelName = this.currentModel === 'primary'
      ? this.modelConfig.primaryModel
      : this.modelConfig.fallbackModel;

    try {
      if (this.verbose) {
        console.log(`[PromptGenerator] Generating ${count} prompts using ${modelName}...`);
      }

      const result = await model.generateContent([
        { text: PROMPT_GENERATION_SYSTEM },
        { text: userPrompt },
      ]);

      // Track successful call
      if (this.currentModel === 'primary') {
        this.modelStats.primaryCalls++;
      } else {
        this.modelStats.fallbackCalls++;
      }

      const response = result.response.text();
      const prompts = this.parseResponse(response);

      if (this.verbose) {
        console.log(`[PromptGenerator] ✓ Generated ${prompts.length} prompts with ${modelName}`);
      }

      return prompts;
    } catch (error: any) {
      // Track error
      if (this.currentModel === 'primary') {
        this.modelStats.primaryErrors++;
      } else {
        this.modelStats.fallbackErrors++;
      }

      // Check if it's a quota error and we can fallback
      if (this.isQuotaError(error) && this.currentModel === 'primary' && this.modelConfig.enableFallback) {
        console.warn(`[PromptGenerator] ⚠️ ${modelName} quota exceeded, switching to fallback...`);
        this.handleQuotaExceeded();

        // Retry with fallback model
        return this.generateWithFallback(userPrompt, count);
      }

      // If we're already on fallback or it's not a quota error, log and return fallback prompts
      console.error(`[PromptGenerator] Generation failed on ${modelName}:`, error.message);
      return this.getFallbackPrompts(count);
    }
  }

  /**
   * Parse Gemini response to GeneratedPrompt array
   */
  private parseResponse(response: string): GeneratedPrompt[] {
    try {
      // Clean up response (remove markdown code blocks if present)
      let jsonContent = response.trim();
      if (jsonContent.startsWith('```json')) {
        jsonContent = jsonContent.replace(/^```json\n?/, '').replace(/\n?```$/, '').trim();
      } else if (jsonContent.startsWith('```')) {
        jsonContent = jsonContent.replace(/^```\n?/, '').replace(/\n?```$/, '').trim();
      }

      const parsed = JSON.parse(jsonContent);

      if (!Array.isArray(parsed)) {
        throw new Error('Response is not an array');
      }

      return parsed.map((item: any) => this.normalizePrompt(item));
    } catch (error) {
      console.warn('[PromptGenerator] Failed to parse response, using fallback');
      return this.getFallbackPrompts(4);
    }
  }

  /**
   * Normalize and validate a prompt object
   */
  private normalizePrompt(item: any): GeneratedPrompt {
    this.promptCounter++;
    const id = `prompt_${Date.now()}_${this.promptCounter.toString().padStart(4, '0')}`;

    return {
      id,
      query: String(item.query || ''),
      expectedIntent: this.normalizeIntent(item.expectedIntent),
      expectedSource: this.normalizeSource(item.expectedSource),
      difficulty: this.normalizeDifficulty(item.difficulty),
      category: this.normalizeCategory(item.category),
      timestamp: new Date().toISOString(),
      metadata: {
        rawGenerated: item,
      },
    };
  }

  private normalizeIntent(intent: string): string {
    const validIntents = ['fetch_api', 'crawl_site', 'parse_pdf', 'analyze_data', 'export_data'];
    return validIntents.includes(intent) ? intent : 'fetch_api';
  }

  private normalizeSource(source: string): string {
    const validSources = [
      'public_data_party_policy',
      'public_data_election',
      'public_data_candidate',
      'public_data_winner',
      'rone',
      'nabostats',
    ];
    return validSources.includes(source) ? source : 'public_data_party_policy';
  }

  private normalizeDifficulty(difficulty: string): PromptDifficulty {
    const validDifficulties: PromptDifficulty[] = ['easy', 'medium', 'hard', 'edge_case'];
    return validDifficulties.includes(difficulty as PromptDifficulty)
      ? (difficulty as PromptDifficulty)
      : 'medium';
  }

  private normalizeCategory(category: string): PromptCategory {
    const validCategories: PromptCategory[] = [
      'election',
      'policy',
      'candidate',
      'party',
      'statistics',
      'edge_case',
    ];
    return validCategories.includes(category as PromptCategory)
      ? (category as PromptCategory)
      : 'election';
  }

  /**
   * Get fallback prompts when Gemini fails
   */
  private getFallbackPrompts(count: number): GeneratedPrompt[] {
    const fallbacks: Array<Omit<GeneratedPrompt, 'id' | 'timestamp'>> = [
      {
        query: '2022년 지방선거 주요정당 공약',
        expectedIntent: 'fetch_api',
        expectedSource: 'public_data_party_policy',
        difficulty: 'easy',
        category: 'policy',
      },
      {
        query: '윤석열 대선 공약',
        expectedIntent: 'fetch_api',
        expectedSource: 'public_data_election',
        difficulty: 'medium',
        category: 'candidate',
      },
      {
        query: '지난 10년 선거 목록',
        expectedIntent: 'fetch_api',
        expectedSource: 'public_data_election',
        difficulty: 'hard',
        category: 'election',
      },
      {
        query: '공약',
        expectedIntent: 'fetch_api',
        expectedSource: 'public_data_party_policy',
        difficulty: 'edge_case',
        category: 'edge_case',
      },
      {
        query: '더불어민주당 2024 공약 요약',
        expectedIntent: 'fetch_api',
        expectedSource: 'public_data_party_policy',
        difficulty: 'medium',
        category: 'party',
      },
      {
        query: '2020년 총선 후보자 목록',
        expectedIntent: 'fetch_api',
        expectedSource: 'public_data_candidate',
        difficulty: 'easy',
        category: 'candidate',
      },
      {
        query: '지방서거 결과',
        expectedIntent: 'fetch_api',
        expectedSource: 'public_data_election',
        difficulty: 'edge_case',
        category: 'edge_case',
      },
      {
        query: '국민의힘 정의당 민주당 공약 비교',
        expectedIntent: 'fetch_api',
        expectedSource: 'public_data_party_policy',
        difficulty: 'hard',
        category: 'policy',
      },
    ];

    return fallbacks.slice(0, count).map((item) => {
      this.promptCounter++;
      return {
        ...item,
        id: `prompt_fallback_${this.promptCounter.toString().padStart(4, '0')}`,
        timestamp: new Date().toISOString(),
      };
    });
  }

  /**
   * Get system prompt for customization
   */
  protected getSystemPrompt(): string {
    return PROMPT_GENERATION_SYSTEM;
  }
}
