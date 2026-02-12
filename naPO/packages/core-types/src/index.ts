/**
 * @labgod/core-types
 *
 * Shared TypeScript types for Labgod platform
 * Used by: naPO, naON, and other Labgod apps
 *
 * @packageDocumentation
 */

// ==========================================
// API 응답 타입
// ==========================================

/**
 * 표준화된 API 응답 구조
 */
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: ApiError;
  metadata?: ResponseMetadata;
}

/**
 * 정규화된 API 응답 (커넥터용)
 * 모든 어댑터의 normalizeResponse() 반환 타입
 */
export interface NormalizedResponse<T = unknown> {
  success: boolean;
  totalCount: number;
  data: T[];
  error?: ApiError;
  pagination?: PaginationInfo;
  /** 현재 페이지 번호 (1-based) */
  page?: number;
  /** 페이지 크기 */
  pageSize?: number;
  _raw?: unknown;
}

/**
 * 응답 메타데이터
 */
export interface ResponseMetadata {
  source: string;
  timestamp: string;
  requestId?: string;
  apiVersion?: string;
  [key: string]: unknown;
}

/**
 * API 에러 정보
 */
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  hint?: string;
}

// ==========================================
// 페이지네이션 타입
// ==========================================

/**
 * 페이지네이션 파라미터 (요청용)
 * 각 API 스타일에 맞는 필드 지원
 */
export interface PaginationParams {
  /** 표준 페이지 번호 (1-based) */
  page?: number;
  /** 표준 페이지 크기 */
  pageSize?: number;
  /** 공공데이터포털 스타일 */
  pageNo?: number;
  numOfRows?: number;
  /** ECOS 스타일 */
  startCount?: number;
  endCount?: number;
  /** R-ONE 스타일 */
  pIndex?: number;
  pSize?: number;
}

/**
 * 페이지네이션 정보 (응답용)
 */
export interface PaginationInfo {
  totalCount: number;
  page: number;
  pageSize: number;
  totalPages?: number;
  hasMore?: boolean;
}

/**
 * 페이지네이션 응답
 */
export interface PaginatedResponse<T = unknown> {
  items: T[];
  pagination: PaginationInfo;
}

// ==========================================
// 검증 타입
// ==========================================

/**
 * 검증 오류 항목
 */
export interface ValidationError {
  field: string;
  message: string;
  value?: unknown;
}

/**
 * 검증 결과
 */
export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
}

// ==========================================
// 날짜 관련 타입
// ==========================================

/**
 * 날짜 범위
 */
export interface DateRange {
  /** ISO 형식: YYYY-MM-DD */
  start?: string;
  /** ISO 형식: YYYY-MM-DD */
  end?: string;
}

/**
 * 날짜 형식 타입
 * - compact: YYYYMMDD (공공데이터포털)
 * - month: YYYYMM (KOSIS, ECOS)
 * - year: YYYY (연간 통계)
 * - quarter: YYYYQ1 (분기 통계)
 * - dot: YYYY.MM (일부 API)
 */
export type DateFormatType = 'compact' | 'month' | 'year' | 'quarter' | 'dot';

// ==========================================
// 지역 관련 타입
// ==========================================

/**
 * 지역 정보
 */
export interface RegionInfo {
  /** 시도명 */
  sido?: string;
  /** 시군구명 */
  sigungu?: string;
  /** 지역코드 */
  code?: string;
}

// ==========================================
// 커넥터 관련 타입
// ==========================================

/**
 * API 커넥터 설정
 */
export interface ConnectorConfig {
  id: string;
  name: string;
  baseUrl: string;
  apiKey?: string;
  timeout?: number;
  rateLimit?: RateLimitConfig;
  enabled?: boolean;
}

/**
 * 레이트 리밋 설정
 */
export interface RateLimitConfig {
  /** 초당 요청 수 */
  requestsPerSecond?: number;
  /** 분당 요청 수 */
  requestsPerMinute?: number;
  /** 일일 요청 수 */
  requestsPerDay?: number;
}

/**
 * 커넥터 상태
 */
export interface ConnectorStatus {
  /** 연결 상태 */
  isConnected: boolean;
  /** 마지막 상태 확인 시간 */
  lastCheck: string;
  /** 상태 메시지 */
  message?: string;
  /** 에러 메시지 */
  error?: string;
  /** 커넥터 ID (선택) */
  id?: string;
  /** 커넥터 이름 (선택) */
  name?: string;
  /** 활성화 여부 (선택) */
  enabled?: boolean;
  /** 정상 여부 (선택) */
  healthy?: boolean;
  /** 남은 할당량 (선택) */
  quotaRemaining?: number;
  /** 할당량 리셋 시간 (선택) */
  quotaResetAt?: string;
}

