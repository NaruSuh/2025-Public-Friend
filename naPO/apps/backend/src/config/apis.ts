import { ApiEndpointConfig } from '@/types/api.types';

// 사전 정의된 API 엔드포인트
export const predefinedApis: Record<string, ApiEndpointConfig> = {
  // 공공데이터포털 - 선거공약 API
  public_data_election: {
    id: 'public_data_election',
    name: '선거공약정보',
    displayName: '중앙선거관리위원회_선거공약정보',
    baseUrl: 'http://apis.data.go.kr/9760000/ElecPrmsInfoInqireService',
    authType: 'api_key',
    authConfig: {
      keyParamName: 'ServiceKey',
      keyLocation: 'query',
    },
    responseFormat: 'json',
    rateLimit: {
      requestsPerMinute: 100,
      requestsPerDay: 10000,
    },
    endpoints: {
      getPromises: '/getCnddtElecPrmsInfoInqire',
    },
  },

  // 공공데이터포털 - 당선인 정보
  public_data_winner: {
    id: 'public_data_winner',
    name: '당선인정보',
    displayName: '중앙선거관리위원회_당선인정보',
    baseUrl: 'http://apis.data.go.kr/9760000/WinnerInfoInqireService2',
    authType: 'api_key',
    authConfig: {
      keyParamName: 'ServiceKey',
      keyLocation: 'query',
    },
    responseFormat: 'json',
    endpoints: {
      getWinners: '/getWinnerInfoInqire',
    },
  },

  // 공공데이터포털 - 후보자 정보
  public_data_candidate: {
    id: 'public_data_candidate',
    name: '후보자정보',
    displayName: '중앙선거관리위원회_후보자정보',
    baseUrl: 'http://apis.data.go.kr/9760000/PofelcddInfoInqireService',
    authType: 'api_key',
    authConfig: {
      keyParamName: 'ServiceKey',
      keyLocation: 'query',
    },
    responseFormat: 'json',
    endpoints: {
      getCandidates: '/getPoelpcddRegistSttusInfoInqire',
    },
  },

  // 공공데이터포털 - 코드관리 API
  public_data_common_code: {
    id: 'public_data_common_code',
    name: '코드관리',
    displayName: '중앙선거관리위원회_코드관리',
    baseUrl: 'http://apis.data.go.kr/9760000/CommonCodeService',
    authType: 'api_key',
    authConfig: {
      keyParamName: 'ServiceKey',
      keyLocation: 'query',
    },
    responseFormat: 'json',
    endpoints: {
      getElectionCodes: '/getCommonSgCodeList',
      getDistrictCodes: '/getCommonGusigunCodeList',
      getConstituencyCodes: '/getCommonSggCodeList',
      getPartyCodes: '/getCommonPartyCodeList',
      getJobCodes: '/getCommonJobCodeList',
      getEducationCodes: '/getCommonEduBckgrdCodeList',
    },
  },

  // 공공데이터포털 - 정당정책 정보 API
  public_data_party_policy: {
    id: 'public_data_party_policy',
    name: '정당정책정보',
    displayName: '중앙선거관리위원회_정당정책정보',
    baseUrl: 'http://apis.data.go.kr/9760000/PartyPlcInfoInqireService',
    authType: 'api_key',
    authConfig: {
      keyParamName: 'ServiceKey',
      keyLocation: 'query',
    },
    responseFormat: 'json',
    endpoints: {
      getPartyPolicy: '/getPartyPlcInfoInqire',
    },
  },

  // R-ONE 부동산 통계정보 API
  rone: {
    id: 'rone',
    name: 'R-ONE부동산통계',
    displayName: 'R-ONE 부동산통계정보',
    baseUrl: 'https://www.reb.or.kr/r-one/openapi',
    authType: 'api_key',
    authConfig: {
      keyParamName: 'KEY',
      keyLocation: 'query',
    },
    responseFormat: 'json',
    endpoints: {
      getTableList: '/SttsApiTbl.do',      // 서비스 통계목록 조회
      getTableItems: '/SttsApiTblItm.do',  // 통계 세부항목 목록 조회
      getTableData: '/SttsApiTblData.do',  // 통계 조회 조건 설정
    },
    defaultParams: {
      Type: 'json',
      pIndex: '1',
      pSize: '100',
    },
  },
};

// API 레지스트리 (런타임에 동적 추가 가능)
export class ApiRegistry {
  private static instance: ApiRegistry;
  private apis: Map<string, ApiEndpointConfig> = new Map();

  private constructor() {
    // 사전 정의된 API 로드
    Object.entries(predefinedApis).forEach(([id, config]) => {
      this.apis.set(id, config);
    });
  }

  static getInstance(): ApiRegistry {
    if (!ApiRegistry.instance) {
      ApiRegistry.instance = new ApiRegistry();
    }
    return ApiRegistry.instance;
  }

  register(config: ApiEndpointConfig): void {
    this.apis.set(config.id, config);
  }

  get(id: string): ApiEndpointConfig | undefined {
    return this.apis.get(id);
  }

  getAll(): ApiEndpointConfig[] {
    return Array.from(this.apis.values());
  }

  remove(id: string): boolean {
    return this.apis.delete(id);
  }
}
