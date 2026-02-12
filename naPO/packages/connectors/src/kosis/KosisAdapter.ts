/**
 * KOSIS API Adapter
 * 통계청 국가통계포털 KOSIS Open API 응답 정규화 및 유틸리티
 *
 * API 정보:
 * - 서비스명: 국가통계포털 KOSIS Open API
 * - 제공기관: 통계청
 * - Base URL: https://kosis.kr/openapi
 * - 인증방식: API Key (Query Parameter: apiKey)
 * - 응답형식: JSON, XML
 *
 * 주요 엔드포인트:
 * - /Param/statisticsParameterData.do: 통계 파라미터 조회
 * - /statisticsData.do: 통계 데이터 조회
 * - /statisticsList.do: 통계 목록 조회
 */

import type { QueryFilters, NormalizedResponse, ApiError } from '@labgod/core-types';

// ==========================================
// 타입 정의
// ==========================================

export interface KosisStatListItem {
  LIST_ID: string;
  LIST_NM: string;
  ORG_ID: string;
  TBL_ID: string;
  TBL_NM: string;
  STAT_ID: string;
  STAT_NM: string;
  START_PRD: string;
  END_PRD: string;
  PRD_SE: string;
  PRD_DE: string;
}

export interface KosisStatDataItem {
  TBL_ID: string;
  TBL_NM: string;
  ORG_ID: string;
  ORG_NM?: string;
  ITM_ID: string;
  ITM_NM: string;
  ITM_NM_ENG?: string;
  UNIT_NM?: string;
  UNIT_NM_ENG?: string;
  PRD_SE: string;
  PRD_DE: string;
  DT: string;
  C1?: string;
  C1_NM?: string;
  C2?: string;
  C2_NM?: string;
  C3?: string;
  C3_NM?: string;
}

export interface KosisParamItem {
  ORG_ID: string;
  TBL_ID: string;
  OBJ_ID: string;
  OBJ_NM: string;
  OBJ_NM_ENG?: string;
  ITM_ID: string;
  ITM_NM: string;
  UP_ITM_ID?: string;
}

// ==========================================
// KOSIS Adapter 클래스
// ==========================================

export class KosisAdapter {
  // 주요 기관 ID 매핑
  static readonly ORG_CODES: Record<string, string> = {
    '통계청': '101',
    '고용노동부': '118',
    '보건복지부': '117',
    '교육부': '112',
    '국토교통부': '116',
    '행정안전부': '110',
    '기획재정부': '301',
    '한국은행': '301',
  };

  // 주요 통계 카테고리 매핑
  static readonly STAT_CATEGORIES: Record<string, { orgId: string; keywords: string[] }> = {
    '인구': { orgId: '101', keywords: ['인구', '출생', '사망', '혼인', '이혼'] },
    '가구': { orgId: '101', keywords: ['가구', '세대', '주거'] },
    '고용': { orgId: '101', keywords: ['고용', '취업', '실업', '경제활동'] },
    '물가': { orgId: '101', keywords: ['물가', '소비자물가', 'CPI'] },
    '경제성장': { orgId: '301', keywords: ['GDP', '경제성장', '국내총생산'] },
  };

  // 주기 코드 매핑
  static readonly PERIOD_CODES: Record<string, string> = {
    '월': 'M',
    '월간': 'M',
    '분기': 'Q',
    '분기별': 'Q',
    '연': 'Y',
    '연간': 'Y',
    '년': 'Y',
  };

  // 에러 코드 매핑
  private static readonly ERROR_CODES: Record<string, string> = {
    'INFO-000': '정상 처리',
    'INFO-100': '인증키 없음',
    'INFO-200': '데이터 없음',
    'INFO-300': '필수 파라미터 누락',
    'ERROR-001': '서버 오류',
    'ERROR-100': '인증키 오류',
    'ERROR-200': '호출 횟수 초과',
  };

  // 주요 인구통계 표 목록
  static readonly POPULAR_TABLES = {
    population: { orgId: '101', tblId: 'DT_1B040M1', name: '주민등록인구현황' },
    employment: { orgId: '101', tblId: 'DT_1DA7012S', name: '경제활동인구조사' },
    cpi: { orgId: '101', tblId: 'DT_1J20003', name: '소비자물가지수' },
    gdp: { orgId: '301', tblId: 'DT_111Y002', name: '국내총생산' },
  };