// ==========================================
// 쿼리 필터 타입 (NLP용)
// ==========================================

/**
 * 쿼리 필터 (자연어 파싱 결과)
 */
export interface QueryFilters {
  /** 날짜 범위 */
  dateRange?: DateRange;
  /** 지역 정보 */
  region?: RegionInfo | string;
  /** 키워드 목록 */
  keywords?: string[];
  /** 카테고리 */
  category?: string;
  /** 정렬 기준 */
  orderBy?: string;
  /** 정렬 방향 */
  orderDirection?: 'asc' | 'desc';
  /** 결과 제한 */
  limit?: number;
  /** API별 추가 파라미터 */
  custom?: Record<string, unknown>;
}

// ==========================================
// 작업 관련 타입
// ==========================================

/**
 * 작업 상태
 */
export type JobStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

/**
 * 작업 유형
 */
export type JobType = 'API_FETCH' | 'CRAWL' | 'PDF_PARSE' | 'ANALYSIS' | 'EXPORT';

/**
 * 작업 정보
 */
export interface Job {
  id: string;
  jobType: JobType;
  status: JobStatus;
  progress?: number;
  resultCount?: number;
  errorMessage?: string;
  createdAt: Date;
  startedAt?: Date;
  completedAt?: Date;
  metadata?: Record<string, unknown>;
}

// ==========================================
// 감사 로그 타입 (정보기관용)
// ==========================================

/**
 * 감사 로그 항목
 */
export interface AuditLogEntry {
  id: string;
  timestamp: string;
  userId: string;
  action: AuditAction;
  resource: string;
  resourceId?: string;
  details?: Record<string, unknown>;
  ipAddress?: string;
  userAgent?: string;
  success: boolean;
  errorMessage?: string;
}

/**
 * 감사 대상 액션
 */
export type AuditAction =
  | 'LOGIN'
  | 'LOGOUT'
  | 'QUERY'
  | 'EXPORT'
  | 'CREATE'
  | 'UPDATE'
  | 'DELETE'
  | 'ACCESS'
  | 'SHARE';

// ==========================================
// 유틸리티 타입
// ==========================================

/**
 * 키-값 레코드
 */
export type KeyValue<T = unknown> = Record<string, T>;

/**
 * Nullable 타입 헬퍼
 */
export type Nullable<T> = T | null;

/**
 * Optional 타입 헬퍼
 */
export type Optional<T> = T | undefined;

/**
 * 선택적 필드를 가진 타입 생성
 */
export type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

/**
 * 필수 필드를 가진 타입 생성
 */
export type RequiredBy<T, K extends keyof T> = Omit<T, K> & Required<Pick<T, K>>;

/**
 * 읽기 전용 레코드 타입
 */
export type ReadonlyRecord<K extends string | number | symbol, V> = Readonly<Record<K, V>>;

// ==========================================
// 에러 코드 타입
// ==========================================

/**
 * 에러 코드 형식 (API별로 다름)
 */
export type ErrorCodeFormat = 'resultCode' | 'error_code' | 'errCd' | 'CODE';

// ==========================================
// 원시 응답 타입 (API별)
// ==========================================

/**
 * 공공데이터포털 API 원시 응답 구조
 */
export interface PublicDataRawResponse {
  response?: {
    header?: {
      resultCode: string;
      resultMsg: string;
    };
    body?: {
      items?: {
        item?: unknown | unknown[];
      };
      totalCount?: number | string;
      pageNo?: number | string;
      numOfRows?: number | string;
    };
  };
}

/**
 * R-ONE/NABO/KOSIS API 원시 응답 구조
 */
export interface StatApiRawResponse {
  RESULT?: {
    CODE: string;
    MESSAGE?: string;
  };
  error_code?: string;
  error_msg?: string;
  err?: string;
  errMsg?: string;
  list_total_count?: number;
  row?: unknown[];
  [key: string]: unknown;
}

/**
 * ECOS API 원시 응답 구조
 */
export interface EcosRawResponse {
  StatisticSearch?: {
    list_total_count?: number;
    row?: unknown[];
  };
  RESULT?: {
    CODE: string;
    MESSAGE?: string;
  };
}

/**
 * HUG API 원시 응답 구조
 */
export interface HugRawResponse {
  response?: {
    header?: {
      resultCode: string;
      resultMsg: string;
    };
    body?: {
      items?: unknown[];
      totalCount?: number;
    };
  };
}
