export type AuthType = 'api_key' | 'oauth' | 'bearer' | 'none';
export type ResponseFormat = 'json' | 'xml';
export type KeyLocation = 'query' | 'header';

export interface AuthConfig {
  keyParamName?: string;
  keyLocation?: KeyLocation;
  headerName?: string;
  tokenUrl?: string;
  clientId?: string;
  clientSecret?: string;
}

export interface RateLimitConfig {
  requestsPerMinute?: number;
  requestsPerDay?: number;
}

export interface ApiEndpointConfig {
  id: string;
  name: string;
  displayName: string;
  baseUrl: string;
  authType: AuthType;
  authConfig: AuthConfig;
  responseFormat: ResponseFormat;
  rateLimit?: RateLimitConfig;
  endpoints?: Record<string, string>;
  defaultParams?: Record<string, string>;
}

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
    pageNo?: number;
    numOfRows?: number;
  };
}

export interface ApiRequestParams {
  endpoint?: string;
  params?: Record<string, string | number | boolean>;
  headers?: Record<string, string>;
}

// ==========================================
// Common Code API Types (선거관리위원회 코드)
// ==========================================

export interface ElectionCode {
  sgId: string;
  sgName: string;
  sgTypecode: string;
  sgVotedate: string;
}

export interface DistrictCode {
  sdCode: string;
  sdName: string;
  wiwCode?: string;
  wiwName?: string;
}

export interface PartyCode {
  jdCode: string;
  jdName: string;
}

export interface JobCode {
  jobId: string;
  jobName: string;
}

export interface EducationCode {
  eduId: string;
  eduName: string;
}

// Generic normalized response for common code API
export interface NormalizedCodeResponse<T> {
  success: boolean;
  totalCount: number;
  pageNo: number;
  numOfRows: number;
  data: T[];
  error?: {
    code: string;
    message: string;
  };
}

// ==========================================
// Party Policy API Types (정당정책 API)
// ==========================================

export interface PolicyItem {
  order: number;
  realm: string | null;
  title: string | null;
  content: string | null;
}

export interface PartyPolicyData {
  electionId: string;
  partyName: string;
  policyCount: number;
  policies: PolicyItem[];
}

export interface PartyPolicyResponse extends NormalizedCodeResponse<PartyPolicyData> {}

// ==========================================
// Inferred Params Type
// ==========================================

export interface InferredParams {
  [key: string]: string | number | boolean | undefined | InferredMeta;
  _inferred?: InferredMeta;
  _needsTableLookup?: boolean;
  _needsItemLookup?: boolean;
  _needsCandidateLookup?: boolean;
  _queryAllMajorParties?: boolean;
}

export interface InferredMeta {
  [key: string]: string;
}
