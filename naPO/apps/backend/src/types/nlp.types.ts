export type QueryIntent =
  | 'fetch_api' // API에서 데이터 가져오기
  | 'crawl_site' // 사이트 크롤링
  | 'parse_pdf' // PDF 파싱
  | 'analyze_data' // 데이터 분석
  | 'export_data'; // 데이터 내보내기

export interface ParsedQuery {
  intent: QueryIntent;
  confidence: number;
  source: {
    type: 'api' | 'crawler' | 'local' | 'unknown';
    id?: string;
    url?: string;
    crawlerType?: import('./crawler.types').CrawlerType;
  };
  filters: QueryFilters;
  output: OutputConfig;
  rawQuery: string;
}

export interface QueryFilters {
  dateRange?: {
    start?: string;
    end?: string;
  };
  region?: string | {
    sido?: string;
    sigungu?: string;
  };
  category?: string;
  keywords?: string[];
  election?: {
    year?: number;
    type?: string; // '대통령', '지방선거', '총선'
    position?: string; // '시장', '도지사', '구청장'
    sgTypecode?: string; // 선거종류코드
  };
  // 선거 관련 필드
  sgId?: string | string[]; // 선거ID (예: 20220601)
  partyName?: string; // 정당명
  custom?: Record<string, any>;
}

export interface OutputConfig {
  format: 'csv' | 'json' | 'table' | 'chart' | 'excel';
  columns?: string[];
  sorting?: {
    field: string;
    order: 'asc' | 'desc';
  };
  limit?: number;
}

export interface NLQueryResponse {
  parsedQuery: ParsedQuery;
  explanation: string;
  suggestedActions: string[];
}
