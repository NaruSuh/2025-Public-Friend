import { env } from '@/config/env';
import { getApiKey as getDbApiKey } from './apiKeyHelper';

/**
 * Unified API Key Manager
 *
 * 환경변수와 DB에 저장된 암호화 키를 통합 관리합니다.
 * 우선순위: DB 저장 키 > 환경변수 키
 */

export interface ApiKeySource {
  key: string;
  source: 'database' | 'environment';
  encrypted: boolean;
}

export class UnifiedApiKeyManager {
  private static cache: Map<string, ApiKeySource> = new Map();
  private static cacheTimeout = 5 * 60 * 1000; // 5 minutes
  private static cacheTimestamps: Map<string, number> = new Map();

  /**
   * Get API key from DB or environment variable
   * Priority: DB > Environment Variable
   */
  static async getKey(sourceName: string): Promise<ApiKeySource | null> {
    // Check cache
    if (this.isCacheValid(sourceName)) {
      return this.cache.get(sourceName) || null;
    }

    // Try database first
    try {
      const dbKey = await getDbApiKey(sourceName);
      if (dbKey) {
        const result: ApiKeySource = {
          key: dbKey,
          source: 'database',
          encrypted: true, // DB keys are always encrypted/decrypted
        };
        this.updateCache(sourceName, result);
        return result;
      }
    } catch (error) {
      console.warn(`Failed to get API key from database for ${sourceName}:`, error);
    }

    // Fallback to environment variable
    const envKey = this.getEnvKey(sourceName);
    if (envKey) {
      const result: ApiKeySource = {
        key: envKey,
        source: 'environment',
        encrypted: false,
      };
      this.updateCache(sourceName, result);
      return result;
    }

    return null;
  }

  /**
   * Get raw API key string (for backward compatibility)
   */
  static async getKeyString(sourceName: string): Promise<string | null> {
    const keySource = await this.getKey(sourceName);
    return keySource?.key || null;
  }

  /**
   * Get environment variable API key
   */
  private static getEnvKey(sourceName: string): string | null {
    const envMap: Record<string, string | undefined> = {
      'public_data': env.PUBLIC_DATA_API_KEY,
      'nabostats': env.NABOSTATS_API_KEY,
      'nec_manifesto': env.NEC_MANIFESTO_API_KEY,
      'rone': env.RONE_API_KEY,
      'openai': env.OPENAI_API_KEY,
      'youtube': env.YOUTUBE_API_KEY,
    };

    return envMap[sourceName] || null;
  }

  /**
   * Cache management
   */
  private static isCacheValid(sourceName: string): boolean {
    const timestamp = this.cacheTimestamps.get(sourceName);
    if (!timestamp) return false;
    return Date.now() - timestamp < this.cacheTimeout;
  }

  private static updateCache(sourceName: string, keySource: ApiKeySource): void {
    this.cache.set(sourceName, keySource);
    this.cacheTimestamps.set(sourceName, Date.now());
  }

  /**
   * Clear cache for a specific source or all sources
   */
  static clearCache(sourceName?: string): void {
    if (sourceName) {
      this.cache.delete(sourceName);
      this.cacheTimestamps.delete(sourceName);
    } else {
      this.cache.clear();
      this.cacheTimestamps.clear();
    }
  }

  /**
   * Check if API key is available
   */
  static async hasKey(sourceName: string): Promise<boolean> {
    const keySource = await this.getKey(sourceName);
    return keySource !== null;
  }

  /**
   * Get all available API sources
   */
  static async getAvailableSources(): Promise<string[]> {
    const sources = ['public_data', 'nabostats', 'nec_manifesto', 'rone', 'openai', 'youtube'];
    const available: string[] = [];

    for (const source of sources) {
      if (await this.hasKey(source)) {
        available.push(source);
      }
    }

    return available;
  }
}
