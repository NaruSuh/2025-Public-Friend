/**
 * naPO Crawler Services
 *
 * 웹 크롤링 서비스 모듈
 * - 선거관리위원회 (NEC) 계열
 * - 정당 사이트
 * - 커스텀 크롤러
 */

// Base
export { BaseCrawler } from './baseCrawler';

// NEC 계열
export { NecLibraryCrawler } from './necLibraryCrawler';
export { NecPolicyCrawler } from './necPolicyCrawler';

// 정당 사이트
export { PartyMinjooCrawler, PartyPPPCrawler } from './partyCrawler';

// 커스텀
export { CustomCrawler } from './customCrawler';

// 팩토리
export { CrawlerFactory } from './crawlerFactory';

// 타입 re-export
export type {
  CrawlerType,
  CrawlOptions,
  CrawlResult,
  CrawledItem,
  CrawlError,
  CrawlerSiteConfig,
  PledgeData,
  PledgeCategory,
  PartyInfo,
} from '@/types/crawler.types';
