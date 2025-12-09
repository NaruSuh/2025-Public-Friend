/**
 * Auto Debug Collector Types
 * 재사용 가능한 타입 정의
 */

// ============ Configuration Types ============

export interface AutoDebugConfig {
  /** Gemini API Key */
  geminiApiKey: string;

  /** naPO Backend Base URL (e.g., http://localhost:3001/api/v1) */
  napoBaseUrl: string;

  /** Number of prompts to generate per minute (default: 4) */
  promptsPerMinute: number;

  /** Directory for temporary test data (default: ./test_temp) */
  testTempDir: string;

  /** Maximum iterations before auto-stop (default: 100, 0 for unlimited) */
  maxIterations?: number;

  /** Test domains to generate prompts for */
  domains: PromptCategory[];

  /** Enable verbose logging (default: false) */
  verbose?: boolean;
}

// ============ Prompt Types ============

export type PromptCategory = 'election' | 'policy' | 'candidate' | 'party' | 'statistics' | 'edge_case';
export type PromptDifficulty = 'easy' | 'medium' | 'hard' | 'edge_case';

export interface GeneratedPrompt {
  /** Unique identifier */
  id: string;

  /** Generated Korean query */
  query: string;

  /** Expected intent from parsing */
  expectedIntent: string;

  /** Expected data source */
  expectedSource: string;

  /** Difficulty level */
  difficulty: PromptDifficulty;

  /** Category */
  category: PromptCategory;

  /** Generation timestamp */
  timestamp: string;

  /** Additional metadata */
  metadata?: Record<string, any>;
}

// ============ Test Result Types ============

export interface ParsedQueryResult {
  intent: string;
  confidence: number;
  source: {
    type: string;
    id?: string;
    url?: string;
  };
  filters: Record<string, any>;
  output: {
    format: string;
    fields?: string[];
    limit?: number;
  };
  rawQuery: string;
}

export interface TestResult {
  /** Prompt ID */
  promptId: string;

  /** Original query */
  query: string;

  // Parse Phase
  parseSuccess: boolean;
  parsedQuery?: ParsedQueryResult;
  parseError?: string;
  parseTime: number;

  // Execute Phase
  executeSuccess: boolean;
  executeResult?: any;
  executeError?: string;
  executeTime: number;
  rowCount: number;

  // Metadata
  timestamp: string;
  debugInfo?: Record<string, any>;
}

// ============ Analysis Types ============

export interface AnalysisRow {
  // Identifiers
  test_id: string;
  timestamp: string;

  // Input
  query: string;
  category: string;
  difficulty: string;

  // Parse Results
  parse_success: boolean;
  parse_intent: string;
  parse_source: string;
  parse_confidence: number;
  parse_error: string;
  parse_time_ms: number;

  // Execute Results
  execute_success: boolean;
  execute_row_count: number;
  execute_error: string;
  execute_time_ms: number;

  // Analysis
  expected_intent: string;
  expected_source: string;
  intent_match: boolean;
  source_match: boolean;
  is_edge_case: boolean;

  // File References
  prompt_file: string;
  response_file: string;
}

export interface AnalysisSummary {
  totalTests: number;
  parseSuccessRate: number;
  executeSuccessRate: number;
  intentMatchRate: number;
  sourceMatchRate: number;
  averageParseTime: number;
  averageExecuteTime: number;
  edgeCasesFound: number;
  errorPatterns: Array<{
    pattern: string;
    count: number;
    examples: string[];
  }>;
  categoryBreakdown: Record<PromptCategory, {
    total: number;
    success: number;
    failed: number;
  }>;
}

// ============ Collector Stats Types ============

export interface CollectorStats {
  /** Total prompts generated */
  promptsGenerated: number;

  /** Total tests executed */
  testsExecuted: number;

  /** Successful parses */
  parseSuccess: number;

  /** Failed parses */
  parseFailed: number;

  /** Successful executions */
  executeSuccess: number;

  /** Failed executions */
  executeFailed: number;

  /** Edge cases identified */
  edgeCasesFound: number;

  /** Start time */
  startTime: string;

  /** Current runtime in seconds */
  runtimeSeconds: number;

  /** Is currently running */
  isRunning: boolean;
}

// ============ Rate Limiter Types ============

export interface RateLimiterConfig {
  /** Maximum calls per minute */
  maxCallsPerMinute: number;

  /** Window size in milliseconds (default: 60000) */
  windowMs?: number;
}

// ============ Gemini Model Types ============

export type GeminiModelId = 'gemini-2.0-flash' | 'gemini-2.5-flash-preview-05-20';

export interface GeminiModelConfig {
  /** Primary model to use (default: gemini-2.0-flash for lower token usage) */
  primaryModel: GeminiModelId;

  /** Fallback model when primary hits rate limit */
  fallbackModel: GeminiModelId;

  /** Enable automatic fallback on quota exceeded (default: true) */
  enableFallback: boolean;

  /** Cooldown time in ms before retrying primary model (default: 60000) */
  primaryCooldownMs: number;
}

export const GEMINI_MODELS: Record<GeminiModelId, { name: string; tokenEfficiency: string }> = {
  'gemini-2.0-flash': {
    name: 'Gemini 2.0 Flash',
    tokenEfficiency: 'high', // Lower token usage
  },
  'gemini-2.5-flash-preview-05-20': {
    name: 'Gemini 2.5 Flash Preview',
    tokenEfficiency: 'medium', // Higher capability but more tokens
  },
};

// ============ Logger Types ============

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  data?: any;
}
