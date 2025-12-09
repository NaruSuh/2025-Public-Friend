/**
 * Query Tester
 * Tests generated prompts against naPO API and collects results
 */

import axios, { AxiosInstance } from 'axios';
import { GeneratedPrompt, TestResult, ParsedQueryResult } from './types';

export class QueryTester {
  private client: AxiosInstance;
  private verbose: boolean;

  constructor(napoBaseUrl: string, options: { verbose?: boolean } = {}) {
    this.client = axios.create({
      baseURL: napoBaseUrl,
      timeout: 120000, // 2 minutes for long-running queries
      headers: {
        'Content-Type': 'application/json',
      },
    });
    this.verbose = options.verbose ?? false;
  }

  /**
   * Test a single prompt against naPO API
   */
  async testQuery(prompt: GeneratedPrompt): Promise<TestResult> {
    const timestamp = new Date().toISOString();

    if (this.verbose) {
      console.log(`[QueryTester] Testing: "${prompt.query}"`);
    }

    // Phase 1: Parse the query
    const parseStart = Date.now();
    let parseSuccess = false;
    let parsedQuery: ParsedQueryResult | undefined;
    let parseError: string | undefined;

    try {
      const parseResponse = await this.client.post('/query', {
        query: prompt.query,
      });

      if (parseResponse.data?.success && parseResponse.data?.data?.parsedQuery) {
        parseSuccess = true;
        parsedQuery = parseResponse.data.data.parsedQuery;
      } else {
        parseError = 'Parse response did not contain parsedQuery';
      }
    } catch (error: any) {
      parseError = error.response?.data?.error?.message || error.message;
    }

    const parseTime = Date.now() - parseStart;

    // Phase 2: Execute the parsed query (only if parse succeeded)
    const executeStart = Date.now();
    let executeSuccess = false;
    let executeResult: any;
    let executeError: string | undefined;
    let rowCount = 0;
    let debugInfo: Record<string, any> | undefined;

    if (parseSuccess && parsedQuery) {
      try {
        const executeResponse = await this.client.post('/query/execute', {
          parsedQuery,
        });

        if (executeResponse.data?.success) {
          executeSuccess = true;
          executeResult = executeResponse.data.data;

          // Extract row count
          if (executeResult?.data) {
            if (Array.isArray(executeResult.data)) {
              rowCount = executeResult.data.length;
            } else if (executeResult.data?.data && Array.isArray(executeResult.data.data)) {
              rowCount = executeResult.data.data.length;
            } else if (typeof executeResult.data?.totalCount === 'number') {
              rowCount = executeResult.data.totalCount;
            }
          }

          // Extract debug info
          if (executeResult?.metadata?.debug) {
            debugInfo = executeResult.metadata.debug;
          }
        } else {
          executeError = executeResponse.data?.error?.message || 'Execution failed';
        }
      } catch (error: any) {
        executeError = error.response?.data?.error?.message || error.message;
      }
    } else {
      executeError = 'Skipped due to parse failure';
    }

    const executeTime = Date.now() - executeStart;

    const result: TestResult = {
      promptId: prompt.id,
      query: prompt.query,
      parseSuccess,
      parsedQuery,
      parseError,
      parseTime,
      executeSuccess,
      executeResult,
      executeError,
      executeTime,
      rowCount,
      timestamp,
      debugInfo,
    };

    if (this.verbose) {
      console.log(
        `[QueryTester] Result: parse=${parseSuccess}, execute=${executeSuccess}, rows=${rowCount}`
      );
    }

    return result;
  }

  /**
   * Test multiple prompts in sequence
   */
  async testBatch(
    prompts: GeneratedPrompt[],
    delayMs: number = 0
  ): Promise<TestResult[]> {
    const results: TestResult[] = [];

    for (let i = 0; i < prompts.length; i++) {
      const prompt = prompts[i];
      const result = await this.testQuery(prompt);
      results.push(result);

      // Delay between requests if specified
      if (delayMs > 0 && i < prompts.length - 1) {
        await this.sleep(delayMs);
      }
    }

    return results;
  }

  /**
   * Health check for naPO API
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.client.get('/health');
      return response.status === 200;
    } catch {
      // Try a simple query as fallback health check
      try {
        await this.client.post('/query', { query: 'test' });
        return true;
      } catch {
        return false;
      }
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
