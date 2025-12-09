import { BaseApiConnector } from './baseConnector';
import { ApiEndpointConfig, ApiResponse } from '@/types/api.types';
import { env } from '@/config/env';
import { predefinedApis } from '@/config/apis';

// 공공데이터포털 선거공약 API 커넥터
export class ElectionPromiseConnector extends BaseApiConnector {
  constructor() {
    const config = predefinedApis.public_data_election;
    if (!config) {
      throw new Error('public_data_election API configuration not found');
    }
    super(config);
  }

  protected getApiKey(): string | undefined {
    return env.PUBLIC_DATA_API_KEY;
  }

  // 당선인 공약 조회
  async getPromises(params: {
    sgId: string; // 선거ID (예: 20220601)
    sgTypecode: string; // 선거종류코드 (3=시도지사, 4=구시군장)
    cnddtId: string; // 후보자ID
    pageNo?: number;
    numOfRows?: number;
  }): Promise<ApiResponse> {
    return this.fetch({
      endpoint: '/getCnddtElecPrmsInfoInqire',
      params: {
        ...params,
        pageNo: params.pageNo || 1,
        numOfRows: params.numOfRows || 10,
      },
    });
  }
}

// 당선인 정보 API 커넥터
export class WinnerInfoConnector extends BaseApiConnector {
  constructor() {
    const config = predefinedApis.public_data_winner;
    if (!config) {
      throw new Error('public_data_winner API configuration not found');
    }
    super(config);
  }

  protected getApiKey(): string | undefined {
    return env.PUBLIC_DATA_API_KEY;
  }

  // 당선인 목록 조회
  async getWinners(params: {
    sgId: string;
    sgTypecode: string;
    sdName?: string; // 시도명
    pageNo?: number;
    numOfRows?: number;
  }): Promise<ApiResponse> {
    return this.fetch({
      endpoint: '/getWinnerInfoInqire',
      params: {
        ...params,
        pageNo: params.pageNo || 1,
        numOfRows: params.numOfRows || 100,
      },
    });
  }

  // 모든 당선인 조회 (페이징 자동 처리)
  async getAllWinners(sgId: string, sgTypecode: string): Promise<ApiResponse> {
    const allItems: any[] = [];
    let pageNo = 1;
    let totalCount = 0;

    do {
      const response = await this.getWinners({
        sgId,
        sgTypecode,
        pageNo,
        numOfRows: 100,
      });

      if (!response.success) {
        return response;
      }

      const items = Array.isArray(response.data) ? response.data : [response.data];
      allItems.push(...items.filter(Boolean));

      totalCount = response.metadata?.totalCount || 0;
      pageNo++;

      // Rate limiting
      await new Promise((resolve) => setTimeout(resolve, 500));
    } while (allItems.length < totalCount);

    return {
      success: true,
      data: allItems,
      metadata: {
        requestId: `batch-${Date.now()}`,
        timestamp: new Date().toISOString(),
        source: this.config.id,
        totalCount: allItems.length,
      },
    };
  }
}

// 후보자 정보 API 커넥터
export class CandidateInfoConnector extends BaseApiConnector {
  constructor() {
    const config = predefinedApis.public_data_candidate;
    if (!config) {
      throw new Error('public_data_candidate API configuration not found');
    }
    super(config);
  }

  protected getApiKey(): string | undefined {
    return env.PUBLIC_DATA_API_KEY;
  }

  // 후보자 목록 조회
  async getCandidates(params: {
    sgId: string;
    sgTypecode: string;
    sdName?: string;
    wiwName?: string;
    pageNo?: number;
    numOfRows?: number;
  }): Promise<ApiResponse> {
    return this.fetch({
      endpoint: '/getPoelpcddRegistSttusInfoInqire',
      params: {
        ...params,
        pageNo: params.pageNo || 1,
        numOfRows: params.numOfRows || 100,
      },
    });
  }
}
