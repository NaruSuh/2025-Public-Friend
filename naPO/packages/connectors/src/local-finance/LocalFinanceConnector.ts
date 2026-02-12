/**
 * Local Finance Connector
 * 행정안전부 지방재정365 Open API 커넥터
 *
 * API 정보:
 * - Base URL: https://www.lofin365.go.kr/lf/hub
 * - 인증: API Key (Key 쿼리 파라미터)
 */

import type { ConnectorConfig, ConnectorStatus, NormalizedResponse, QueryFilters } from '@labgod/core-types';
import { BaseConnector, type ConnectorOptions } from '../base';
import {
  LocalFinanceAdapter,
  type LocalFinanceEndpointType,
  type LocalFinanceExpItem,
  type LocalFinanceRatioItem,
  type LocalFinanceDebtItem,
  type LocalFinanceNormalizedResponse,
} from './LocalFinanceAdapter';

export const LOCAL_FINANCE_CONFIG: ConnectorConfig = {
  id: 'local_finance',
  name: '지방재정365',
  baseUrl: 'https://www.lofin365.go.kr/lf/hub',
  timeout: 30000,
};

export interface LocalFinanceConnectorOptions extends ConnectorOptions {
  apiKey: string;
}

export class LocalFinanceConnector extends BaseConnector {
  private readonly lfApiKey: string;

  constructor(options: LocalFinanceConnectorOptions) {
    super(LOCAL_FINANCE_CONFIG, options);
    this.lfApiKey = options.apiKey;
  }

  async checkStatus(): Promise<ConnectorStatus> {
    try {
      const response = await this.getFinanceIndependence({ fyr: String(new Date().getFullYear() - 1) });
      return {
        isConnected: response.success,
        lastCheck: new Date().toISOString(),
        message: response.success ? 'Connected' : 'Failed to connect',
      };
    } catch (error) {
      return {
        isConnected: false,
        lastCheck: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  async fetchByFilters<T>(filters: QueryFilters): Promise<NormalizedResponse<T>> {
    const adaptedParams = LocalFinanceAdapter.adaptFilters(filters);
    const endpoint = (filters.custom?.endpoint as LocalFinanceEndpointType) || 'expByProject';

    let result: LocalFinanceNormalizedResponse<unknown>;

    switch (endpoint) {
      case 'financeIndependence':
        result = await this.getFinanceIndependence({
          fyr: adaptedParams.fyr as string,
          wa_laf_cd: adaptedParams.wa_laf_cd as string | undefined,
        });
        break;
      case 'localDebt':
        result = await this.getLocalDebt({
          fyr: adaptedParams.fyr as string,
          wa_laf_cd: adaptedParams.wa_laf_cd as string | undefined,
        });
        break;
      default:
        result = await this.getExpByProject({
          fyr: adaptedParams.fyr as string,
          wa_laf_cd: adaptedParams.wa_laf_cd as string | undefined,
          pIndex: adaptedParams.pIndex as number | undefined,
          pSize: adaptedParams.pSize as number | undefined,
        });
    }

    return {
      success: result.success,
      totalCount: result.totalCount,
      data: result.data as T[],
      pagination: {
        page: result.page,
        pageSize: result.pageSize,
        totalCount: result.totalCount,
        hasMore: result.totalCount > result.page * result.pageSize,
      },
    };
  }

  /**
   * 세부사업별 세출현황 조회 (QWGJK)
   */
  async getExpByProject(params: {
    fyr: string;
    wa_laf_cd?: string;
    laf_cd?: string;
    dbiz_nm?: string;
    pIndex?: number;
    pSize?: number;
  }): Promise<LocalFinanceNormalizedResponse<LocalFinanceExpItem>> {
    const validation = LocalFinanceAdapter.validateParams(params);
    if (!validation.valid) {
      return {
        success: false,
        totalCount: 0,
        page: 1,
        pageSize: 0,
        data: [],
        error: {
          code: 'VALIDATION_ERROR',
          message: validation.errors?.join(', ') || 'Validation failed',
        },
      };
    }

    const queryParams: Record<string, unknown> = {
      Key: this.lfApiKey,
      Type: 'json',
      fyr: params.fyr,
      pIndex: params.pIndex || 1,
      pSize: params.pSize || 100,
    };

    if (params.wa_laf_cd) queryParams.wa_laf_cd = params.wa_laf_cd;
    if (params.laf_cd) queryParams.laf_cd = params.laf_cd;
    if (params.dbiz_nm) queryParams.dbiz_nm = params.dbiz_nm;

    const data = await this.get<unknown>(
      LocalFinanceAdapter.ENDPOINTS.expByProject,
      queryParams
    );
    return LocalFinanceAdapter.normalizeExpResponse(data);
  }

  /**
   * 재정자립도 조회 (FNNCI)
   */
  async getFinanceIndependence(params: {
    fyr: string;
    wa_laf_cd?: string;
    pIndex?: number;
    pSize?: number;
  }): Promise<LocalFinanceNormalizedResponse<LocalFinanceRatioItem>> {
    const validation = LocalFinanceAdapter.validateParams(params);
    if (!validation.valid) {
      return {
        success: false,
        totalCount: 0,
        page: 1,
        pageSize: 0,
        data: [],
        error: {
          code: 'VALIDATION_ERROR',
          message: validation.errors?.join(', ') || 'Validation failed',
        },
      };
    }

    const queryParams: Record<string, unknown> = {
      Key: this.lfApiKey,
      Type: 'json',
      fyr: params.fyr,
      pIndex: params.pIndex || 1,
      pSize: params.pSize || 100,
    };

    if (params.wa_laf_cd) queryParams.wa_laf_cd = params.wa_laf_cd;

    const data = await this.get<unknown>(
      LocalFinanceAdapter.ENDPOINTS.financeIndependence,
      queryParams
    );
    return LocalFinanceAdapter.normalizeRatioResponse(data);
  }

  /**
   * 지방채 현황 조회 (LDEBT)
   */
  async getLocalDebt(params: {
    fyr: string;
    wa_laf_cd?: string;
    pIndex?: number;
    pSize?: number;
  }): Promise<LocalFinanceNormalizedResponse<LocalFinanceDebtItem>> {
    const validation = LocalFinanceAdapter.validateParams(params);
    if (!validation.valid) {
      return {
        success: false,
        totalCount: 0,
        page: 1,
        pageSize: 0,
        data: [],
        error: {
          code: 'VALIDATION_ERROR',
          message: validation.errors?.join(', ') || 'Validation failed',
        },
      };
    }

    const queryParams: Record<string, unknown> = {
      Key: this.lfApiKey,
      Type: 'json',
      fyr: params.fyr,
      pIndex: params.pIndex || 1,
      pSize: params.pSize || 100,
    };

    if (params.wa_laf_cd) queryParams.wa_laf_cd = params.wa_laf_cd;

    const data = await this.get<unknown>(
      LocalFinanceAdapter.ENDPOINTS.localDebt,
      queryParams
    );
    return LocalFinanceAdapter.normalizeDebtResponse(data);
  }

  getAvailableEndpoints(): Array<{
    endpoint: LocalFinanceEndpointType;
    name: string;
    path: string;
  }> {
    return (Object.keys(LocalFinanceAdapter.ENDPOINTS) as LocalFinanceEndpointType[]).map(endpoint => ({
      endpoint,
      name: LocalFinanceAdapter.ENDPOINT_NAMES[endpoint],
      path: LocalFinanceAdapter.ENDPOINTS[endpoint],
    }));
  }
}
