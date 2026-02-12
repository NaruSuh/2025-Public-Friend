/**
 * HUG Connector
 * 주택도시보증공사 Open API 커넥터
 *
 * API 정보:
 * - Base URL: https://www.khug.or.kr
 * - 인증: API Key (serviceKey 쿼리 파라미터)
 * - 응답형식: XML
 *
 * 8개 엔드포인트:
 * - distributionGuarantee: 분양보증현황(지역)
 * - guaranteeAmount: 민간분양아파트 보증금액(지역별)
 * - constructionRate: 분양아파트 공정률(지역별)
 * - pfLoanAmount: PF대출금액 현황(연도별, 지역별)
 * - distributionPerformance: 분양보증 분양이행 현황(연도별, 지역별)
 * - newDistribution: 신규 분양세대수(지역별)
 * - priceIndex: 지역별 ㎡당 분양가격지수
 * - pricePerSqm: 지역별 ㎡당 분양가격
 */

import type { ConnectorConfig, ConnectorStatus, NormalizedResponse, QueryFilters } from '@labgod/core-types';
import { BaseConnector, type ConnectorOptions } from '../base';
import {
  HugAdapter,
  type HugEndpointType,
  type HugDistributionGuaranteeItem,
  type HugGuaranteeAmountItem,
  type HugConstructionRateItem,
  type HugPfLoanItem,
  type HugDistributionPerformanceItem,
  type HugNewDistributionItem,
  type HugPriceIndexItem,
  type HugPricePerSqmItem,
  type HugNormalizedResponse,
} from './HugAdapter';

/**
 * HUG API 설정
 */
export const HUG_CONFIG: ConnectorConfig = {
  id: 'hug',
  name: 'HUG 주택도시보증공사',
  baseUrl: 'https://www.khug.or.kr',
  timeout: 30000,
};

/**
 * HUG 커넥터 옵션
 */
export interface HugConnectorOptions extends ConnectorOptions {
  /** API 키 (공공데이터포털 발급) */
  apiKey: string;
}

/**
 * HUG 커넥터
 */
export class HugConnector extends BaseConnector {
  private readonly hugApiKey: string;

  constructor(options: HugConnectorOptions) {
    super(HUG_CONFIG, options);
    this.hugApiKey = options.apiKey;
  }

  /**
   * 기본 헤더 (XML 응답)
   */
  protected getDefaultHeaders(): Record<string, string> {
    return {
      'Accept': 'application/xml',
    };
  }

