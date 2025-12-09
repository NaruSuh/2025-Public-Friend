/**
 * Rate Limiter
 * Token bucket algorithm for API rate limiting
 */

import { RateLimiterConfig } from './types';

export class RateLimiter {
  private maxCalls: number;
  private windowMs: number;
  private timestamps: number[] = [];

  constructor(config: RateLimiterConfig) {
    this.maxCalls = config.maxCallsPerMinute;
    this.windowMs = config.windowMs ?? 60000; // Default 1 minute
  }

  /**
   * Acquire a token - waits if rate limit exceeded
   */
  async acquire(): Promise<void> {
    const now = Date.now();

    // Remove expired timestamps
    this.timestamps = this.timestamps.filter(
      (ts) => now - ts < this.windowMs
    );

    // If at capacity, wait until oldest expires
    if (this.timestamps.length >= this.maxCalls) {
      const oldestTimestamp = this.timestamps[0];
      const waitTime = this.windowMs - (now - oldestTimestamp) + 100; // Add 100ms buffer

      if (waitTime > 0) {
        await this.sleep(waitTime);
        return this.acquire(); // Retry after waiting
      }
    }

    // Record this call
    this.timestamps.push(Date.now());
  }

  /**
   * Acquire with exponential backoff retry
   * @param maxRetries Maximum number of retries (default: 3)
   * @returns Promise that resolves when token acquired
   * @throws Error if max retries exceeded
   */
  async acquireWithRetry(maxRetries: number = 3): Promise<void> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        await this.acquire();
        return;
      } catch (error) {
        lastError = error as Error;
        const delay = Math.pow(2, attempt) * 1000; // 1s, 2s, 4s exponential backoff
        console.log(`[RateLimiter] Retry ${attempt + 1}/${maxRetries} after ${delay}ms`);
        await this.sleep(delay);
      }
    }

    throw new Error(`Rate limit exceeded after ${maxRetries} retries: ${lastError?.message}`);
  }

  /**
   * Try to acquire without waiting
   * @returns true if acquired, false if rate limited
   */
  tryAcquire(): boolean {
    const now = Date.now();

    // Remove expired timestamps
    this.timestamps = this.timestamps.filter(
      (ts) => now - ts < this.windowMs
    );

    if (this.timestamps.length >= this.maxCalls) {
      return false;
    }

    this.timestamps.push(now);
    return true;
  }

  /**
   * Get remaining calls in current window
   */
  getRemaining(): number {
    const now = Date.now();
    this.timestamps = this.timestamps.filter(
      (ts) => now - ts < this.windowMs
    );
    return Math.max(0, this.maxCalls - this.timestamps.length);
  }

  /**
   * Get time until next slot available (in ms)
   */
  getWaitTime(): number {
    if (this.getRemaining() > 0) {
      return 0;
    }

    const now = Date.now();
    const oldestTimestamp = this.timestamps[0];
    return Math.max(0, this.windowMs - (now - oldestTimestamp));
  }

  /**
   * Reset the rate limiter
   */
  reset(): void {
    this.timestamps = [];
  }

  /**
   * Get current state info
   */
  getState(): {
    used: number;
    remaining: number;
    maxCalls: number;
    windowMs: number;
    waitTimeMs: number;
  } {
    return {
      used: this.timestamps.length,
      remaining: this.getRemaining(),
      maxCalls: this.maxCalls,
      windowMs: this.windowMs,
      waitTimeMs: this.getWaitTime(),
    };
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

/**
 * Shared rate limiter for Gemini API (10 calls/min)
 */
export function createGeminiRateLimiter(): RateLimiter {
  return new RateLimiter({ maxCallsPerMinute: 10 });
}
