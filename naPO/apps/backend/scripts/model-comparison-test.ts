#!/usr/bin/env npx tsx
/**
 * Gemini Model Comparison Test
 *
 * Compares parsing performance between:
 * - gemini-2.0-flash (lower token usage)
 * - gemini-2.5-flash-preview-05-20 (higher capability)
 *
 * Runs 25 iterations each and generates a comparison report
 */

import * as fs from 'fs';
import * as path from 'path';
import * as dotenv from 'dotenv';

// Load environment variables from .env file
dotenv.config({ path: path.resolve(__dirname, '../.env') });

// Dynamic import for the auto-debug-collector package
async function main() {
  const { AutoDebugCollector, PromptGenerator, RateLimiter, DEFAULT_CONFIG } =
    await import('../../../packages/auto-debug-collector/src');

  const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
  const NAPO_BASE_URL = process.env.NAPO_BASE_URL || 'http://localhost:3001/api/v1';
  const ITERATIONS_PER_MODEL = 25;
  const TEST_OUTPUT_DIR = './test_temp/model_comparison';

  if (!GEMINI_API_KEY) {
    console.error('❌ GEMINI_API_KEY environment variable is required');
    process.exit(1);
  }

  // Ensure output directory exists
  if (!fs.existsSync(TEST_OUTPUT_DIR)) {
    fs.mkdirSync(TEST_OUTPUT_DIR, { recursive: true });
  }

  console.log('═══════════════════════════════════════════════════════════════');
  console.log('🔬 Gemini Model Comparison Test');
  console.log('═══════════════════════════════════════════════════════════════');
  console.log(`📊 Iterations per model: ${ITERATIONS_PER_MODEL}`);
  console.log(`📁 Output directory: ${TEST_OUTPUT_DIR}`);
  console.log('');

  interface ModelResult {
    model: string;
    iterations: number;
    promptsGenerated: number;
    testsExecuted: number;
    parseSuccess: number;
    parseFailed: number;
    executeSuccess: number;
    executeFailed: number;
    intentMatchRate: number;
    sourceMatchRate: number;
    avgParseTime: number;
    avgExecuteTime: number;
    errors: string[];
    startTime: string;
    endTime: string;
    durationMs: number;
  }

  const results: ModelResult[] = [];

  // Test each model
  const models = [
    { id: 'gemini-2.0-flash', name: 'Gemini 2.0 Flash' },
    { id: 'gemini-2.5-flash-preview-05-20', name: 'Gemini 2.5 Flash Preview' },
  ] as const;

  for (const modelInfo of models) {
    console.log('───────────────────────────────────────────────────────────────');
    console.log(`🧪 Testing: ${modelInfo.name}`);
    console.log('───────────────────────────────────────────────────────────────');

    const modelOutputDir = path.join(TEST_OUTPUT_DIR, modelInfo.id.replace(/[^a-z0-9]/g, '_'));

    // Clean previous results
    if (fs.existsSync(modelOutputDir)) {
      fs.rmSync(modelOutputDir, { recursive: true, force: true });
    }
    fs.mkdirSync(modelOutputDir, { recursive: true });

    const startTime = new Date();
    const errors: string[] = [];

    try {
      // Create collector with specific model configuration
      const collector = new AutoDebugCollector({
        geminiApiKey: GEMINI_API_KEY,
        napoBaseUrl: NAPO_BASE_URL,
        promptsPerMinute: 3, // Conservative rate limit
        testTempDir: modelOutputDir,
        maxIterations: ITERATIONS_PER_MODEL,
        domains: ['election', 'policy', 'candidate', 'party'],
        verbose: true,
        // Force specific model (disable fallback for fair comparison)
        modelConfig: {
          primaryModel: modelInfo.id,
          fallbackModel: modelInfo.id, // Same model to prevent fallback
          enableFallback: false,
          primaryCooldownMs: 60000,
        },
      } as any);

      // Run the test
      await collector.start();

      const stats = collector.getStats();
      const endTime = new Date();

      // Read the CSV to calculate intent/source match rates
      const csvPath = path.join(modelOutputDir, 'test_document_1st.csv');
      let intentMatchRate = 0;
      let sourceMatchRate = 0;
      let avgParseTime = 0;
      let avgExecuteTime = 0;

      if (fs.existsSync(csvPath)) {
        const csvContent = fs.readFileSync(csvPath, 'utf-8');
        const lines = csvContent.split('\n').filter(l => l.trim());
        const dataLines = lines.slice(1); // Skip header

        let intentMatches = 0;
        let sourceMatches = 0;
        let totalParseTime = 0;
        let totalExecuteTime = 0;
        let validRows = 0;

        for (const line of dataLines) {
          const cols = line.split(',');
          if (cols.length >= 20) {
            validRows++;
            if (cols[16] === 'true') intentMatches++;
            if (cols[17] === 'true') sourceMatches++;
            totalParseTime += parseFloat(cols[9]) || 0;
            totalExecuteTime += parseFloat(cols[13]) || 0;
          }
        }

        if (validRows > 0) {
          intentMatchRate = (intentMatches / validRows) * 100;
          sourceMatchRate = (sourceMatches / validRows) * 100;
          avgParseTime = totalParseTime / validRows;
          avgExecuteTime = totalExecuteTime / validRows;
        }
      }

      results.push({
        model: modelInfo.id,
        iterations: ITERATIONS_PER_MODEL,
        promptsGenerated: stats.promptsGenerated,
        testsExecuted: stats.testsExecuted,
        parseSuccess: stats.parseSuccess,
        parseFailed: stats.parseFailed,
        executeSuccess: stats.executeSuccess,
        executeFailed: stats.executeFailed,
        intentMatchRate,
        sourceMatchRate,
        avgParseTime,
        avgExecuteTime,
        errors,
        startTime: startTime.toISOString(),
        endTime: endTime.toISOString(),
        durationMs: endTime.getTime() - startTime.getTime(),
      });

      console.log(`✅ ${modelInfo.name} test completed`);
      console.log(`   - Tests: ${stats.testsExecuted}, Parse Success: ${stats.parseSuccess}`);

    } catch (error: any) {
      console.error(`❌ ${modelInfo.name} test failed:`, error.message);
      errors.push(error.message);

      results.push({
        model: modelInfo.id,
        iterations: ITERATIONS_PER_MODEL,
        promptsGenerated: 0,
        testsExecuted: 0,
        parseSuccess: 0,
        parseFailed: 0,
        executeSuccess: 0,
        executeFailed: 0,
        intentMatchRate: 0,
        sourceMatchRate: 0,
        avgParseTime: 0,
        avgExecuteTime: 0,
        errors,
        startTime: startTime.toISOString(),
        endTime: new Date().toISOString(),
        durationMs: Date.now() - startTime.getTime(),
      });
    }

    // Wait between models to avoid rate limiting
    if (models.indexOf(modelInfo) < models.length - 1) {
      console.log('\n⏳ Waiting 60s before next model test...\n');
      await new Promise(resolve => setTimeout(resolve, 60000));
    }
  }

  // Generate comparison report
  console.log('\n');
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('📊 COMPARISON REPORT');
  console.log('═══════════════════════════════════════════════════════════════');

  const report = generateComparisonReport(results);
  console.log(report);

  // Save report
  const reportPath = path.join(TEST_OUTPUT_DIR, 'comparison_report.md');
  fs.writeFileSync(reportPath, report);
  console.log(`\n📄 Report saved to: ${reportPath}`);

  // Save raw results as JSON
  const jsonPath = path.join(TEST_OUTPUT_DIR, 'comparison_results.json');
  fs.writeFileSync(jsonPath, JSON.stringify(results, null, 2));
  console.log(`📄 Raw results saved to: ${jsonPath}`);
}