  /**
   * QueryFilters를 KOSIS API 파라미터로 변환
   */
  static adaptFilters(filters: QueryFilters): Record<string, unknown> {
    const params: Record<string, unknown> = {
      method: 'getList',
      format: 'json',
      jsonVD: 'Y',
    };

    // 키워드에서 기관 ID 추론
    if (filters.keywords) {
      const orgId = this.inferOrgFromKeywords(filters.keywords);
      if (orgId) {
        params.orgId = orgId;
      }
      params.searchNm = filters.keywords.join(' ');
    }

    // 날짜 범위 (KOSIS는 YYYYMM 형식)
    if (filters.dateRange) {
      if (filters.dateRange.start) {
        params.startPrdDe = filters.dateRange.start.replace(/-/g, '').substring(0, 6);
      }
      if (filters.dateRange.end) {
        params.endPrdDe = filters.dateRange.end.replace(/-/g, '').substring(0, 6);
      }
    }

    // 주기 필터
    if (filters.custom?.period) {
      params.prdSe = filters.custom.period;
    } else if (filters.keywords) {
      const period = this.inferPeriodFromKeywords(filters.keywords);
      if (period) {
        params.prdSe = period;
      }
    }

    // 통계표 ID가 직접 제공된 경우
    if (filters.custom?.tblId) params.tblId = filters.custom.tblId;
    if (filters.custom?.orgId) params.orgId = filters.custom.orgId;

    return params;
  }

  /**
   * 키워드에서 기관 ID 추론
   */
  private static inferOrgFromKeywords(keywords: string[]): string | null {
    const text = keywords.join(' ');

    for (const [orgName, orgId] of Object.entries(this.ORG_CODES)) {
      if (text.includes(orgName)) return orgId;
    }

    for (const [, category] of Object.entries(this.STAT_CATEGORIES)) {
      for (const keyword of category.keywords) {
        if (text.includes(keyword)) return category.orgId;
      }
    }

    return '101'; // 기본값: 통계청
  }

  /**
   * 키워드에서 주기 추론
   */
  private static inferPeriodFromKeywords(keywords: string[]): string | null {
    const text = keywords.join(' ');
    for (const [keyword, code] of Object.entries(this.PERIOD_CODES)) {
      if (text.includes(keyword)) return code;
    }
    return null;
  }

  /**
   * 통계 목록 응답 정규화
   */
  static normalizeListResponse(data: unknown): NormalizedResponse<KosisStatListItem> {
    if (this.isErrorResponse(data)) {
      const errData = data as { err?: string; errMsg?: string };
      return {
        success: false,
        totalCount: 0,
        page: 1,
        pageSize: 0,
        data: [],
        error: {
          code: errData.err || 'UNKNOWN',
          message: this.getErrorMessage(errData.err || 'UNKNOWN'),
        },
        _raw: data,
      };
    }

    if (Array.isArray(data)) {
      return {
        success: true,
        totalCount: data.length,
        page: 1,
        pageSize: data.length,
        data: data.map(item => this.normalizeListItem(item)),
        _raw: data,
      };
    }

    const dataObj = data as Record<string, unknown>;
    if (dataObj.StatisticsList && Array.isArray(dataObj.StatisticsList)) {
      const items = dataObj.StatisticsList as unknown[];
      return {
        success: true,
        totalCount: items.length,
        page: 1,
        pageSize: items.length,
        data: items.map(item => this.normalizeListItem(item)),
        _raw: data,
      };
    }

    return { success: true, totalCount: 0, page: 1, pageSize: 0, data: [], _raw: data };
  }

  /**
   * 통계 데이터 응답 정규화
   */
  static normalizeDataResponse(data: unknown): NormalizedResponse<KosisStatDataItem> {
    if (this.isErrorResponse(data)) {
      const errData = data as { err?: string; errMsg?: string };
      return {
        success: false,
        totalCount: 0,
        page: 1,
        pageSize: 0,
        data: [],
        error: {
          code: errData.err || 'UNKNOWN',
          message: this.getErrorMessage(errData.err || 'UNKNOWN'),
        },
        _raw: data,
      };
    }

    if (Array.isArray(data)) {
      return {
        success: true,
        totalCount: data.length,
        page: 1,
        pageSize: data.length,
        data: data.map(item => this.normalizeDataItem(item)),
        _raw: data,
      };
    }

    return { success: true, totalCount: 0, page: 1, pageSize: 0, data: [], _raw: data };
  }

  private static isErrorResponse(data: unknown): boolean {
    if (typeof data !== 'object' || data === null) return false;
    const obj = data as Record<string, unknown>;
    return obj.err !== undefined && String(obj.err).startsWith('ERROR');
  }

  private static getErrorMessage(errorCode: string): string {
    return this.ERROR_CODES[errorCode] || `알 수 없는 오류: ${errorCode}`;
  }

  private static normalizeListItem(item: unknown): KosisStatListItem {
    const obj = item as Record<string, unknown>;
    return {
      LIST_ID: String(obj.LIST_ID || obj.listId || ''),
      LIST_NM: String(obj.LIST_NM || obj.listNm || ''),
      ORG_ID: String(obj.ORG_ID || obj.orgId || ''),
      TBL_ID: String(obj.TBL_ID || obj.tblId || ''),
      TBL_NM: String(obj.TBL_NM || obj.tblNm || ''),
      STAT_ID: String(obj.STAT_ID || obj.statId || ''),
      STAT_NM: String(obj.STAT_NM || obj.statNm || ''),
      START_PRD: String(obj.START_PRD || obj.startPrd || ''),
      END_PRD: String(obj.END_PRD || obj.endPrd || ''),
      PRD_SE: String(obj.PRD_SE || obj.prdSe || ''),
      PRD_DE: String(obj.PRD_DE || obj.prdDe || ''),
    };
  }

