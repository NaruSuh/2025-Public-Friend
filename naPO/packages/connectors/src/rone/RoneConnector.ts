/**
 * R-ONE Connector
 * 한국부동산원 부동산통계정보 API 커넥터
 *
 * API 정보:
 * - Base URL: https://www.reb.or.kr/r-one/openapi
 * - 인증: API Key (KEY 쿼리 파라미터)
 *
 * Endpoints:
 * - SttsApiTbl.do: 통계목록 조회
 * - SttsApiTblItm.do: 통계 세부항목 조회
 * - SttsApiTblData.do: 통계 데이터 조회
 */

import type { ConnectorConfig, ConnectorStatus, NormalizedResponse, QueryFilters } from '@labgod/core-types';
import { BaseConnector, type ConnectorOptions } from '../base';
import {
  RoneAdapter,
  type RoneTableListItem,
  type RoneTableItemsItem,
  type RoneTableDataItem,
} from './RoneAdapter';

/**
 * R-ONE API 설정
 */
export const RONE_CONFIG: ConnectorConfig = {
  id: 'rone',
  name: 'R-ONE 부동산통계',
  baseUrl: 'https://www.reb.or.kr/r-one/openApi',
  timeout: 30000,
};

/**
 * R-ONE 커넥터 옵션
 */
export interface RoneConnectorOptions extends ConnectorOptions {
  /** API 키 (한국부동산원 발급) */
  apiKey: string;
}

/**
 * R-ONE 커넥터
 */
export class RoneConnector extends BaseConnector {
  private readonly roneApiKey: string;

  constructor(options: RoneConnectorOptions) {
    super(RONE_CONFIG, options);
    this.roneApiKey = options.apiKey;
  }

