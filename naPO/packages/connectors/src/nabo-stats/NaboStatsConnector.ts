/**
 * NABOSTATS Connector
 * 국회예산정책처 재정경제통계시스템 Open API 커넥터
 *
 * API 정보:
 * - Base URL: https://www.nabostats.go.kr/openapi
 * - 인증: API Key (Key 쿼리 파라미터)
 */

import type { ConnectorConfig, ConnectorStatus, NormalizedResponse, QueryFilters } from '@labgod/core-types';
import { BaseConnector, type ConnectorOptions } from '../base';
import {
  NaboStatsAdapter,
  type NaboEndpointType,
  type NaboTableItem,
  type NaboTableItemDetail,
  type NaboDataItem,
  type NaboDictionaryItem,
  type NaboNormalizedResponse,
} from './NaboStatsAdapter';

export const NABOSTATS_CONFIG: ConnectorConfig = {
  id: 'nabostats',
  name: 'NABOSTATS 재정경제통계시스템',
  baseUrl: 'https://www.nabostats.go.kr/openapi',
  timeout: 30000,
};

export interface NaboStatsConnectorOptions extends ConnectorOptions {
  apiKey: string;
}

export class NaboStatsConnector extends BaseConnector {
  private readonly naboApiKey: string;

  constructor(options: NaboStatsConnectorOptions) {
    super(NABOSTATS_CONFIG, options);
    this.naboApiKey = options.apiKey;
  }

  async checkStatus(): Promise<ConnectorStatus> {
    try {
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

  async fetchByFilters<T>(filters: QueryFilters): Promise<NormalizedResponse<T>> {
    const adaptedParams = NaboStatsAdapter.adaptFilters(filters);

    // 엔드포인트 결정
    let result: NaboNormalizedResponse<unknown>;

    if (adaptedParams.STATBL_ID && adaptedParams.DTACYCLE_CD) {
      result = await this.getTableData({
        tableId: adaptedParams.STATBL_ID as string,
        dataCycle: adaptedParams.DTACYCLE_CD as string,
        timeId: adaptedParams.WRTTIME_IDTFR_ID as string | undefined,
        pIndex: adaptedParams.pIndex as number | undefined,
        pSize: adaptedParams.pSize as number | undefined,
      });
    } else if (adaptedParams.STATBL_ID) {
      result = await this.getTableItems({
        tableId: adaptedParams.STATBL_ID as string,
        pIndex: adaptedParams.pIndex as number | undefined,
        pSize: adaptedParams.pSize as number | undefined,
      });
    } else {
      result = await this.getTableList({
        tableId: adaptedParams.STATBL_ID as string | undefined,
        tableName: adaptedParams.STATBL_NM as string | undefined,
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
   * 통계표 목록 조회
   */
  async getTableList(params?: {
    tableId?: string;
    tableName?: string;
    pIndex?: number;
    pSize?: number;
  }): Promise<NaboNormalizedResponse<NaboTableItem>> {
    const validation = NaboStatsAdapter.validateParams('tableList', params || {});
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
      Key: this.naboApiKey,
      Type: 'json',
      pIndex: params?.pIndex || 1,
      pSize: params?.pSize || 100,
    };

    if (params?.tableId) queryParams.STATBL_ID = params.tableId;
    if (params?.tableName) queryParams.STATBL_NM = params.tableName;

    const data = await this.get<unknown>(
      NaboStatsAdapter.ENDPOINTS.tableList,
      queryParams
    );
    return NaboStatsAdapter.normalizeTableListResponse(data);
  }

  /**
   * 통계 세부항목 조회
   */
  async getTableItems(params: {
    tableId: string;
    pIndex?: number;
    pSize?: number;
  }): Promise<NaboNormalizedResponse<NaboTableItemDetail>> {
    const validation = NaboStatsAdapter.validateParams('tableItems', { STATBL_ID: params.tableId });
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
      Key: this.naboApiKey,
      Type: 'json',
      STATBL_ID: params.tableId,
      pIndex: params.pIndex || 1,
      pSize: params.pSize || 100,
    };

    const data = await this.get<unknown>(
      NaboStatsAdapter.ENDPOINTS.tableItems,
      queryParams
    );
    return NaboStatsAdapter.normalizeTableItemsResponse(data);
  }

  /**
   * 통계 데이터 조회
   */
  async getTableData(params: {
    tableId: string;
    dataCycle: string;
    timeId?: string;
    pIndex?: number;
    pSize?: number;
  }): Promise<NaboNormalizedResponse<NaboDataItem>> {
    const validation = NaboStatsAdapter.validateParams('tableData', {
      STATBL_ID: params.tableId,
      DTACYCLE_CD: params.dataCycle,
    });
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
      Key: this.naboApiKey,
      Type: 'json',
      STATBL_ID: params.tableId,
      DTACYCLE_CD: params.dataCycle,
      pIndex: params.pIndex || 1,
      pSize: params.pSize || 100,
    };

    if (params.timeId) queryParams.WRTTIME_IDTFR_ID = params.timeId;

    const data = await this.get<unknown>(
      NaboStatsAdapter.ENDPOINTS.tableData,
      queryParams
    );
    return NaboStatsAdapter.normalizeTableDataResponse(data);
  }

  /**
   * 용어사전 조회
   */
  async getDictionary(params?: {
    title?: string;
    pIndex?: number;
    pSize?: number;
  }): Promise<NaboNormalizedResponse<NaboDictionaryItem>> {
    const queryParams: Record<string, unknown> = {
      Key: this.naboApiKey,
      Type: 'json',
      pIndex: params?.pIndex || 1,
      pSize: params?.pSize || 100,
    };

    if (params?.title) queryParams.DIC_TITLE = params.title;

    const data = await this.get<unknown>(
      NaboStatsAdapter.ENDPOINTS.dictionary,
      queryParams
    );
    return NaboStatsAdapter.normalizeDictionaryResponse(data);
  }

  /**
   * 통계표 검색
   */
  async searchTables(keyword: string, params?: {
    pIndex?: number;
    pSize?: number;
  }): Promise<NaboNormalizedResponse<NaboTableItem>> {
    return this.getTableList({
      tableName: keyword,
      ...params,
    });
  }

  getAvailableEndpoints(): Array<{
    endpoint: NaboEndpointType;
    name: string;
    path: string;
  }> {
    return (Object.keys(NaboStatsAdapter.ENDPOINTS) as NaboEndpointType[]).map(endpoint => ({
      endpoint,
      name: NaboStatsAdapter.ENDPOINT_NAMES[endpoint],
      path: NaboStatsAdapter.ENDPOINTS[endpoint],
    }));
  }
}
