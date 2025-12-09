#!/usr/bin/env ts-node
/**
 * 대규모 크롤링 실행 스크립트
 *
 * 사용법:
 *   npx ts-node src/scripts/runCrawler.ts [options]
 *
 * 옵션:
 *   --crawler=<type>   특정 크롤러만 실행 (nec_policy, party_minjoo, party_ppp)
 *   --download         PDF 다운로드 활성화
 *   --pages=<n>        크롤링할 페이지 수 (기본: 3)
 *   --dry-run          실제 저장 없이 테스트
 */

import { CrawlerFactory } from '../services/crawler/crawlerFactory';
import { CrawlOptions, CrawlResult, CrawlerType } from '../types/crawler.types';
import fs from 'fs/promises';
import path from 'path';

// 설정
const BASE_OUTPUT_DIR = path.resolve(__dirname, '../../../data/crawled');
const LOG_DIR = path.resolve(__dirname, '../../../data/crawled/logs');

// 크롤링 대상 목록
const CRAWL_TARGETS: CrawlerType[] = [
  'nec_policy',
  'party_minjoo',
  'party_ppp',
];

interface CrawlStats {
  crawler: string;
  status: 'success' | 'partial' | 'failed';
  itemCount: number;
  downloadedFiles: number;
  errors: number;
  durationMs: number;
}

async function ensureDirectories(): Promise<void> {
  await fs.mkdir(LOG_DIR, { recursive: true });
  for (const target of CRAWL_TARGETS) {
    await fs.mkdir(path.join(BASE_OUTPUT_DIR, target, 'pdf'), { recursive: true });
    await fs.mkdir(path.join(BASE_OUTPUT_DIR, target, 'json'), { recursive: true });
  }
}

async function saveResults(
  crawlerType: string,
  result: CrawlResult
): Promise<void> {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const jsonPath = path.join(
    BASE_OUTPUT_DIR,
    crawlerType,
    'json',
    `crawl_${timestamp}.json`
  );

  await fs.writeFile(jsonPath, JSON.stringify(result, null, 2), 'utf-8');
  console.log(`  📁 결과 저장: ${jsonPath}`);
}

async function runCrawler(
  crawlerType: CrawlerType,
  options: CrawlOptions
): Promise<CrawlStats> {
  console.log(`\n🚀 [${crawlerType}] 크롤링 시작...`);
  const startTime = Date.now();

  try {
    const crawler = CrawlerFactory.create(crawlerType);
    const result = await crawler.crawl(options);

    // 결과 저장
    await saveResults(crawlerType, result);

    const stats: CrawlStats = {
      crawler: crawlerType,
      status: result.success ? 'success' : 'partial',
      itemCount: result.itemCount,
      downloadedFiles: result.downloadedFiles?.length || 0,
      errors: result.errors?.length || 0,
      durationMs: Date.now() - startTime,
    };

    console.log(`  ✅ 완료: ${stats.itemCount}개 항목, ${stats.downloadedFiles}개 파일`);
    if (stats.errors > 0) {
      console.log(`  ⚠️  에러: ${stats.errors}개`);
    }

    return stats;
  } catch (error: any) {
    console.error(`  ❌ 실패: ${error.message}`);
    return {
      crawler: crawlerType,
      status: 'failed',
      itemCount: 0,
      downloadedFiles: 0,
      errors: 1,
      durationMs: Date.now() - startTime,
    };
  }
}

async function main(): Promise<void> {
  console.log('═══════════════════════════════════════════════════════════');
  console.log('   naPO 대규모 크롤링 시작');
  console.log('   시작 시간:', new Date().toLocaleString('ko-KR'));
  console.log('═══════════════════════════════════════════════════════════');

  // 인자 파싱
  const args = process.argv.slice(2);
  const targetCrawler = args.find(a => a.startsWith('--crawler='))?.split('=')[1];
  const downloadFiles = args.includes('--download');
  const pagesArg = args.find(a => a.startsWith('--pages='))?.split('=')[1];
  const endPage = pagesArg ? parseInt(pagesArg, 10) : 3;
  const dryRun = args.includes('--dry-run');

  if (dryRun) {
    console.log('\n⚠️  DRY RUN 모드 - 실제 저장 없음\n');
  }

  // 디렉토리 생성
  await ensureDirectories();

  // 크롤링 옵션
  const crawlOptions: CrawlOptions = {
    startPage: 1,
    endPage,
    downloadFiles,
    outputDir: BASE_OUTPUT_DIR,
    filters: {
      includePolicy: true,
      includeCandidates: false, // 선거 기간 아니면 false
    },
  };

  console.log('\n📋 크롤링 설정:');
  console.log(`   - 페이지 범위: 1~${endPage}`);
  console.log(`   - PDF 다운로드: ${downloadFiles ? '활성화' : '비활성화'}`);
  console.log(`   - 대상: ${targetCrawler || '모든 크롤러'}`);

  // 크롤링 실행
  const targets = targetCrawler
    ? [targetCrawler as CrawlerType]
    : CRAWL_TARGETS;

  const allStats: CrawlStats[] = [];

  for (const target of targets) {
    const outputDir = path.join(BASE_OUTPUT_DIR, target, 'pdf');
    const stats = await runCrawler(target, {
      ...crawlOptions,
      outputDir,
    });
    allStats.push(stats);

    // 크롤러 간 딜레이 (서버 부하 방지)
    if (targets.indexOf(target) < targets.length - 1) {
      console.log('\n⏳ 다음 크롤러 대기 (5초)...');
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
  }

  // 최종 보고서
  console.log('\n═══════════════════════════════════════════════════════════');
  console.log('   크롤링 완료 보고서');
  console.log('═══════════════════════════════════════════════════════════');

  let totalItems = 0;
  let totalFiles = 0;
  let totalErrors = 0;
  let totalDuration = 0;

  for (const stats of allStats) {
    const statusIcon =
      stats.status === 'success' ? '✅' :
      stats.status === 'partial' ? '⚠️' : '❌';

    console.log(`\n${statusIcon} ${stats.crawler}:`);
    console.log(`   - 항목: ${stats.itemCount}개`);
    console.log(`   - 파일: ${stats.downloadedFiles}개`);
    console.log(`   - 에러: ${stats.errors}개`);
    console.log(`   - 소요: ${(stats.durationMs / 1000).toFixed(1)}초`);

    totalItems += stats.itemCount;
    totalFiles += stats.downloadedFiles;
    totalErrors += stats.errors;
    totalDuration += stats.durationMs;
  }

  console.log('\n───────────────────────────────────────────────────────────');
  console.log(`📊 총계:`);
  console.log(`   - 총 항목: ${totalItems}개`);
  console.log(`   - 총 파일: ${totalFiles}개`);
  console.log(`   - 총 에러: ${totalErrors}개`);
  console.log(`   - 총 소요: ${(totalDuration / 1000 / 60).toFixed(1)}분`);
  console.log(`   - 종료 시간: ${new Date().toLocaleString('ko-KR')}`);
  console.log('═══════════════════════════════════════════════════════════\n');

  // 로그 저장
  const logPath = path.join(
    LOG_DIR,
    `crawl_${new Date().toISOString().split('T')[0]}.log`
  );
  const logContent = {
    startTime: new Date(Date.now() - totalDuration).toISOString(),
    endTime: new Date().toISOString(),
    stats: allStats,
    totals: { totalItems, totalFiles, totalErrors, totalDuration },
  };
  await fs.writeFile(logPath, JSON.stringify(logContent, null, 2), 'utf-8');
  console.log(`📝 로그 저장: ${logPath}`);
}

main().catch(console.error);