  /**
   * 커넥터 상태 확인
   */
  async checkStatus(): Promise<ConnectorStatus> {
    try {
      // 간단한 분양보증 조회로 상태 확인
      const response = await this.getDistributionGuarantee();
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
   */
  async fetchByFilters<T>(filters: QueryFilters): Promise<NormalizedResponse<T>> {
    const adaptedParams = HugAdapter.adaptFilters(filters);
    const endpoint = (adaptedParams._endpoint as HugEndpointType) || 'distributionGuarantee';

    let result: HugNormalizedResponse<unknown>;

    switch (endpoint) {
      case 'distributionGuarantee':
        result = await this.getDistributionGuarantee({
          regionCode: adaptedParams.regionCode as string | undefined,
          year: adaptedParams.year as string | undefined,
        });
        break;
      case 'guaranteeAmount':
        result = await this.getGuaranteeAmount({
          regionCode: adaptedParams.regionCode as string | undefined,
          year: adaptedParams.year as string | undefined,
        });
        break;
      case 'constructionRate':
        result = await this.getConstructionRate({
          regionCode: adaptedParams.regionCode as string | undefined,
          year: adaptedParams.year as string | undefined,
        });
        break;
      case 'pfLoanAmount':
        result = await this.getPfLoanAmount({
          regionCode: adaptedParams.regionCode as string | undefined,
          year: adaptedParams.year as string | undefined,
        });
        break;
      case 'distributionPerformance':
        result = await this.getDistributionPerformance({
          regionCode: adaptedParams.regionCode as string | undefined,
          year: adaptedParams.year as string | undefined,
        });
        break;
      case 'newDistribution':
        result = await this.getNewDistribution({
          regionCode: adaptedParams.regionCode as string | undefined,
          year: adaptedParams.year as string | undefined,
        });
        break;
      case 'priceIndex':
        result = await this.getPriceIndex({
          regionCode: adaptedParams.regionCode as string | undefined,
          year: adaptedParams.year as string | undefined,
        });
        break;
      case 'pricePerSqm':
        result = await this.getPricePerSqm({
          regionCode: adaptedParams.regionCode as string | undefined,
          year: adaptedParams.year as string | undefined,
        });
        break;
      default:
        result = await this.getDistributionGuarantee({
          regionCode: adaptedParams.regionCode as string | undefined,
          year: adaptedParams.year as string | undefined,
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
   * 분양보증현황(지역) 조회
   */
  async getDistributionGuarantee(params?: {
    regionCode?: string;
    year?: string;
  }): Promise<HugNormalizedResponse<HugDistributionGuaranteeItem>> {
    const validation = HugAdapter.validateParams(params || {});
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
      serviceKey: this.hugApiKey,
    };
    if (params?.regionCode) queryParams.REGION_CD = params.regionCode;
    if (params?.year) queryParams.YEAR = params.year;

    const data = await this.get<unknown>(
      HugAdapter.ENDPOINTS.distributionGuarantee,
      queryParams
    );
    return HugAdapter.normalizeDistributionGuaranteeResponse(data);
  }

  /**
   * 민간분양아파트 보증금액(지역별) 조회
   */
  async getGuaranteeAmount(params?: {
    regionCode?: string;
    year?: string;
  }): Promise<HugNormalizedResponse<HugGuaranteeAmountItem>> {
    const validation = HugAdapter.validateParams(params || {});
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
      serviceKey: this.hugApiKey,
    };
    if (params?.regionCode) queryParams.REGION_CD = params.regionCode;
    if (params?.year) queryParams.YEAR = params.year;

    const data = await this.get<unknown>(
      HugAdapter.ENDPOINTS.guaranteeAmount,
      queryParams
    );
    return HugAdapter.normalizeGuaranteeAmountResponse(data);
  }

  /**
   * 분양아파트 공정률(지역별) 조회
   */
  async getConstructionRate(params?: {
    regionCode?: string;
    year?: string;
  }): Promise<HugNormalizedResponse<HugConstructionRateItem>> {
    const validation = HugAdapter.validateParams(params || {});
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
      serviceKey: this.hugApiKey,
    };
    if (params?.regionCode) queryParams.REGION_CD = params.regionCode;
    if (params?.year) queryParams.YEAR = params.year;

    const data = await this.get<unknown>(
      HugAdapter.ENDPOINTS.constructionRate,
      queryParams
    );
    return HugAdapter.normalizeConstructionRateResponse(data);
  }

  /**
   * PF대출금액 현황(연도별, 지역별) 조회
   */
  async getPfLoanAmount(params?: {
    regionCode?: string;
    year?: string;
  }): Promise<HugNormalizedResponse<HugPfLoanItem>> {
    const validation = HugAdapter.validateParams(params || {});
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
      serviceKey: this.hugApiKey,
    };
    if (params?.regionCode) queryParams.REGION_CD = params.regionCode;
    if (params?.year) queryParams.YEAR = params.year;

    const data = await this.get<unknown>(
      HugAdapter.ENDPOINTS.pfLoanAmount,
      queryParams
    );
    return HugAdapter.normalizePfLoanResponse(data);
  }

  /**
   * 분양보증 분양이행 현황(연도별, 지역별) 조회
   */
  async getDistributionPerformance(params?: {
    regionCode?: string;
    year?: string;
  }): Promise<HugNormalizedResponse<HugDistributionPerformanceItem>> {
    const validation = HugAdapter.validateParams(params || {});
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
      serviceKey: this.hugApiKey,
    };
    if (params?.regionCode) queryParams.REGION_CD = params.regionCode;
    if (params?.year) queryParams.YEAR = params.year;

    const data = await this.get<unknown>(
      HugAdapter.ENDPOINTS.distributionPerformance,
      queryParams
    );
    return HugAdapter.normalizeDistributionPerformanceResponse(data);
  }

  /**
   * 신규 분양세대수(지역별) 조회
   */
  async getNewDistribution(params?: {
    regionCode?: string;
    year?: string;
  }): Promise<HugNormalizedResponse<HugNewDistributionItem>> {
    const validation = HugAdapter.validateParams(params || {});
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
      serviceKey: this.hugApiKey,
    };
    if (params?.regionCode) queryParams.REGION_CD = params.regionCode;
    if (params?.year) queryParams.YEAR = params.year;

    const data = await this.get<unknown>(
      HugAdapter.ENDPOINTS.newDistribution,
      queryParams
    );
    return HugAdapter.normalizeNewDistributionResponse(data);
  }

  /**
   * 지역별 ㎡당 분양가격지수 조회
   */
  async getPriceIndex(params?: {
    regionCode?: string;
    year?: string;
    month?: string;
  }): Promise<HugNormalizedResponse<HugPriceIndexItem>> {
    const validation = HugAdapter.validateParams(params || {});
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
      serviceKey: this.hugApiKey,
    };
    if (params?.regionCode) queryParams.REGION_CD = params.regionCode;
    if (params?.year) queryParams.YEAR = params.year;
    if (params?.month) queryParams.MONTH = params.month;

    const data = await this.get<unknown>(
      HugAdapter.ENDPOINTS.priceIndex,
      queryParams
    );
    return HugAdapter.normalizePriceIndexResponse(data);
  }

  /**
   * 지역별 ㎡당 분양가격 조회
   */
  async getPricePerSqm(params?: {
    regionCode?: string;
    year?: string;
    month?: string;
  }): Promise<HugNormalizedResponse<HugPricePerSqmItem>> {
    const validation = HugAdapter.validateParams(params || {});
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
      serviceKey: this.hugApiKey,
    };
    if (params?.regionCode) queryParams.REGION_CD = params.regionCode;
    if (params?.year) queryParams.YEAR = params.year;
    if (params?.month) queryParams.MONTH = params.month;

    const data = await this.get<unknown>(
      HugAdapter.ENDPOINTS.pricePerSqm,
      queryParams
    );
    return HugAdapter.normalizePricePerSqmResponse(data);
  }

  /**
   * 모든 엔드포인트 목록 조회
   */
  getAvailableEndpoints(): Array<{
    endpoint: HugEndpointType;
    name: string;
    path: string;
  }> {
    return (Object.keys(HugAdapter.ENDPOINTS) as HugEndpointType[]).map(endpoint => ({
      endpoint,
      name: HugAdapter.ENDPOINT_NAMES[endpoint],
      path: HugAdapter.ENDPOINTS[endpoint],
    }));
  }
}
