/**
 * Auto Debug Collector
 * Main orchestrator for automated debug data collection
 */

import { AutoDebugConfig, CollectorStats, GeneratedPrompt, PromptCategory, GeminiModelConfig } from './types';
import { DEFAULT_CONFIG, DEFAULT_GEMINI_CONFIG } from './config';
import { RateLimiter, createGeminiRateLimiter } from './RateLimiter';
import { PromptGenerator } from './PromptGenerator';
import { QueryTester } from './QueryTester';
import { ResultAnalyzer } from './ResultAnalyzer';

// Extended config for model comparison tests
interface ExtendedAutoDebugConfig extends AutoDebugConfig {
  modelConfig?: Partial<GeminiModelConfig>;
}

export class AutoDebugCollector {
  private config: Required<AutoDebugConfig>;
  private modelConfig?: Partial<GeminiModelConfig>;
  private rateLimiter: RateLimiter;
  private promptGenerator: PromptGenerator;
  private queryTester: QueryTester;
  private resultAnalyzer: ResultAnalyzer;

  private isRunning: boolean = false;
  private shouldStop: boolean = false;
  private startTime: Date | null = null;

  // Stats
  private stats: CollectorStats = {
    promptsGenerated: 0,
    testsExecuted: 0,
    parseSuccess: 0,
    parseFailed: 0,
    executeSuccess: 0,
    executeFailed: 0,
    edgeCasesFound: 0,
    startTime: '',
    runtimeSeconds: 0,
    isRunning: false,
  };

  constructor(config: ExtendedAutoDebugConfig) {
    // Merge with defaults
    this.config = {
      ...DEFAULT_CONFIG,
      ...config,
      maxIterations: config.maxIterations ?? DEFAULT_CONFIG.maxIterations ?? 100,
      verbose: config.verbose ?? DEFAULT_CONFIG.verbose ?? false,
      domains: config.domains ?? (DEFAULT_CONFIG.domains as PromptCategory[]),
    } as Required<AutoDebugConfig>;

    // Store model config for comparison tests
    this.modelConfig = config.modelConfig;

    // Initialize rate limiter (shared for Gemini calls)
    this.rateLimiter = createGeminiRateLimiter();

    // Initialize components with optional model config
    this.promptGenerator = new PromptGenerator(
      this.config.geminiApiKey,
      this.rateLimiter,
      {
        verbose: this.config.verbose,
        modelConfig: this.modelConfig,
      }
    );

    this.queryTester = new QueryTester(this.config.napoBaseUrl, {
      verbose: this.config.verbose,
    });

    this.resultAnalyzer = new ResultAnalyzer(this.config.testTempDir, {
      verbose: this.config.verbose,
    });
  }

  /**
   * Start the automated collection process
   */
  async start(): Promise<void> {
    if (this.isRunning) {
      console.warn('[AutoDebugCollector] Already running');
      return;
    }

    this.isRunning = true;
    this.shouldStop = false;
    this.startTime = new Date();
    this.stats.startTime = this.startTime.toISOString();
    this.stats.isRunning = true;

    this.log('info', 'Starting auto debug collection', {
      config: {
        napoBaseUrl: this.config.napoBaseUrl,
        promptsPerMinute: this.config.promptsPerMinute,
        maxIterations: this.config.maxIterations,
        domains: this.config.domains,
      },
    });

    // Check naPO health
    const isHealthy = await this.queryTester.healthCheck();
    if (!isHealthy) {
      this.log('error', 'naPO API is not responding');
      this.isRunning = false;
      this.stats.isRunning = false;
      throw new Error('naPO API is not responding');
    }

    this.log('info', 'naPO API health check passed');

    // Main collection loop
    let iteration = 0;
    const maxIterations = this.config.maxIterations;
    const intervalMs = 60000 / this.config.promptsPerMinute; // Time between batches

    while (!this.shouldStop && (maxIterations === 0 || iteration < maxIterations)) {
      try {
        await this.runIteration(iteration);
        iteration++;

        // Update stats
        this.updateStats();

        // Wait before next iteration
        if (!this.shouldStop && (maxIterations === 0 || iteration < maxIterations)) {
          await this.sleep(intervalMs);
        }
      } catch (error: any) {
        this.log('error', `Iteration ${iteration} failed: ${error.message}`);
        // Continue to next iteration on error
        iteration++;
        await this.sleep(intervalMs);
      }
    }

    // Generate final summary
    const summary = await this.resultAnalyzer.generateSummary();
    this.log('info', 'Collection completed', { summary });

    this.isRunning = false;
    this.stats.isRunning = false;
  }

