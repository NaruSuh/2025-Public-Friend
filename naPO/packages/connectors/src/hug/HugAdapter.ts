/**
 * HUG API Adapter
 * 주택도시보증공사 Open API 응답 정규화 및 유틸리티
 *
 * API 정보:
 * - 서비스명: 주택도시보증공사 공공데이터 Open API
 * - 제공기관: 주택도시보증공사 (HUG)
 * - Base URL: https://www.khug.or.kr
 * - 인증방식: API Key (Query Parameter: serviceKey)
 * - 응답형식: XML
 *
 * 주요 엔드포인트 (8개):
 * 1. /areaBusinessDistributionGuaranteeStatus.do  - 분양보증현황(지역)
 * 2. /amountOfGuranteePrivateDistributionApt.do   - 민간분양아파트 보증금액(지역별)
 * 3. /rateOfBuildingDistributionApt.do             - 분양아파트 공정률(지역별)
 * 4. /amountPFLoanStatus.do                        - PF대출금액 현황(연도별, 지역별)
 * 5. /distributeDistributionGuaranteeStatus.do     - 분양보증 분양이행 현황(연도별, 지역별)
 * 6. /newDistributionNumber.do                     - 신규 분양세대수(지역별)
 * 7. /siltPwnIndxDistributedBySize.do              - 지역별 ㎡당 분양가격지수(지역)
 * 8. /priceDistributedPrice3dot3.do                - 지역별 ㎡당 분양가격(지역)
 *
 * 공통 파라미터:
 * - serviceKey: 인증키 (필수)
 * - 지역코드: 01~16 (서울~울산)
 * - 년도/기간: 엔드포인트별 상이
 */

import type { QueryFilters } from '@labgod/core-types';

// ==========================================
// 타입 정의
// ==========================================

/** 분양보증현황(지역) */
export interface HugDistributionGuaranteeItem {
  regionCode: string;       // 지역코드
  regionName: string;       // 지역명
  year: string;             // 연도
  guaranteeCount: number;   // 보증건수
  guaranteeAmount: number;  // 보증금액
  householdCount: number;   // 세대수
}

/** 민간분양아파트 보증금액(지역별) */
export interface HugGuaranteeAmountItem {
  regionCode: string;
  regionName: string;
  year: string;
  guaranteeAmount: number;  // 보증금액
}

/** 분양아파트 공정률(지역별) */
export interface HugConstructionRateItem {
  regionCode: string;
  regionName: string;
  year: string;
  constructionRate: number; // 공정률 (%)
}

/** PF대출금액 현황(연도별, 지역별) */
export interface HugPfLoanItem {
  regionCode: string;
  regionName: string;
  year: string;
  loanAmount: number;       // PF대출금액
}

/** 분양보증 분양이행 현황(연도별, 지역별) */
export interface HugDistributionPerformanceItem {
  regionCode: string;
  regionName: string;
  year: string;
  performanceCount: number; // 이행건수
  performanceAmount: number; // 이행금액
}

/** 신규 분양세대수(지역별) */
export interface HugNewDistributionItem {
  regionCode: string;
  regionName: string;
  year: string;
  householdCount: number;   // 신규 분양세대수
}

/** 지역별 ㎡당 분양가격지수 */
export interface HugPriceIndexItem {
  regionCode: string;
  regionName: string;
  year: string;
  month?: string;
  priceIndex: number;       // 분양가격지수
}

/** 지역별 ㎡당 분양가격 */
export interface HugPricePerSqmItem {
  regionCode: string;
  regionName: string;
  year: string;
  month?: string;
  pricePerSqm: number;     // ㎡당 분양가격 (원)
}

/** 공통 정규화 응답 타입 */
export interface HugNormalizedResponse<T> {
  success: boolean;
  totalCount: number;
  page: number;
  pageSize: number;
  data: T[];
  error?: {
    code: string;
    message: string;
  };
  _raw?: unknown;
}

/** HUG 엔드포인트 타입 */
export type HugEndpointType =
  | 'distributionGuarantee'
  | 'guaranteeAmount'
  | 'constructionRate'
  | 'pfLoanAmount'
  | 'distributionPerformance'
  | 'newDistribution'
  | 'priceIndex'
  | 'pricePerSqm';

// ==========================================
// HUG Adapter 클래스
// ==========================================