function generateComparisonReport(results: any[]): string {
  const timestamp = new Date().toISOString();

  let report = `# Gemini Model Comparison Report

**Generated:** ${timestamp}
**Test Type:** naPO Query Parsing Performance

---

## Executive Summary

`;

  // Find winner for each metric
  const model1 = results[0];
  const model2 = results[1];

  if (model1 && model2) {
    const parseRate1 = model1.testsExecuted > 0 ? (model1.parseSuccess / model1.testsExecuted * 100) : 0;
    const parseRate2 = model2.testsExecuted > 0 ? (model2.parseSuccess / model2.testsExecuted * 100) : 0;
    const execRate1 = model1.testsExecuted > 0 ? (model1.executeSuccess / model1.testsExecuted * 100) : 0;
    const execRate2 = model2.testsExecuted > 0 ? (model2.executeSuccess / model2.testsExecuted * 100) : 0;

    report += `| Metric | ${model1.model} | ${model2.model} | Winner |
|--------|----------------|----------------|--------|
| Parse Success Rate | ${parseRate1.toFixed(1)}% | ${parseRate2.toFixed(1)}% | ${parseRate1 > parseRate2 ? '🏆 2.0' : parseRate2 > parseRate1 ? '🏆 2.5' : 'Tie'} |
| Execute Success Rate | ${execRate1.toFixed(1)}% | ${execRate2.toFixed(1)}% | ${execRate1 > execRate2 ? '🏆 2.0' : execRate2 > execRate1 ? '🏆 2.5' : 'Tie'} |
| Intent Match Rate | ${model1.intentMatchRate.toFixed(1)}% | ${model2.intentMatchRate.toFixed(1)}% | ${model1.intentMatchRate > model2.intentMatchRate ? '🏆 2.0' : model2.intentMatchRate > model1.intentMatchRate ? '🏆 2.5' : 'Tie'} |
| Source Match Rate | ${model1.sourceMatchRate.toFixed(1)}% | ${model2.sourceMatchRate.toFixed(1)}% | ${model1.sourceMatchRate > model2.sourceMatchRate ? '🏆 2.0' : model2.sourceMatchRate > model1.sourceMatchRate ? '🏆 2.5' : 'Tie'} |
| Avg Parse Time | ${model1.avgParseTime.toFixed(0)}ms | ${model2.avgParseTime.toFixed(0)}ms | ${model1.avgParseTime < model2.avgParseTime ? '🏆 2.0' : model2.avgParseTime < model1.avgParseTime ? '🏆 2.5' : 'Tie'} |
| Avg Execute Time | ${model1.avgExecuteTime.toFixed(0)}ms | ${model2.avgExecuteTime.toFixed(0)}ms | ${model1.avgExecuteTime < model2.avgExecuteTime ? '🏆 2.0' : model2.avgExecuteTime < model1.avgExecuteTime ? '🏆 2.5' : 'Tie'} |

`;
  }

  report += `---

## Detailed Results

`;

  for (const result of results) {
    const parseRate = result.testsExecuted > 0 ? (result.parseSuccess / result.testsExecuted * 100) : 0;
    const execRate = result.testsExecuted > 0 ? (result.executeSuccess / result.testsExecuted * 100) : 0;

    report += `### ${result.model}

| Metric | Value |
|--------|-------|
| Iterations | ${result.iterations} |
| Prompts Generated | ${result.promptsGenerated} |
| Tests Executed | ${result.testsExecuted} |
| Parse Success | ${result.parseSuccess} (${parseRate.toFixed(1)}%) |
| Parse Failed | ${result.parseFailed} |
| Execute Success | ${result.executeSuccess} (${execRate.toFixed(1)}%) |
| Execute Failed | ${result.executeFailed} |
| Intent Match Rate | ${result.intentMatchRate.toFixed(1)}% |
| Source Match Rate | ${result.sourceMatchRate.toFixed(1)}% |
| Avg Parse Time | ${result.avgParseTime.toFixed(0)}ms |
| Avg Execute Time | ${result.avgExecuteTime.toFixed(0)}ms |
| Duration | ${(result.durationMs / 1000 / 60).toFixed(1)} min |

`;

    if (result.errors.length > 0) {
      report += `**Errors:**
${result.errors.map((e: string) => `- ${e}`).join('\n')}

`;
    }
  }

  report += `---

## Recommendations

`;

  if (model1 && model2) {
    const parseRate1 = model1.testsExecuted > 0 ? (model1.parseSuccess / model1.testsExecuted * 100) : 0;
    const parseRate2 = model2.testsExecuted > 0 ? (model2.parseSuccess / model2.testsExecuted * 100) : 0;

    const diff = Math.abs(parseRate1 - parseRate2);

    if (diff < 5) {
      report += `**결론:** 두 모델의 성능 차이가 미미합니다 (${diff.toFixed(1)}% 차이).
토큰 효율성이 높은 **gemini-2.0-flash**를 기본으로 사용하는 것을 권장합니다.

`;
    } else if (parseRate1 > parseRate2) {
      report += `**결론:** gemini-2.0-flash가 ${diff.toFixed(1)}% 더 높은 파싱 성공률을 보입니다.
토큰 효율성도 높으므로 **gemini-2.0-flash**를 기본으로 사용하는 것을 권장합니다.

`;
    } else {
      report += `**결론:** gemini-2.5-flash-preview가 ${diff.toFixed(1)}% 더 높은 파싱 성공률을 보입니다.
성능이 중요한 경우 **gemini-2.5-flash-preview-05-20**를 고려하세요.
그러나 토큰 사용량이 증가할 수 있습니다.

`;
    }
  }

  report += `---

*Generated by naPO Auto Debug Collector Model Comparison Test*
`;

  return report;
}

main().catch(console.error);