  private static normalizeDataItem(item: unknown): KosisStatDataItem {
    const obj = item as Record<string, unknown>;
    return {
      TBL_ID: String(obj.TBL_ID || obj.tblId || ''),
      TBL_NM: String(obj.TBL_NM || obj.tblNm || ''),
      ORG_ID: String(obj.ORG_ID || obj.orgId || ''),
      ORG_NM: obj.ORG_NM ? String(obj.ORG_NM) : undefined,
      ITM_ID: String(obj.ITM_ID || obj.itmId || ''),
      ITM_NM: String(obj.ITM_NM || obj.itmNm || ''),
      ITM_NM_ENG: obj.ITM_NM_ENG ? String(obj.ITM_NM_ENG) : undefined,
      UNIT_NM: obj.UNIT_NM ? String(obj.UNIT_NM) : undefined,
      UNIT_NM_ENG: obj.UNIT_NM_ENG ? String(obj.UNIT_NM_ENG) : undefined,
      PRD_SE: String(obj.PRD_SE || obj.prdSe || ''),
      PRD_DE: String(obj.PRD_DE || obj.prdDe || ''),
      DT: String(obj.DT || obj.dt || ''),
      C1: obj.C1 ? String(obj.C1) : undefined,
      C1_NM: obj.C1_NM ? String(obj.C1_NM) : undefined,
      C2: obj.C2 ? String(obj.C2) : undefined,
      C2_NM: obj.C2_NM ? String(obj.C2_NM) : undefined,
      C3: obj.C3 ? String(obj.C3) : undefined,
      C3_NM: obj.C3_NM ? String(obj.C3_NM) : undefined,
    };
  }

  /**
   * 파라미터 검증 - 통계 목록 조회
   */
  static validateListParams(params: Record<string, unknown>): { valid: boolean; errors?: string[] } {
    const errors: string[] = [];
    if (params.method && !['getList', 'getMeta'].includes(String(params.method))) {
      errors.push('method는 getList 또는 getMeta이어야 합니다');
    }
    return { valid: errors.length === 0, errors: errors.length > 0 ? errors : undefined };
  }

  /**
   * 파라미터 검증 - 통계 데이터 조회
   */
  static validateDataParams(params: Record<string, unknown>): { valid: boolean; errors?: string[] } {
    const errors: string[] = [];
    if (!params.orgId) errors.push('orgId는 필수 파라미터입니다');
    if (!params.tblId) errors.push('tblId는 필수 파라미터입니다');
    return { valid: errors.length === 0, errors: errors.length > 0 ? errors : undefined };
  }

  /**
   * 키워드에서 인기 통계표 추론
   */
  static inferPopularTable(keywords: string[]): { orgId: string; tblId: string; name: string } | null {
    const text = keywords.join(' ');
    if (text.includes('인구') || text.includes('주민등록')) return this.POPULAR_TABLES.population;
    if (text.includes('고용') || text.includes('취업') || text.includes('실업')) return this.POPULAR_TABLES.employment;
    if (text.includes('물가') || text.includes('CPI')) return this.POPULAR_TABLES.cpi;
    if (text.includes('GDP') || text.includes('국내총생산') || text.includes('경제성장')) return this.POPULAR_TABLES.gdp;
    return null;
  }

  /**
   * 지역별 인구 데이터 조회용 파라미터 생성
   */
  static buildPopulationParams(region?: string, year?: string): Record<string, unknown> {
    const params: Record<string, unknown> = {
      method: 'getList',
      format: 'json',
      jsonVD: 'Y',
      orgId: '101',
      tblId: 'DT_1B040M1',
    };
    if (year) params.prdDe = year;
    return params;
  }

  /**
   * 데이터 요약 생성
   */
  static generateSummary(data: KosisStatDataItem[]): {
    totalRecords: number;
    dateRange: { start: string; end: string } | null;
    categories: string[];
    units: string[];
  } {
    if (data.length === 0) {
      return { totalRecords: 0, dateRange: null, categories: [], units: [] };
    }

    const periods = data.map(d => d.PRD_DE).sort();
    const categories = [...new Set(data.map(d => d.C1_NM).filter(Boolean))] as string[];
    const units = [...new Set(data.map(d => d.UNIT_NM).filter(Boolean))] as string[];

    return {
      totalRecords: data.length,
      dateRange: periods.length > 0 ? { start: periods[0] || '', end: periods[periods.length - 1] || '' } : null,
      categories,
      units,
    };
  }
}