export class HugAdapter {
  // HUG 지역코드 매핑 (01~16)
  static readonly REGION_CODES: Record<string, string> = {
    '서울': '01',
    '부산': '02',
    '대구': '03',
    '인천': '04',
    '광주': '05',
    '대전': '06',
    '경기': '07',
    '강원': '08',
    '충북': '09',
    '충남': '10',
    '전북': '11',
    '전남': '12',
    '경북': '13',
    '경남': '14',
    '제주': '15',
    '울산': '16',
  };

  // 역방향 매핑 (코드 → 지역명)
  static readonly REGION_NAMES: Record<string, string> = Object.fromEntries(
    Object.entries(HugAdapter.REGION_CODES).map(([name, code]) => [code, name])
  );

  // 엔드포인트 경로 매핑
  static readonly ENDPOINTS: Record<HugEndpointType, string> = {
    distributionGuarantee: '/areaBusinessDistributionGuaranteeStatus.do',
    guaranteeAmount: '/amountOfGuranteePrivateDistributionApt.do',
    constructionRate: '/rateOfBuildingDistributionApt.do',
    pfLoanAmount: '/amountPFLoanStatus.do',
    distributionPerformance: '/distributeDistributionGuaranteeStatus.do',
    newDistribution: '/newDistributionNumber.do',
    priceIndex: '/siltPwnIndxDistributedBySize.do',
    pricePerSqm: '/priceDistributedPrice3dot3.do',
  };

  // 엔드포인트별 한글 설명
  static readonly ENDPOINT_NAMES: Record<HugEndpointType, string> = {
    distributionGuarantee: '분양보증현황(지역)',
    guaranteeAmount: '민간분양아파트 보증금액(지역별)',
    constructionRate: '분양아파트 공정률(지역별)',
    pfLoanAmount: 'PF대출금액 현황(연도별, 지역별)',
    distributionPerformance: '분양보증 분양이행 현황(연도별, 지역별)',
    newDistribution: '신규 분양세대수(지역별)',
    priceIndex: '지역별 ㎡당 분양가격지수',
    pricePerSqm: '지역별 ㎡당 분양가격',
  };

  // 키워드 → 엔드포인트 매핑
  private static readonly KEYWORD_ENDPOINT_MAP: Array<{ keywords: RegExp; endpoint: HugEndpointType }> = [
    { keywords: /PF|프로젝트파이낸싱|PF대출/, endpoint: 'pfLoanAmount' },
    { keywords: /분양가격지수|가격지수/, endpoint: 'priceIndex' },
    { keywords: /분양가격|분양가|㎡당/, endpoint: 'pricePerSqm' },
    { keywords: /공정률|공정|진행률/, endpoint: 'constructionRate' },
    { keywords: /분양이행|이행현황|이행/, endpoint: 'distributionPerformance' },
    { keywords: /신규\s*분양|신규\s*세대|분양세대/, endpoint: 'newDistribution' },
    { keywords: /보증금액|보증\s*금/, endpoint: 'guaranteeAmount' },
    { keywords: /분양보증|보증현황|보증/, endpoint: 'distributionGuarantee' },
  ];

  /**
   * QueryFilters를 HUG API 파라미터로 변환
   */
  static adaptFilters(filters: QueryFilters): Record<string, unknown> {
    const params: Record<string, unknown> = {};

    // 지역 필터
    if (filters.region) {
      let regionCode: string | undefined;
      if (typeof filters.region === 'object') {
        regionCode = this.REGION_CODES[filters.region.sido || ''];
      } else if (typeof filters.region === 'string') {
        regionCode = this.REGION_CODES[filters.region];
      }
      if (regionCode) {
        params.regionCode = regionCode;
      }
    }

    // 키워드에서 지역 추출
    if (filters.keywords && !params.regionCode) {
      const region = this.extractRegionFromKeywords(filters.keywords);
      if (region) {
        params.regionCode = region;
      }
    }

    // 연도 설정
    if (filters.dateRange?.start) {
      params.year = filters.dateRange.start.substring(0, 4);
    } else if (filters.custom?.year) {
      params.year = String(filters.custom.year);
    }

    // 키워드에서 엔드포인트 추론
    if (filters.keywords) {
      const endpoint = this.inferEndpointFromKeywords(filters.keywords);
      if (endpoint) {
        params._endpoint = endpoint;
        params._endpointName = this.ENDPOINT_NAMES[endpoint];
      }
    }

    // 직접 지정된 엔드포인트
    if (filters.custom?.endpoint) {
      params._endpoint = filters.custom.endpoint;
    }

    return params;
  }

