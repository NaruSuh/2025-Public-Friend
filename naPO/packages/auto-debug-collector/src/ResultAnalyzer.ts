/**
 * Result Analyzer
 * Analyzes test results and writes to CSV
 */

import * as fs from 'fs';
import * as path from 'path';
import {
  GeneratedPrompt,
  TestResult,
  AnalysisRow,
  AnalysisSummary,
  PromptCategory,
} from './types';
import { CSV_HEADER, DIRS, FILES } from './config';

export class ResultAnalyzer {
  private testTempDir: string;
  private verbose: boolean;
  private analysisRows: AnalysisRow[] = [];

  constructor(testTempDir: string, options: { verbose?: boolean } = {}) {
    this.testTempDir = testTempDir;
    this.verbose = options.verbose ?? false;
    this.ensureDirectories();
  }

  /**
   * Ensure all required directories exist
   */
  private ensureDirectories(): void {
    const dirs = [
      this.testTempDir,
      path.join(this.testTempDir, DIRS.prompts),
      path.join(this.testTempDir, DIRS.responses),
      path.join(this.testTempDir, DIRS.logs),
    ];

    for (const dir of dirs) {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    }

    // Initialize CSV with header if not exists
    const csvPath = path.join(this.testTempDir, FILES.analysisCSV);
    if (!fs.existsSync(csvPath)) {
      fs.writeFileSync(csvPath, CSV_HEADER + '\n', 'utf-8');
    }
  }

  /**
   * Analyze a single test result
   */
  async analyze(prompt: GeneratedPrompt, result: TestResult): Promise<AnalysisRow> {
    // Save prompt to file
    const promptFile = path.join(DIRS.prompts, `${prompt.id}.json`);
    const promptPath = path.join(this.testTempDir, promptFile);
    fs.writeFileSync(promptPath, JSON.stringify(prompt, null, 2), 'utf-8');

    // Save response to file
    const responseFile = path.join(DIRS.responses, `${prompt.id}.json`);
    const responsePath = path.join(this.testTempDir, responseFile);
    fs.writeFileSync(responsePath, JSON.stringify(result, null, 2), 'utf-8');

    // Extract parsed values
    const parseIntent = result.parsedQuery?.intent || '';
    const parseSource = result.parsedQuery?.source?.id || '';
    const parseConfidence = result.parsedQuery?.confidence || 0;

    // Check matches
    const intentMatch = parseIntent === prompt.expectedIntent;
    const sourceMatch = parseSource === prompt.expectedSource;
    const isEdgeCase = prompt.difficulty === 'edge_case' || prompt.category === 'edge_case';

    const row: AnalysisRow = {
      test_id: prompt.id,
      timestamp: result.timestamp,
      query: prompt.query,
      category: prompt.category,
      difficulty: prompt.difficulty,
      parse_success: result.parseSuccess,
      parse_intent: parseIntent,
      parse_source: parseSource,
      parse_confidence: parseConfidence,
      parse_error: result.parseError || '',
      parse_time_ms: result.parseTime,
      execute_success: result.executeSuccess,
      execute_row_count: result.rowCount,
      execute_error: result.executeError || '',
      execute_time_ms: result.executeTime,
      expected_intent: prompt.expectedIntent,
      expected_source: prompt.expectedSource,
      intent_match: intentMatch,
      source_match: sourceMatch,
      is_edge_case: isEdgeCase,
      prompt_file: promptFile,
      response_file: responseFile,
    };

    this.analysisRows.push(row);

    if (this.verbose) {
      console.log(
        `[ResultAnalyzer] Analyzed: ${prompt.id}, intent_match=${intentMatch}, source_match=${sourceMatch}`
      );
    }

    return row;
  }

  /**
   * Append a row to CSV file
   */
  async appendToCSV(row: AnalysisRow): Promise<void> {
    const csvPath = path.join(this.testTempDir, FILES.analysisCSV);

    const csvRow = [
      row.test_id,
      row.timestamp,
      this.escapeCSV(row.query),
      row.category,
      row.difficulty,
      row.parse_success,
      row.parse_intent,
      row.parse_source,
      row.parse_confidence,
      this.escapeCSV(row.parse_error),
      row.parse_time_ms,
      row.execute_success,
      row.execute_row_count,
      this.escapeCSV(row.execute_error),
      row.execute_time_ms,
      row.expected_intent,
      row.expected_source,
      row.intent_match,
      row.source_match,
      row.is_edge_case,
      row.prompt_file,
      row.response_file,
    ].join(',');

    fs.appendFileSync(csvPath, csvRow + '\n', 'utf-8');
  }

