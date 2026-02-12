/**
 * Base Connector Class
 *
 * 모든 API 커넥터의 기반 클래스
 * 공통 기능: HTTP 요청, 에러 처리, 레이트 리밋, 로깅
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios';
import type {
  ConnectorConfig,
  ConnectorStatus,
  NormalizedResponse,
  ApiError,
  QueryFilters,
} from '@labgod/core-types';

/**
 * 커넥터 옵션
 */
export interface ConnectorOptions {
  /** API 키 */
  apiKey?: string;
  /** 기본 URL */
  baseUrl?: string;
  /** 타임아웃 (ms) */
  timeout?: number;
  /** 디버그 모드 */
  debug?: boolean;
}

/**
 * 기본 커넥터 추상 클래스
 */
export abstract class BaseConnector {
  protected readonly id: string;
  protected readonly name: string;
  protected readonly baseUrl: string;
  protected readonly apiKey?: string;
  protected readonly timeout: number;
  protected readonly debug: boolean;
  protected readonly client: AxiosInstance;

  constructor(config: ConnectorConfig, options: ConnectorOptions = {}) {
    this.id = config.id;
    this.name = config.name;
    this.baseUrl = options.baseUrl || config.baseUrl;
    this.apiKey = options.apiKey || config.apiKey;
    this.timeout = options.timeout || config.timeout || 30000;
    this.debug = options.debug || false;

    this.client = axios.create({
      baseURL: this.baseUrl,
      timeout: this.timeout,
      headers: this.getDefaultHeaders(),
    });

    this.setupInterceptors();
  }

  /**
   * 기본 헤더 반환 (하위 클래스에서 오버라이드 가능)
   */
  protected getDefaultHeaders(): Record<string, string> {
    return {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
  }

  /**
   * 인터셉터 설정
   */
  private setupInterceptors(): void {
    // 요청 인터셉터
    this.client.interceptors.request.use(
      (config) => {
        if (this.debug) {
          console.log(`[${this.id}] Request:`, config.method?.toUpperCase(), config.url);
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // 응답 인터셉터
    this.client.interceptors.response.use(
      (response) => {
        if (this.debug) {
          console.log(`[${this.id}] Response:`, response.status);
        }
        return response;
      },
      (error: AxiosError) => {
        if (this.debug) {
          console.error(`[${this.id}] Error:`, error.message);
        }
        return Promise.reject(this.normalizeError(error));
      }
    );
  }

  /**
   * 에러 정규화
   */
  protected normalizeError(error: AxiosError): ApiError {
    if (error.response) {
      return {
        code: `HTTP_${error.response.status}`,
        message: error.message,
        details: {
          status: error.response.status,
          data: error.response.data,
        },
      };
    }

    if (error.request) {
      return {
        code: 'NETWORK_ERROR',
        message: 'Network request failed',
        details: {
          message: error.message,
        },
      };
    }

    return {
      code: 'UNKNOWN_ERROR',
      message: error.message,
    };
  }

  /**
   * GET 요청
   */
  protected async get<T>(
    url: string,
    params?: Record<string, unknown>,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.get<T>(url, { ...config, params });
    return response.data;
  }

  /**
   * POST 요청
   */
  protected async post<T>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  /**
   * 커넥터 상태 확인
   */
  abstract checkStatus(): Promise<ConnectorStatus>;

  /**
   * 필터 기반 데이터 조회
   */
  abstract fetchByFilters<T>(filters: QueryFilters): Promise<NormalizedResponse<T>>;

  /**
   * 커넥터 ID 반환
   */
  getId(): string {
    return this.id;
  }

  /**
   * 커넥터 이름 반환
   */
  getName(): string {
    return this.name;
  }
}
