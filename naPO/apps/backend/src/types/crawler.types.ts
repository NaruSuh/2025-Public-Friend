export type CrawlerType =
  | 'nec_library' // 선거정보도서관
  | 'nec_policy' // 정책·공약마당
  | 'nec_data' // 국가선거정보 개방포털
  | 'party_minjoo' // 더불어민주당
  | 'party_ppp' // 국민의힘
  | 'nanet' // 국회도서관
  | 'law' // 국가법령정보센터
  | 'custom'; // 커스텀

export interface CrawlOptions {
  url?: string;
  startPage?: number;
  endPage?: number;
  dateRange?: {
    start: string;
    end: string;
  };
  filters?: Record<string, any>;
  downloadFiles?: boolean;
  outputDir?: string;
}

export interface CrawlResult {
  success: boolean;
  crawlerId: string;
  itemCount: number;
  items: CrawledItem[];
  downloadedFiles?: string[];
  errors?: CrawlError[];
  metadata: {
    startTime: string;
    endTime: string;
    durationMs: number;
    pagesProcessed: number;
  };
}

export interface CrawledItem {
  id: string;
  title?: string;
  content?: string;
  url?: string;
  fileUrl?: string;
  category?: string;
  date?: string;
  metadata?: Record<string, any>;
}

export interface CrawlError {
  url: string;
  message: string;
  timestamp: string;
}

export interface CrawlerSiteConfig {
  id: CrawlerType;
  name: string;
  baseUrl: string;
  selectors: {
    listContainer?: string;
    listItem?: string;
    title?: string;
    content?: string;
    link?: string;
    pagination?: string;
    nextPage?: string;
    pdfLink?: string;
  };
  authentication?: {
    type: 'cookie' | 'login' | 'none';
    credentials?: Record<string, string>;
  };
}

// 공약/정책 데이터 타입
export interface PledgeData {
  id: string;
  sourceUrl: string;
  sourceSite: CrawlerType;

  // 선거 정보
  electionType: 'presidential' | 'legislative' | 'local' | 'by_election';
  electionDate?: string;
  electionName: string;

  // 정당/후보 정보
  partyName: string;
  candidateName?: string;
  constituency?: string;

  // 공약 내용
  title: string;
  summary?: string;
  fullContent: string;
  category: PledgeCategory;

  // 첨부 파일
  pdfUrl?: string;
  pdfLocalPath?: string;

  // 메타데이터
  crawledAt: string;
  publishedAt?: string;
}

export type PledgeCategory =
  | 'economy'
  | 'welfare'
  | 'education'
  | 'security'
  | 'environment'
  | 'culture'
  | 'governance'
  | 'other';

// 정당 정보 타입
export interface PartyInfo {
  id: string;
  name: string;
  officialName: string;
  website: string;
  color?: string;
  logoUrl?: string;
}