  /**
   * Run a single iteration (generate prompts, test, analyze)
   */
  private async runIteration(iteration: number): Promise<void> {
    this.log('debug', `Starting iteration ${iteration}`);

    // Step 1: Generate prompts (uses 1 Gemini call for 4 prompts)
    const prompts = await this.promptGenerator.generatePrompts(
      this.config.promptsPerMinute,
      this.config.domains
    );

    this.stats.promptsGenerated += prompts.length;
    this.log('info', `Generated ${prompts.length} prompts`);

    // Step 2: Test each prompt (each test uses 1 Gemini call via naPO parse)
    for (const prompt of prompts) {
      if (this.shouldStop) break;

      try {
        // Rate limit for naPO parse (which uses Gemini)
        await this.rateLimiter.acquire();

        const result = await this.queryTester.testQuery(prompt);
        this.stats.testsExecuted++;

        // Update success/fail counts
        if (result.parseSuccess) {
          this.stats.parseSuccess++;
        } else {
          this.stats.parseFailed++;
        }

        if (result.executeSuccess) {
          this.stats.executeSuccess++;
        } else {
          this.stats.executeFailed++;
        }

        // Check for edge case
        if (prompt.difficulty === 'edge_case' || prompt.category === 'edge_case') {
          this.stats.edgeCasesFound++;
        }

        // Step 3: Analyze and save results
        const row = await this.resultAnalyzer.analyze(prompt, result);
        await this.resultAnalyzer.appendToCSV(row);

        this.log('debug', `Tested: "${prompt.query}" -> success=${result.executeSuccess}`);
      } catch (error: any) {
        this.log('error', `Test failed for prompt ${prompt.id}: ${error.message}`);
        this.stats.parseFailed++;
      }
    }
  }

  /**
   * Stop the collection process gracefully
   */
  stop(): void {
    this.log('info', 'Stop requested');
    this.shouldStop = true;
  }

  /**
   * Get current statistics
   */
  getStats(): CollectorStats {
    this.updateStats();
    return { ...this.stats };
  }

  /**
   * Update runtime in stats
   */
  private updateStats(): void {
    if (this.startTime) {
      this.stats.runtimeSeconds = Math.floor(
        (Date.now() - this.startTime.getTime()) / 1000
      );
    }
  }

  /**
   * Cleanup test_temp directory
   */
  async cleanup(): Promise<void> {
    const fs = await import('fs');
    const path = await import('path');

    const testTempDir = this.config.testTempDir;

    if (fs.existsSync(testTempDir)) {
      // Recursively delete directory
      fs.rmSync(testTempDir, { recursive: true, force: true });
      this.log('info', `Cleaned up ${testTempDir}`);
    }
  }

  /**
   * Get the result analyzer for accessing summary
   */
  getResultAnalyzer(): ResultAnalyzer {
    return this.resultAnalyzer;
  }

  /**
   * Log message
   */
  private log(
    level: 'debug' | 'info' | 'warn' | 'error',
    message: string,
    data?: any
  ): void {
    this.resultAnalyzer.log(level, message, data);

    if (this.config.verbose || level === 'error' || level === 'warn') {
      const prefix = `[AutoDebugCollector]`;
      if (level === 'error') {
        console.error(`${prefix} ${message}`, data || '');
      } else if (level === 'warn') {
        console.warn(`${prefix} ${message}`, data || '');
      } else {
        console.log(`${prefix} ${message}`, data || '');
      }
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