  /**
   * 키워드에서 지역코드 추출
   */
  private static extractRegionFromKeywords(keywords: string[]): string | null {
    const text = keywords.join(' ');

    for (const [region, code] of Object.entries(this.REGION_CODES)) {
      if (text.includes(region)) {
        return code;
      }
    }

    return null;
  }

  /**
   * 키워드에서 적합한 엔드포인트 추론
   */
  static inferEndpointFromKeywords(keywords: string[]): HugEndpointType | null {
    const text = keywords.join(' ');

    for (const { keywords: pattern, endpoint } of this.KEYWORD_ENDPOINT_MAP) {
      if (pattern.test(text)) {
        return endpoint;
      }
    }

    return null;
  }

  /**
   * XML 응답 정규화 (공통)
   *
   * HUG API XML 응답 구조 (fast-xml-parser 파싱 후):
   * {
   *   response: {
   *     header: { resultCode: "00", resultMsg: "NORMAL SERVICE" },
   *     body: {
   *       items: { item: [...] | {...} },
   *       totalCount: N,
   *       pageNo: 1,
   *       numOfRows: 100
   *     }
   *   }
   * }
   */
  static normalizeResponse<T>(
    data: unknown,
    normalizeItem: (item: unknown) => T
  ): HugNormalizedResponse<T> {
    const dataObj = data as Record<string, unknown>;

    // 에러 응답 확인
    if (dataObj?.response) {
      const response = dataObj.response as Record<string, unknown>;
      const header = response.header as Record<string, unknown> | undefined;

      if (header) {
        const resultCode = String(header.resultCode || '');
        if (resultCode !== '00' && resultCode !== '') {
          return {
            success: false,
            totalCount: 0,
            page: 1,
            pageSize: 0,
            data: [],
            error: {
              code: resultCode,
              message: String(header.resultMsg || 'Unknown error'),
            },
            _raw: data,
          };
        }
      }

      const body = response.body as Record<string, unknown> | undefined;
      if (body) {
        const items = body.items as Record<string, unknown> | undefined;
        let itemList: unknown[] = [];

        if (items?.item) {
          itemList = Array.isArray(items.item) ? items.item : [items.item];
        }

        return {
          success: true,
          totalCount: Number(body.totalCount || itemList.length),
          page: Number(body.pageNo || 1),
          pageSize: itemList.length,
          data: itemList.map(item => normalizeItem(item)),
          _raw: data,
        };
      }
    }

    // 배열 형태인 경우 (baseConnector에서 이미 정규화된 경우)
    if (Array.isArray(data)) {
      return {
        success: true,
        totalCount: data.length,
        page: 1,
        pageSize: data.length,
        data: data.map(item => normalizeItem(item)),
        _raw: data,
      };
    }

    // 데이터 없음
    return {
      success: true,
      totalCount: 0,
      page: 1,
      pageSize: 0,
      data: [],
      _raw: data,
    };
  }

  // ==========================================
  // 엔드포인트별 응답 정규화
  // ==========================================

  /** 분양보증현황(지역) 응답 정규화 */
  static normalizeDistributionGuaranteeResponse(
    data: unknown
  ): HugNormalizedResponse<HugDistributionGuaranteeItem> {
    return this.normalizeResponse(data, (item) => {
      const raw = item as Record<string, unknown>;
      const regionCode = String(raw.REGION_CD || raw.regionCd || raw.region_cd || '');
      return {
        regionCode,
        regionName: this.REGION_NAMES[regionCode] || String(raw.REGION_NM || raw.regionNm || ''),
        year: String(raw.YEAR || raw.year || raw.BASE_YEAR || ''),
        guaranteeCount: Number(raw.GRNT_CNT || raw.grntCnt || raw.guarantee_cnt || 0),
        guaranteeAmount: Number(raw.GRNT_AMT || raw.grntAmt || raw.guarantee_amt || 0),
        householdCount: Number(raw.HSHOLD_CNT || raw.hsholdCnt || raw.household_cnt || 0),
      };
    });
  }

