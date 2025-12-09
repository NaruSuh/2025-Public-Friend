// API Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
  };
  metadata?: {
    requestId: string;
    timestamp: string;
    source: string;
    totalCount?: number;
  };
}

// Query Types
export type QueryIntent = 'fetch_api' | 'crawl_site' | 'parse_pdf' | 'analyze_data' | 'export_data';

export interface ParsedQuery {
  intent: QueryIntent;
  confidence: number;
  source: {
    type: 'api' | 'crawler' | 'local' | 'unknown';
    id?: string;
    url?: string;
  };
  filters: Record<string, any>;
  output: {
    format: 'csv' | 'json' | 'table' | 'chart' | 'excel';
    columns?: string[];
  };
  rawQuery: string;
}

export interface NLQueryResponse {
  parsedQuery: ParsedQuery;
  explanation: string;
  suggestedActions: string[];
}

// Data Source Types
export interface ApiSource {
  id: string;
  name: string;
  displayName: string;
  baseUrl: string;
  isActive: boolean;
}

export interface CrawlerSite {
  id: string;
  name: string;
  displayName: string;
  baseUrl: string;
  crawlerType: string;
}

// Job Types
export type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface DataJob {
  id: string;
  jobType: string;
  status: JobStatus;
  resultCount?: number;
  errorMessage?: string;
  createdAt: string;
  completedAt?: string;
}

// Parser Types
export type ParserType = 'clova_ocr' | 'google_vision' | 'pymupdf' | 'dolphin';

export interface ParserInfo {
  id: ParserType;
  name: string;
  available: boolean;
  bestFor: string;
}

// Export Types
export type ExportFormat = 'csv' | 'json' | 'xlsx' | 'pdf';

// Debug / Observability Types
export interface ApiCallInfo {
  endpoint: string;
  params: Record<string, any>;
  status: 'pending' | 'success' | 'error';
  duration?: number;
  error?: string;
}

export interface DebugInfo {
  // Timing
  parseStartTime?: number;
  parseEndTime?: number;
  executeStartTime?: number;
  executeEndTime?: number;

  // Parse Result
  parsedQuery?: ParsedQuery;
  parseSource?: 'gemini' | 'pattern' | 'unknown';

  // Execution Details
  apiCalls?: ApiCallInfo[];
  queriedParties?: string[];
  failedParties?: string[];

  // Result Summary
  totalRows?: number;
  source?: string;

  // Metadata from backend
  backendDebug?: {
    apiChainUsed?: boolean;
    stages?: string[];
    originalFilters?: Record<string, any>;
    adaptedParams?: Record<string, any>;
    successCount?: number;
    failedCount?: number;
    successParties?: string[];
    failedParties?: string[];
    candidateName?: string;
  };
}

// UI Types
export interface NavItem {
  id: string;
  label: string;
  icon?: string;
  path?: string;
  children?: NavItem[];
}
