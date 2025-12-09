#!/usr/bin/env npx tsx
/**
 * Run Auto Debug Collector
 *
 * Usage:
 *   npx tsx scripts/run-auto-debug.ts [options]
 *
 * Options:
 *   --iterations N    Max iterations (default: 100, 0 for unlimited)
 *   --rate N          Prompts per minute (default: 4)
 *   --verbose         Enable verbose logging
 *   --cleanup         Clean up test_temp before starting
 *
 * Environment:
 *   GEMINI_API_KEY    Required - Gemini API key
 *   NAPO_API_URL      Optional - naPO API URL (default: http://localhost:3001/api/v1)
 */

import * as path from 'path';
import * as fs from 'fs';

// Parse command line arguments
const args = process.argv.slice(2);
const getArg = (name: string, defaultValue: string): string => {
  const index = args.indexOf(`--${name}`);
  if (index !== -1 && args[index + 1]) {
    return args[index + 1];
  }
  return defaultValue;
};
const hasFlag = (name: string): boolean => args.includes(`--${name}`);

// Load environment variables
import dotenv from 'dotenv';
dotenv.config();

// Configuration
const config = {
  geminiApiKey: process.env.GEMINI_API_KEY || '',
  napoBaseUrl: process.env.NAPO_API_URL || 'http://localhost:3001/api/v1',
  promptsPerMinute: parseInt(getArg('rate', '4'), 10),
  maxIterations: parseInt(getArg('iterations', '100'), 10),
  testTempDir: path.join(__dirname, '..', 'test_temp'),
  verbose: hasFlag('verbose'),
  cleanup: hasFlag('cleanup'),
};

async function main() {
  console.log('╔════════════════════════════════════════════════════╗');
  console.log('║         naPO Auto Debug Collector                  ║');
  console.log('╚════════════════════════════════════════════════════╝');
  console.log('');

  // Validate configuration
  if (!config.geminiApiKey) {
    console.error('ERROR: GEMINI_API_KEY environment variable is required');
    process.exit(1);
  }

  console.log('Configuration:');
  console.log(`  - API URL: ${config.napoBaseUrl}`);
  console.log(`  - Prompts/min: ${config.promptsPerMinute}`);
  console.log(`  - Max iterations: ${config.maxIterations || 'unlimited'}`);
  console.log(`  - Output dir: ${config.testTempDir}`);
  console.log(`  - Verbose: ${config.verbose}`);
  console.log('');

  // Cleanup if requested
  if (config.cleanup && fs.existsSync(config.testTempDir)) {
    console.log('Cleaning up previous test data...');
    fs.rmSync(config.testTempDir, { recursive: true, force: true });
  }

  // Dynamic import to handle the package
  // Path: apps/backend/scripts -> ../../../packages/auto-debug-collector/src
  const { AutoDebugCollector } = await import('../../../packages/auto-debug-collector/src');

  const collector = new AutoDebugCollector({
    geminiApiKey: config.geminiApiKey,
    napoBaseUrl: config.napoBaseUrl,
    promptsPerMinute: config.promptsPerMinute,
    testTempDir: config.testTempDir,
    maxIterations: config.maxIterations,
    domains: ['election', 'policy', 'candidate', 'party'],
    verbose: config.verbose,
  });

  // Handle graceful shutdown
  let shutdownRequested = false;
  const shutdown = () => {
    if (shutdownRequested) {
      console.log('\nForce shutdown...');
      process.exit(1);
    }
    shutdownRequested = true;
    console.log('\nGraceful shutdown requested. Finishing current iteration...');
    collector.stop();
  };

  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);

  // Print progress periodically
  const progressInterval = setInterval(() => {
    const stats = collector.getStats();
    if (stats.isRunning) {
      console.log(
        `[Progress] Tests: ${stats.testsExecuted}, ` +
        `Parse OK: ${stats.parseSuccess}, ` +
        `Execute OK: ${stats.executeSuccess}, ` +
        `Edge cases: ${stats.edgeCasesFound}, ` +
        `Runtime: ${stats.runtimeSeconds}s`
      );
    }
  }, 30000); // Every 30 seconds

  try {
    console.log('Starting collection...\n');
    await collector.start();
  } catch (error: any) {
    console.error('Collection failed:', error.message);
  } finally {
    clearInterval(progressInterval);

    // Print final stats
    const stats = collector.getStats();
    console.log('\n╔════════════════════════════════════════════════════╗');
    console.log('║                 Final Statistics                    ║');
    console.log('╚════════════════════════════════════════════════════╝');
    console.log(`  Prompts Generated: ${stats.promptsGenerated}`);
    console.log(`  Tests Executed:    ${stats.testsExecuted}`);
    console.log(`  Parse Success:     ${stats.parseSuccess} (${((stats.parseSuccess / stats.testsExecuted) * 100 || 0).toFixed(1)}%)`);
    console.log(`  Parse Failed:      ${stats.parseFailed}`);
    console.log(`  Execute Success:   ${stats.executeSuccess} (${((stats.executeSuccess / stats.testsExecuted) * 100 || 0).toFixed(1)}%)`);
    console.log(`  Execute Failed:    ${stats.executeFailed}`);
    console.log(`  Edge Cases Found:  ${stats.edgeCasesFound}`);
    console.log(`  Total Runtime:     ${stats.runtimeSeconds}s`);
    console.log('');
    console.log(`Results saved to: ${config.testTempDir}`);
    console.log(`  - test_document_1st.csv (analysis data)`);
    console.log(`  - summary.json (summary statistics)`);
    console.log(`  - prompts/ (generated prompts)`);
    console.log(`  - responses/ (API responses)`);
    console.log(`  - logs/ (execution logs)`);
  }
}

main().catch(console.error);