  /** 민간분양아파트 보증금액(지역별) 응답 정규화 */
  static normalizeGuaranteeAmountResponse(
    data: unknown
  ): HugNormalizedResponse<HugGuaranteeAmountItem> {
    return this.normalizeResponse(data, (item) => {
      const raw = item as Record<string, unknown>;
      const regionCode = String(raw.REGION_CD || raw.regionCd || raw.region_cd || '');
      return {
        regionCode,
        regionName: this.REGION_NAMES[regionCode] || String(raw.REGION_NM || raw.regionNm || ''),
        year: String(raw.YEAR || raw.year || raw.BASE_YEAR || ''),
        guaranteeAmount: Number(raw.GRNT_AMT || raw.grntAmt || raw.guarantee_amt || 0),
      };
    });
  }

  /** 분양아파트 공정률(지역별) 응답 정규화 */
  static normalizeConstructionRateResponse(
    data: unknown
  ): HugNormalizedResponse<HugConstructionRateItem> {
    return this.normalizeResponse(data, (item) => {
      const raw = item as Record<string, unknown>;
      const regionCode = String(raw.REGION_CD || raw.regionCd || raw.region_cd || '');
      return {
        regionCode,
        regionName: this.REGION_NAMES[regionCode] || String(raw.REGION_NM || raw.regionNm || ''),
        year: String(raw.YEAR || raw.year || raw.BASE_YEAR || ''),
        constructionRate: Number(raw.CMPLT_RT || raw.cmpltRt || raw.construction_rate || 0),
      };
    });
  }

  /** PF대출금액 현황(연도별, 지역별) 응답 정규화 */
  static normalizePfLoanResponse(
    data: unknown
  ): HugNormalizedResponse<HugPfLoanItem> {
    return this.normalizeResponse(data, (item) => {
      const raw = item as Record<string, unknown>;
      const regionCode = String(raw.REGION_CD || raw.regionCd || raw.region_cd || '');
      return {
        regionCode,
        regionName: this.REGION_NAMES[regionCode] || String(raw.REGION_NM || raw.regionNm || ''),
        year: String(raw.YEAR || raw.year || raw.BASE_YEAR || ''),
        loanAmount: Number(raw.LOAN_AMT || raw.loanAmt || raw.pf_loan_amt || 0),
      };
    });
  }

  /** 분양보증 분양이행 현황 응답 정규화 */
  static normalizeDistributionPerformanceResponse(
    data: unknown
  ): HugNormalizedResponse<HugDistributionPerformanceItem> {
    return this.normalizeResponse(data, (item) => {
      const raw = item as Record<string, unknown>;
      const regionCode = String(raw.REGION_CD || raw.regionCd || raw.region_cd || '');
      return {
        regionCode,
        regionName: this.REGION_NAMES[regionCode] || String(raw.REGION_NM || raw.regionNm || ''),
        year: String(raw.YEAR || raw.year || raw.BASE_YEAR || ''),
        performanceCount: Number(raw.PRFM_CNT || raw.prfmCnt || raw.performance_cnt || 0),
        performanceAmount: Number(raw.PRFM_AMT || raw.prfmAmt || raw.performance_amt || 0),
      };
    });
  }

  /** 신규 분양세대수(지역별) 응답 정규화 */
  static normalizeNewDistributionResponse(
    data: unknown
  ): HugNormalizedResponse<HugNewDistributionItem> {
    return this.normalizeResponse(data, (item) => {
      const raw = item as Record<string, unknown>;
      const regionCode = String(raw.REGION_CD || raw.regionCd || raw.region_cd || '');
      return {
        regionCode,
        regionName: this.REGION_NAMES[regionCode] || String(raw.REGION_NM || raw.regionNm || ''),
        year: String(raw.YEAR || raw.year || raw.BASE_YEAR || ''),
        householdCount: Number(raw.HSHOLD_CNT || raw.hsholdCnt || raw.household_cnt || 0),
      };
    });
  }

  /** 지역별 ㎡당 분양가격지수 응답 정규화 */
  static normalizePriceIndexResponse(
    data: unknown
  ): HugNormalizedResponse<HugPriceIndexItem> {
    return this.normalizeResponse(data, (item) => {
      const raw = item as Record<string, unknown>;
      const regionCode = String(raw.REGION_CD || raw.regionCd || raw.region_cd || '');
      return {
        regionCode,
        regionName: this.REGION_NAMES[regionCode] || String(raw.REGION_NM || raw.regionNm || ''),
        year: String(raw.YEAR || raw.year || raw.BASE_YEAR || ''),
        month: raw.MONTH ? String(raw.MONTH) : raw.month ? String(raw.month) : undefined,
        priceIndex: Number(raw.PRC_INDX || raw.prcIndx || raw.price_index || 0),
      };
    });
  }

