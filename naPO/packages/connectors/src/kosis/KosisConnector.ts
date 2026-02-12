/**
 * KOSIS (통계청) API Connector
 *
 * 통계청 국가통계포털 KOSIS Open API 커넥터
 */

import { BaseConnector, type ConnectorOptions } from '../base';
import { KosisAdapter, type KosisStatDataItem, type KosisStatListItem } from './KosisAdapter';
import type { ConnectorConfig, ConnectorStatus, NormalizedResponse, QueryFilters } from '@labgod/core-types';

/**
 * KOSIS API 설정
 */
export const KOSIS_CONFIG: ConnectorConfig = {
  id: 'kosis',
  name: 'KOSIS (국가통계포털)',
  baseUrl: 'https://kosis.kr/openapi',
  timeout: 30000,
  rateLimit: {
    requestsPerSecond: 5,
    requestsPerDay: 10000,
  },
};

/**
 * KOSIS 커넥터 옵션
 */
export interface KosisConnectorOptions extends ConnectorOptions {
  /** KOSIS API 키 */
  apiKey: string;
}

/**
 * KOSIS API 커넥터
 */
export class KosisConnector extends BaseConnector {
  private readonly kosisApiKey: string;

  constructor(options: KosisConnectorOptions) {
    super(KOSIS_CONFIG, options);
    this.kosisApiKey = options.apiKey;

    if (!this.kosisApiKey) {
      throw new Error('KOSIS API key is required');
    }
  }

  /**
   * 인증 파라미터 생성
   */
  private getAuthParams(): Record<string, string> {
    return { apiKey: this.kosisApiKey };
  }

  /**
   * 커넥터 상태 확인
   */
  async checkStatus(): Promise<ConnectorStatus> {
    try {
      // 간단한 목록 조회로 상태 확인
      const response = await this.get('/Param/statisticsParameterData.do', {
        ...this.getAuthParams(),
        method: 'getList',
        format: 'json',
        orgId: '101',
      });

      const isHealthy = Boolean(response && !this.isErrorResponse(response));

      return {
        isConnected: isHealthy,
        id: this.getId(),
        name: this.getName(),
        enabled: true,
        healthy: isHealthy,
        lastCheck: new Date().toISOString(),
      };
    } catch (error) {
      return {
        isConnected: false,
        id: this.getId(),
        name: this.getName(),
        enabled: true,
        healthy: false,
        lastCheck: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * NLP 필터 기반 데이터 조회
   */
  async fetchByFilters<T = KosisStatDataItem>(filters: QueryFilters): Promise<NormalizedResponse<T>> {
    const params = KosisAdapter.adaptFilters(filters);

    const response = await this.get('/Param/statisticsParameterData.do', {
      ...this.getAuthParams(),
      ...params,
      type: 'json',
    });

    const normalized = KosisAdapter.normalizeDataResponse(response);
    return normalized as unknown as NormalizedResponse<T>;
  }

  /**
   * 통계 목록 조회
   */
  async getStatList(params: {
    orgId?: string;
    tblId?: string;
    parentListId?: string;
  }): Promise<NormalizedResponse<KosisStatListItem>> {
    const adapted = KosisAdapter.adaptFilters({
      custom: { orgId: params.orgId, tblId: params.tblId },
    });

    const response = await this.get('/Param/statisticsParameterData.do', {
      ...this.getAuthParams(),
      method: 'getList',
      ...adapted,
      ...params,
      type: 'json',
    });

    return KosisAdapter.normalizeListResponse(response);
  }

  /**
   * 통계 데이터 조회
   */
  async getStatData(params: {
    orgId: string;
    tblId: string;
    objL1?: string;
    objL2?: string;
    itmId?: string;
    prdSe?: string;
    startPrdDe?: string;
    endPrdDe?: string;
  }): Promise<NormalizedResponse<KosisStatDataItem>> {
    const response = await this.get('/Param/statisticsParameterData.do', {
      ...this.getAuthParams(),
      method: 'getList',
      ...params,
      type: 'json',
    });

    return KosisAdapter.normalizeDataResponse(response);
  }

  /**
   * 인구 통계 조회 (편의 메서드)
   */
  async getPopulationData(params?: {
    region?: string;
    year?: string;
  }): Promise<NormalizedResponse<KosisStatDataItem>> {
    const apiParams = KosisAdapter.buildPopulationParams(params?.region, params?.year);

    const response = await this.get('/Param/statisticsParameterData.do', {
      ...this.getAuthParams(),
      ...apiParams,
      type: 'json',
    });

    return KosisAdapter.normalizeDataResponse(response);
  }

  /**
   * 에러 응답 확인
   */
  private isErrorResponse(data: unknown): boolean {
    if (typeof data !== 'object' || data === null) return false;
    const obj = data as Record<string, unknown>;
    return obj.err !== undefined && String(obj.err).startsWith('ERROR');
  }
}