  /**
   * 커넥터 상태 확인
   */
  async checkStatus(): Promise<ConnectorStatus> {
    try {
      // 간단한 통계목록 조회로 상태 확인
      const response = await this.getTableList({ pSize: 1 });
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

  /**
   * 필터 기반 데이터 조회
   *
   * 3단계 자동 라우팅:
   * - TBL_ID, ITM_ID 없음 → 통계목록 조회
   * - TBL_ID만 있음 → 세부항목 조회
   * - TBL_ID, ITM_ID 있음 → 데이터 조회
   */
  async fetchByFilters<T>(filters: QueryFilters): Promise<NormalizedResponse<T>> {
    const adaptedParams = RoneAdapter.adaptFilters(filters);
    const params = RoneAdapter.inferMissingParams(adaptedParams, {
      keywords: filters.keywords,
    });

    let result;

    // 3단계 자동 라우팅
    if (params.TBL_ID && params.ITM_ID) {
      // Step 3: 데이터 조회
      result = await this.getTableData({
        TBL_ID: params.TBL_ID as string,
        ITM_ID: params.ITM_ID as string,
        startDt: params.startDt as string | undefined,
        endDt: params.endDt as string | undefined,
        pIndex: params.pIndex as number | undefined,
        pSize: params.pSize as number | undefined,
      });
    } else if (params.TBL_ID) {
      // Step 2: 세부항목 조회
      result = await this.getTableItems({
        TBL_ID: params.TBL_ID as string,
        pIndex: params.pIndex as number | undefined,
        pSize: params.pSize as number | undefined,
      });
    } else {
      // Step 1: 통계목록 조회
      result = await this.getTableList({
        pIndex: params.pIndex as number | undefined,
        pSize: params.pSize as number | undefined,
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
   * 통계목록 조회 (SttsApiTbl.do)
   */
  async getTableList(params?: {
    pIndex?: number;
    pSize?: number;
  }): Promise<{
    success: boolean;
    totalCount: number;
    page: number;
    pageSize: number;
    data: RoneTableListItem[];
    error?: { code: string; message: string };
  }> {
    const validation = RoneAdapter.validateTableListParams(params || {});
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

    const queryParams = {
      KEY: this.roneApiKey,
      Type: 'json',
      pIndex: params?.pIndex || 1,
      pSize: params?.pSize || 100,
    };

    const data = await this.get<unknown>('/SttsApiTbl.do', queryParams);
    return RoneAdapter.normalizeTableListResponse(data);
  }

  /**
   * 통계 세부항목 조회 (SttsApiTblItm.do)
   */
  async getTableItems(params: {
    TBL_ID: string;
    pIndex?: number;
    pSize?: number;
  }): Promise<{
    success: boolean;
    totalCount: number;
    page: number;
    pageSize: number;
    data: RoneTableItemsItem[];
    error?: { code: string; message: string };
  }> {
    const validation = RoneAdapter.validateTableItemsParams(params);
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

    const queryParams = {
      KEY: this.roneApiKey,
      Type: 'json',
      TBL_ID: params.TBL_ID,
      pIndex: params.pIndex || 1,
      pSize: params.pSize || 100,
    };

    const data = await this.get<unknown>('/SttsApiTblItm.do', queryParams);
    return RoneAdapter.normalizeTableItemsResponse(data);
  }

  /**
   * 통계 데이터 조회 (SttsApiTblData.do)
   */
  async getTableData(params: {
    TBL_ID: string;
    ITM_ID: string;
    startDt?: string;
    endDt?: string;
    pIndex?: number;
    pSize?: number;
  }): Promise<{
    success: boolean;
    totalCount: number;
    page: number;
    pageSize: number;
    data: RoneTableDataItem[];
    error?: { code: string; message: string };
  }> {
    const validation = RoneAdapter.validateTableDataParams(params);
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
      KEY: this.roneApiKey,
      Type: 'json',
      TBL_ID: params.TBL_ID,
      ITM_ID: params.ITM_ID,
      pIndex: params.pIndex || 1,
      pSize: params.pSize || 100,
    };

    if (params.startDt) queryParams.startDt = params.startDt;
    if (params.endDt) queryParams.endDt = params.endDt;

    const data = await this.get<unknown>('/SttsApiTblData.do', queryParams);
    return RoneAdapter.normalizeTableDataResponse(data);
  }

  /**
   * 주요 통계만 조회
   */
  async getKeyStatistics(params?: {
    pIndex?: number;
    pSize?: number;
  }): Promise<{
    success: boolean;
    totalCount: number;
    data: RoneTableListItem[];
  }> {
    const result = await this.getTableList(params);
    if (!result.success) {
      return { success: false, totalCount: 0, data: [] };
    }

    const filtered = RoneAdapter.filterKeyStatistics(result.data);
    return {
      success: true,
      totalCount: filtered.length,
      data: filtered,
    };
  }

  /**
   * 통계표명으로 검색
   */
  async searchTables(keyword: string, params?: {
    pIndex?: number;
    pSize?: number;
  }): Promise<{
    success: boolean;
    totalCount: number;
    data: RoneTableListItem[];
  }> {
    const result = await this.getTableList(params);
    if (!result.success) {
      return { success: false, totalCount: 0, data: [] };
    }

    const filtered = RoneAdapter.searchByTableName(result.data, keyword);
    return {
      success: true,
      totalCount: filtered.length,
      data: filtered,
    };
  }

  /**
   * 주기별 통계 조회
   */
  async getStatisticsByCycle(
    cycle: 'YY' | 'HY' | 'QY' | 'MM' | 'WK',
    params?: { pIndex?: number; pSize?: number }
  ): Promise<{
    success: boolean;
    totalCount: number;
    data: RoneTableListItem[];
  }> {
    const result = await this.getTableList(params);
    if (!result.success) {
      return { success: false, totalCount: 0, data: [] };
    }

    const filtered = RoneAdapter.filterByCycle(result.data, cycle);
    return {
      success: true,
      totalCount: filtered.length,
      data: filtered,
    };
  }

  /**
   * 통계 요약 정보 생성
   */
  async getStatisticsSummary(): Promise<{
    success: boolean;
    summary?: {
      totalCount: number;
      byCycle: Record<string, number>;
      byOrganization: Record<string, number>;
      byClass: Record<string, number>;
      keyStatisticsCount: number;
      areaStatisticsCount: number;
    };
  }> {
    // 전체 통계목록 조회 (최대 1000건)
    const result = await this.getTableList({ pSize: 1000 });
    if (!result.success) {
      return { success: false };
    }

    const summary = RoneAdapter.generateStatisticsSummary(result.data);
    return { success: true, summary };
  }
}