  /** 지역별 ㎡당 분양가격 응답 정규화 */
  static normalizePricePerSqmResponse(
    data: unknown
  ): HugNormalizedResponse<HugPricePerSqmItem> {
    return this.normalizeResponse(data, (item) => {
      const raw = item as Record<string, unknown>;
      const regionCode = String(raw.REGION_CD || raw.regionCd || raw.region_cd || '');
      return {
        regionCode,
        regionName: this.REGION_NAMES[regionCode] || String(raw.REGION_NM || raw.regionNm || ''),
        year: String(raw.YEAR || raw.year || raw.BASE_YEAR || ''),
        month: raw.MONTH ? String(raw.MONTH) : raw.month ? String(raw.month) : undefined,
        pricePerSqm: Number(raw.PRC_PER_SQM || raw.prcPerSqm || raw.price_per_sqm || 0),
      };
    });
  }

  /**
   * 엔드포인트 유형별 응답 정규화 선택
   */
  static normalizeByEndpoint(
    endpoint: HugEndpointType,
    data: unknown
  ): HugNormalizedResponse<unknown> {
    switch (endpoint) {
      case 'distributionGuarantee':
        return this.normalizeDistributionGuaranteeResponse(data);
      case 'guaranteeAmount':
        return this.normalizeGuaranteeAmountResponse(data);
      case 'constructionRate':
        return this.normalizeConstructionRateResponse(data);
      case 'pfLoanAmount':
        return this.normalizePfLoanResponse(data);
      case 'distributionPerformance':
        return this.normalizeDistributionPerformanceResponse(data);
      case 'newDistribution':
        return this.normalizeNewDistributionResponse(data);
      case 'priceIndex':
        return this.normalizePriceIndexResponse(data);
      case 'pricePerSqm':
        return this.normalizePricePerSqmResponse(data);
      default:
        return this.normalizeDistributionGuaranteeResponse(data);
    }
  }

  // ==========================================
  // 유틸리티
  // ==========================================

  /**
   * 지역명 → 코드 변환
   */
  static getRegionCode(regionName: string): string | null {
    return this.REGION_CODES[regionName] || null;
  }

  /**
   * 지역코드 → 지역명 변환
   */
  static getRegionName(code: string): string | null {
    return this.REGION_NAMES[code] || null;
  }

  /**
   * 파라미터 검증
   */
  static validateParams(params: Record<string, unknown>): {
    valid: boolean;
    errors?: string[];
  } {
    const errors: string[] = [];

    // 지역코드 검증
    if (params.regionCode) {
      const code = String(params.regionCode);
      if (!this.REGION_NAMES[code]) {
        errors.push(`유효하지 않은 지역코드: ${code} (01~16)`);
      }
    }

    // 연도 검증
    if (params.year) {
      const year = parseInt(String(params.year));
      if (isNaN(year) || year < 2000 || year > new Date().getFullYear()) {
        errors.push('year는 2000년부터 현재 연도 사이의 값이어야 합니다');
      }
    }

    return {
      valid: errors.length === 0,
      errors: errors.length > 0 ? errors : undefined,
    };
  }

  /**
   * 데이터 요약 생성
   */
  static generateSummary(data: Array<Record<string, unknown>>, endpointType: HugEndpointType): {
    totalRecords: number;
    endpointName: string;
    regions: string[];
    years: string[];
  } {
    if (data.length === 0) {
      return {
        totalRecords: 0,
        endpointName: this.ENDPOINT_NAMES[endpointType],
        regions: [],
        years: [],
      };
    }

    const regions = [...new Set(data.map(d => {
      const regionCode = String(d.regionCode || d.REGION_CD || '');
      return this.REGION_NAMES[regionCode] || regionCode;
    }).filter(Boolean))];

    const years = [...new Set(data.map(d =>
      String(d.year || d.YEAR || d.BASE_YEAR || '')
    ).filter(Boolean))].sort();

    return {
      totalRecords: data.length,
      endpointName: this.ENDPOINT_NAMES[endpointType],
      regions,
      years,
    };
  }
}
