#!/usr/bin/env npx tsx
/**
 * Quick Improvement Test
 * Tests the improved QueryEngine with various query types
 */

import * as dotenv from 'dotenv';
import * as path from 'path';

dotenv.config({ path: path.resolve(__dirname, '../.env') });

interface TestCase {
  query: string;
  expectedSource: string;
  expectedIntent: string;
  category: string;
}

const TEST_CASES: TestCase[] = [
  // 당선인 조회
  { query: "2022년 지방선거 서울시장 당선자", expectedSource: "public_data_winner", expectedIntent: "fetch_api", category: "winner" },
  { query: "2024년 총선 투표율", expectedSource: "public_data_winner", expectedIntent: "fetch_api", category: "winner" },
  { query: "최근 대선 당선인", expectedSource: "public_data_winner", expectedIntent: "fetch_api", category: "winner" },

  // 정당 정책
  { query: "국민의힘 경제 공약", expectedSource: "public_data_party_policy", expectedIntent: "fetch_api", category: "party_policy" },
  { query: "더불어민주당 복지 정책", expectedSource: "public_data_party_policy", expectedIntent: "fetch_api", category: "party_policy" },
  { query: "주요정당 2022 지방선거 공약", expectedSource: "public_data_party_policy", expectedIntent: "fetch_api", category: "party_policy" },

  // 후보자 공약
  { query: "윤석열 대선 공약", expectedSource: "public_data_election", expectedIntent: "fetch_api", category: "candidate" },
  { query: "이재명 정책", expectedSource: "public_data_election", expectedIntent: "fetch_api", category: "candidate" },

  // 모호한 쿼리
  { query: "공약 알려줘", expectedSource: "public_data_party_policy", expectedIntent: "fetch_api", category: "ambiguous" },
  { query: "선거 결과", expectedSource: "public_data_winner", expectedIntent: "fetch_api", category: "ambiguous" },

  // 엣지 케이스
  { query: "2022년 지방선거 민주당 공약", expectedSource: "public_data_party_policy", expectedIntent: "fetch_api", category: "edge" },
  { query: "서울시장 후보 목록", expectedSource: "public_data_candidate", expectedIntent: "fetch_api", category: "edge" },

  // Phase 2: 득표율 쿼리 (신규)
  { query: "윤석열 득표율", expectedSource: "public_data_winner", expectedIntent: "fetch_api", category: "vote_rate" },
  { query: "2022년 대선 득표율", expectedSource: "public_data_winner", expectedIntent: "fetch_api", category: "vote_rate" },
  { query: "민주당 득표율", expectedSource: "public_data_winner", expectedIntent: "fetch_api", category: "vote_rate" },

  // Phase 2: 최근 선거 쿼리 (신규)
  { query: "최근 선거 결과", expectedSource: "public_data_winner", expectedIntent: "fetch_api", category: "recent_election" },
  { query: "최근 지방선거 결과", expectedSource: "public_data_winner", expectedIntent: "fetch_api", category: "recent_election" },
  { query: "최근 총선 당선자", expectedSource: "public_data_winner", expectedIntent: "fetch_api", category: "recent_election" },
];

async function runTest() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('🧪 Quick Improvement Test - QueryEngine Performance');
  console.log('═══════════════════════════════════════════════════════════════\n');
  
  const results = {
    total: TEST_CASES.length,
    parseSuccess: 0,
    parseFailed: 0,
    sourceMatch: 0,
    intentMatch: 0,
    avgParseTime: 0,
    byCategory: {} as Record<string, { total: number; success: number; sourceMatch: number }>,
    failures: [] as { query: string; expected: string; actual: string; error?: string }[],
  };
  
  let totalParseTime = 0;
  
  for (const testCase of TEST_CASES) {
    // Initialize category stats
    if (!results.byCategory[testCase.category]) {
      results.byCategory[testCase.category] = { total: 0, success: 0, sourceMatch: 0 };
    }
    results.byCategory[testCase.category].total++;
    
    const startTime = Date.now();
    
    try {
      const response = await fetch('http://localhost:3001/api/v1/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: testCase.query }),
      });
      
      const parseTime = Date.now() - startTime;
      totalParseTime += parseTime;
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success && data.data?.parsedQuery) {
        results.parseSuccess++;
        results.byCategory[testCase.category].success++;
        
        const parsed = data.data.parsedQuery;
        const actualSource = parsed.source?.id || 'unknown';
        const actualIntent = parsed.intent || 'unknown';
        
        // Check source match
        if (actualSource === testCase.expectedSource) {
          results.sourceMatch++;
          results.byCategory[testCase.category].sourceMatch++;
          console.log(`✅ [${testCase.category}] "${testCase.query.substring(0, 25)}..." → ${actualSource} (${parseTime}ms)`);
        } else {
          console.log(`⚠️  [${testCase.category}] "${testCase.query.substring(0, 25)}..." → ${actualSource} (expected: ${testCase.expectedSource}) (${parseTime}ms)`);
          results.failures.push({
            query: testCase.query,
            expected: testCase.expectedSource,
            actual: actualSource,
          });
        }
        
        // Check intent match
        if (actualIntent === testCase.expectedIntent) {
          results.intentMatch++;
        }
      } else {
        throw new Error('Invalid response structure');
      }
    } catch (error: any) {
      results.parseFailed++;
      console.log(`❌ [${testCase.category}] "${testCase.query.substring(0, 25)}..." → ERROR: ${error.message}`);
      results.failures.push({
        query: testCase.query,
        expected: testCase.expectedSource,
        actual: 'ERROR',
        error: error.message,
      });
    }
    
    // Small delay between requests
    await new Promise(r => setTimeout(r, 500));
  }
  
  results.avgParseTime = totalParseTime / results.total;
  
  // Print summary
  console.log('\n═══════════════════════════════════════════════════════════════');
  console.log('📊 TEST RESULTS SUMMARY');
  console.log('═══════════════════════════════════════════════════════════════\n');
  
  console.log(`Total Tests:        ${results.total}`);
  console.log(`Parse Success:      ${results.parseSuccess} (${(results.parseSuccess/results.total*100).toFixed(1)}%)`);
  console.log(`Source Match:       ${results.sourceMatch} (${(results.sourceMatch/results.total*100).toFixed(1)}%)`);
  console.log(`Intent Match:       ${results.intentMatch} (${(results.intentMatch/results.total*100).toFixed(1)}%)`);
  console.log(`Avg Parse Time:     ${results.avgParseTime.toFixed(0)}ms`);
  
  console.log('\n📈 Results by Category:');
  for (const [category, stats] of Object.entries(results.byCategory)) {
    const successRate = (stats.success / stats.total * 100).toFixed(1);
    const sourceMatchRate = (stats.sourceMatch / stats.total * 100).toFixed(1);
    console.log(`  ${category}: ${stats.success}/${stats.total} parse (${successRate}%), ${stats.sourceMatch}/${stats.total} source match (${sourceMatchRate}%)`);
  }
  
  if (results.failures.length > 0) {
    console.log('\n⚠️  Failures/Mismatches:');
    for (const f of results.failures) {
      console.log(`  - "${f.query}": expected=${f.expected}, got=${f.actual}${f.error ? `, error=${f.error}` : ''}`);
    }
  }
  
  console.log('\n═══════════════════════════════════════════════════════════════');
  
  // Return results for programmatic use
  return results;
}

runTest().catch(console.error);