  /**
   * Generate summary statistics
   */
  async generateSummary(): Promise<AnalysisSummary> {
    const total = this.analysisRows.length;

    if (total === 0) {
      return this.getEmptySummary();
    }

    // Calculate rates
    const parseSuccessCount = this.analysisRows.filter((r) => r.parse_success).length;
    const executeSuccessCount = this.analysisRows.filter((r) => r.execute_success).length;
    const intentMatchCount = this.analysisRows.filter((r) => r.intent_match).length;
    const sourceMatchCount = this.analysisRows.filter((r) => r.source_match).length;

    // Calculate averages
    const avgParseTime =
      this.analysisRows.reduce((sum, r) => sum + r.parse_time_ms, 0) / total;
    const avgExecuteTime =
      this.analysisRows.reduce((sum, r) => sum + r.execute_time_ms, 0) / total;

    // Count edge cases
    const edgeCases = this.analysisRows.filter((r) => r.is_edge_case);

    // Find error patterns
    const errorPatterns = this.findErrorPatterns();

    // Category breakdown
    const categoryBreakdown = this.getCategoryBreakdown();

    const summary: AnalysisSummary = {
      totalTests: total,
      parseSuccessRate: parseSuccessCount / total,
      executeSuccessRate: executeSuccessCount / total,
      intentMatchRate: intentMatchCount / total,
      sourceMatchRate: sourceMatchCount / total,
      averageParseTime: Math.round(avgParseTime),
      averageExecuteTime: Math.round(avgExecuteTime),
      edgeCasesFound: edgeCases.length,
      errorPatterns,
      categoryBreakdown,
    };

    // Save summary to file
    const summaryPath = path.join(this.testTempDir, FILES.summaryJSON);
    fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2), 'utf-8');

    return summary;
  }

  /**
   * Find common error patterns
   */
  private findErrorPatterns(): AnalysisSummary['errorPatterns'] {
    const errorMap = new Map<string, { count: number; examples: string[] }>();

    for (const row of this.analysisRows) {
      const error = row.parse_error || row.execute_error;
      if (!error) continue;

      // Normalize error message (remove specific IDs, timestamps, etc.)
      const pattern = this.normalizeErrorPattern(error);

      if (!errorMap.has(pattern)) {
        errorMap.set(pattern, { count: 0, examples: [] });
      }

      const entry = errorMap.get(pattern)!;
      entry.count++;
      if (entry.examples.length < 3) {
        entry.examples.push(row.query);
      }
    }

    return Array.from(errorMap.entries())
      .map(([pattern, data]) => ({
        pattern,
        count: data.count,
        examples: data.examples,
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10); // Top 10 patterns
  }

  /**
   * Normalize error message to find patterns
   */
  private normalizeErrorPattern(error: string): string {
    return error
      .replace(/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z/g, '[TIMESTAMP]')
      .replace(/\d{8}/g, '[DATE]')
      .replace(/prompt_\d+_\d+/g, '[PROMPT_ID]')
      .replace(/"[^"]*"/g, '"[STRING]"')
      .substring(0, 100);
  }

  /**
   * Get breakdown by category
   */
  private getCategoryBreakdown(): AnalysisSummary['categoryBreakdown'] {
    const categories: PromptCategory[] = [
      'election',
      'policy',
      'candidate',
      'party',
      'statistics',
      'edge_case',
    ];

    const breakdown: AnalysisSummary['categoryBreakdown'] = {} as any;

    for (const category of categories) {
      const rows = this.analysisRows.filter((r) => r.category === category);
      breakdown[category] = {
        total: rows.length,
        success: rows.filter((r) => r.execute_success).length,
        failed: rows.filter((r) => !r.execute_success).length,
      };
    }

    return breakdown;
  }

  /**
   * Get empty summary template
   */
  private getEmptySummary(): AnalysisSummary {
    return {
      totalTests: 0,
      parseSuccessRate: 0,
      executeSuccessRate: 0,
      intentMatchRate: 0,
      sourceMatchRate: 0,
      averageParseTime: 0,
      averageExecuteTime: 0,
      edgeCasesFound: 0,
      errorPatterns: [],
      categoryBreakdown: {
        election: { total: 0, success: 0, failed: 0 },
        policy: { total: 0, success: 0, failed: 0 },
        candidate: { total: 0, success: 0, failed: 0 },
        party: { total: 0, success: 0, failed: 0 },
        statistics: { total: 0, success: 0, failed: 0 },
        edge_case: { total: 0, success: 0, failed: 0 },
      },
    };
  }

  /**
   * Escape CSV value
   */
  private escapeCSV(value: string): string {
    if (value.includes(',') || value.includes('"') || value.includes('\n')) {
      return `"${value.replace(/"/g, '""')}"`;
    }
    return value;
  }

  /**
   * Write log entry
   */
  log(level: 'debug' | 'info' | 'warn' | 'error', message: string, data?: any): void {
    const logPath = path.join(this.testTempDir, DIRS.logs, FILES.runLog);
    const entry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      data,
    };

    const logLine = JSON.stringify(entry) + '\n';
    fs.appendFileSync(logPath, logLine, 'utf-8');

    if (this.verbose || level === 'error') {
      console.log(`[${level.toUpperCase()}] ${message}`, data || '');
    }
  }

  /**
   * Get all analysis rows
   */
  getRows(): AnalysisRow[] {
    return [...this.analysisRows];
  }

  /**
   * Clear analysis rows (for testing)
   */
  clearRows(): void {
    this.analysisRows = [];
  }
}
