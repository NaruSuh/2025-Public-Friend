/**
 * Common types shared across the application
 */

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
}

export interface PaginatedResponse<T = any> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

export type JobStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

export type JobType = 'API_FETCH' | 'CRAWL' | 'PDF_PARSE' | 'ANALYSIS';

export interface Job {
  id: string;
  jobType: JobType;
  status: JobStatus;
  resultCount?: number;
  errorMessage?: string;
  createdAt: Date;
  startedAt?: Date;
  completedAt?: Date;
}
