/**
 * @napo/auto-debug-collector
 *
 * Automated debug data collector for naPO
 * Generates test prompts using Gemini and collects edge cases
 */

// Main orchestrator
export { AutoDebugCollector } from './AutoDebugCollector';

// Components (for customization/extension)
export { PromptGenerator } from './PromptGenerator';
export { QueryTester } from './QueryTester';
export { ResultAnalyzer } from './ResultAnalyzer';
export { RateLimiter, createGeminiRateLimiter } from './RateLimiter';

// Types
export type {
  AutoDebugConfig,
  GeneratedPrompt,
  PromptCategory,
  PromptDifficulty,
  TestResult,
  ParsedQueryResult,
  AnalysisRow,
  AnalysisSummary,
  CollectorStats,
  RateLimiterConfig,
  LogLevel,
  LogEntry,
  // Gemini model types
  GeminiModelId,
  GeminiModelConfig,
} from './types';

// Gemini model constants
export { GEMINI_MODELS } from './types';

// Config
export { DEFAULT_CONFIG, DEFAULT_GEMINI_CONFIG, PROMPT_GENERATION_SYSTEM, CSV_HEADER, DIRS, FILES } from './config';
