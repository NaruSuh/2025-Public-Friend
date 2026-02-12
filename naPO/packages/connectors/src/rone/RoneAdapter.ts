/**
 * R-ONE API Adapter
 * 한국부동산원 부동산통계정보 API 응답 정규화 및 유틸리티
 *
 * 공식 API 문서 기반: 기술문서_부동산통계 Open API 서비스_250721.pdf
 *
 * API 정보:
 * - 서비스명: 부동산통계 Open API
 * - Endpoints:
 *   - SttsApiTbl.do: 통계목록 조회
 *   - SttsApiTblItm.do: 통계 세부항목 조회
 *   - SttsApiTblData.do: 통계 데이터 조회
 * - Base URL: https://www.reb.or.kr/r-one/openApi
 * - 인증: API Key (한국부동산원 발급)
 *
 * 주요 파라미터:
 * - TBL_ID: 통계표 ID
 * - ITM_ID: 항목 ID
 * - pIndex: 페이지 번호
 * - pSize: 페이지 크기
 * - Type: 응답 형식 (json/xml)
 */

import type { QueryFilters } from '@labgod/core-types';

export interface RoneTableListItem {
  TBL_ID: string;        // 통계표 ID
  TBL_NM: string;        // 통계표명
  ORG_ID: string;        // 제공기관코드
  ORG_NM: string;        // 제공기관명
  CLS_ID: string;        // 분류코드
  CLS_NM: string;        // 분류명
  LST_DT: string;        // 최종수정일
  CYCLE: string;         // 주기코드 (YY/HY/QY/MM/WK)
  CYCLE_NM: string;      // 주기명
  KEY_YN: string;        // 주요통계여부 (Y/N)
  AREA_YN: string;       // 지역별 제공여부 (Y/N)
  FRM_PRD: string;       // 제공시작일
  TO_PRD: string;        // 제공종료일
}

export interface RoneTableItemsItem {
  TBL_ID: string;        // 통계표 ID
  ITM_ID: string;        // 항목 ID
  ITM_NM: string;        // 항목명
  C1?: string;           // 분류 1
  C1_NM?: string;        // 분류 1 명
  C2?: string;           // 분류 2
  C2_NM?: string;        // 분류 2 명
  C3?: string;           // 분류 3
  C3_NM?: string;        // 분류 3 명
  C4?: string;           // 분류 4
  C4_NM?: string;        // 분류 4 명
  UNIT?: string;         // 단위
}

export interface RoneTableDataItem {
  TBL_ID: string;        // 통계표 ID
  ITM_ID: string;        // 항목 ID
  ITM_NM: string;        // 항목명
  DT: string;            // 일자
  DT_NM: string;         // 일자명
  C1?: string;           // 분류 1
  C1_NM?: string;        // 분류 1 명
  C2?: string;           // 분류 2
  C2_NM?: string;        // 분류 2 명
  C3?: string;           // 분류 3
  C3_NM?: string;        // 분류 3 명
  C4?: string;           // 분류 4
  C4_NM?: string;        // 분류 4 명
  UNIT?: string;         // 단위
  DTA?: string;          // 수치
}

export interface RoneErrorResponse {
  error_code: string;
  error_msg: string;
}

export interface RoneNormalizedResponse<T> {
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

export class RoneAdapter {
  // 주요 부동산 통계 카테고리 매핑
  static readonly STATISTICS_CATEGORIES: Record<string, string[]> = {
    '아파트': ['APT', 'APART', '아파트'],
    '오피스텔': ['OFT', 'OFFICETEL', '오피스텔'],
    '단독주택': ['HOUSE', '단독'],
    '연립다세대': ['ROW', '연립', '다세대'],
    '토지': ['LAND', '토지'],
    '상업용': ['COMM', '상업'],
  };

  // 지역명 매핑
  static readonly REGION_CODES: Record<string, string> = {
    '서울': '11',
    '부산': '21',
    '대구': '22',
    '인천': '23',
    '광주': '24',
    '대전': '25',
    '울산': '26',
    '세종': '29',
    '경기': '31',
    '강원': '32',
    '충북': '33',
    '충남': '34',
    '전북': '35',
    '전남': '36',
    '경북': '37',
    '경남': '38',
    '제주': '39',
    '전국': '00',
  };

  // 주기 코드 매핑 (역방향)
  static readonly CYCLE_KEYWORDS: Record<string, string> = {
    '연간': 'YY',
    '매년': 'YY',
    '년': 'YY',
    '반기': 'HY',
    '분기': 'QY',
    '월간': 'MM',
    '매월': 'MM',
    '월': 'MM',
    '주간': 'WK',
    '매주': 'WK',
    '주': 'WK',
  };

  // 주기 코드 매핑
  private static CYCLE_CODES: Record<string, string> = {
    'YY': '연간',
    'HY': '반기',
    'QY': '분기',
    'MM': '월간',
    'WK': '주간',
  };

  // R-ONE API 에러 코드 매핑
  private static ERROR_CODES: Record<string, string> = {
    'ERROR-300': '필수 파라미터 누락',
    'ERROR-290': '유효하지 않은 파라미터',
    'ERROR-310': '인증키 오류',
    'ERROR-320': '권한 없음',
    'ERROR-330': '일일 트래픽 초과',
    'ERROR-331': '분당 트래픽 초과',
    'ERROR-900': '시스템 오류',
    'INFO-000': '정상 조회 (데이터 존재)',
    'INFO-200': '정상 조회 (데이터 없음)',
  };

  /**
   * QueryFilters를 R-ONE API 파라미터로 변환
   */
  static adaptFilters(filters: QueryFilters): Record<string, unknown> {
    const params: Record<string, unknown> = {
      Type: 'json',
      pIndex: 1,
      pSize: 100,
    };

    // TBL_ID가 직접 제공된 경우
    if (filters.custom?.TBL_ID) {
      params.TBL_ID = filters.custom.TBL_ID;
    }

    // ITM_ID가 직접 제공된 경우
    if (filters.custom?.ITM_ID) {
      params.ITM_ID = filters.custom.ITM_ID;
    }

    // 키워드에서 통계 종류 추론
    if (filters.keywords && !params.TBL_ID) {
      const inferredTable = this.inferTableFromKeywords(filters.keywords);
      if (inferredTable) {
        params._suggestedTable = inferredTable;
      }
    }

    // 지역 필터
    if (filters.region) {
      let regionCode: string | undefined;
      if (typeof filters.region === 'object') {
        regionCode = this.REGION_CODES[filters.region.sido || ''] ||
                     this.REGION_CODES[filters.region.sigungu || ''];
      } else if (typeof filters.region === 'string') {
        regionCode = this.REGION_CODES[filters.region];
      }
      if (regionCode) {
        params._regionCode = regionCode;
      }
    }

    // 키워드에서 지역 추출
    if (filters.keywords && !params._regionCode) {
      const region = this.extractRegionFromKeywords(filters.keywords);
      if (region) {
        params._regionCode = region;
      }
    }

    // 날짜 범위 (기간 필터)
    if (filters.dateRange) {
      if (filters.dateRange.start) {
        params.startDt = filters.dateRange.start.replace(/-/g, '');
      }
      if (filters.dateRange.end) {
        params.endDt = filters.dateRange.end.replace(/-/g, '');
      }
    }

    // 주기 필터
    if (filters.custom?.cycle) {
      params._cycle = filters.custom.cycle;
    } else if (filters.keywords) {
      const cycle = this.inferCycleFromKeywords(filters.keywords);
      if (cycle) {
        params._cycle = cycle;
      }
    }

    return params;
  }

  /**
   * 키워드에서 통계표 추론
   */
  private static inferTableFromKeywords(keywords: string[]): { category: string; suggestion: string } | null {
    const text = keywords.join(' ').toLowerCase();

    // 카테고리 매칭
    for (const [category, aliases] of Object.entries(this.STATISTICS_CATEGORIES)) {
      for (const alias of aliases) {
        if (text.includes(alias.toLowerCase())) {
          return {
            category,
            suggestion: `${category} 관련 통계를 조회합니다. 정확한 TBL_ID는 통계목록 조회(SttsApiTbl.do)에서 확인하세요.`,
          };
        }
      }
    }

    // 일반적인 부동산 키워드
    if (text.includes('부동산') || text.includes('주택') || text.includes('매매') || text.includes('전세')) {
      return {
        category: '부동산 일반',
        suggestion: '부동산 관련 통계를 조회합니다. TBL_ID 없이는 통계목록부터 조회해야 합니다.',
      };
    }

    // 가격 관련
    if (text.includes('가격') || text.includes('시세') || text.includes('지수')) {
      return {
        category: '가격지수',
        suggestion: '가격 관련 통계를 조회합니다.',
      };
    }

    return null;
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
   * 키워드에서 주기 추론
   */
  private static inferCycleFromKeywords(keywords: string[]): string | null {
    const text = keywords.join(' ');

    for (const [keyword, code] of Object.entries(this.CYCLE_KEYWORDS)) {
      if (text.includes(keyword)) {
        return code;
      }
    }

    return null;
  }

  /**
   * 누락된 파라미터 추론
   */
  static inferMissingParams(
    params: Record<string, unknown>,
    context?: { keywords?: string[]; query?: string }
  ): Record<string, unknown> {
    const inferred: Record<string, unknown> = { ...params };

    // TBL_ID가 없으면 통계목록 조회가 필요함을 표시
    if (!inferred.TBL_ID) {
      inferred._needsTableLookup = true;
      const inferredTblObj = (inferred._inferred as Record<string, unknown>) || {};
      inferredTblObj.TBL_ID = '통계표 ID가 필요합니다. 먼저 통계목록(SttsApiTbl.do)을 조회하세요.';
      inferred._inferred = inferredTblObj;

      // 키워드에서 힌트 제공
      if (context?.keywords) {
        const tableHint = this.inferTableFromKeywords(context.keywords);
        if (tableHint) {
          inferred._tableHint = tableHint;
        }
      }
    }

    // ITM_ID가 없고 TBL_ID가 있으면 세부항목 조회 필요
    if (inferred.TBL_ID && !inferred.ITM_ID) {
      inferred._needsItemLookup = true;
      const inferredObj = (inferred._inferred as Record<string, unknown>) || {};
      inferredObj.ITM_ID = '항목 ID가 필요합니다. 세부항목(SttsApiTblItm.do)을 조회하세요.';
      inferred._inferred = inferredObj;
    }

    return inferred;
  }

  /**
   * 지역명을 코드로 변환
   */
  static getRegionCode(regionName: string): string | null {
    return this.REGION_CODES[regionName] || null;
  }

  /**
   * 지역코드를 지역명으로 변환
   */
  static getRegionName(code: string): string | null {
    for (const [name, c] of Object.entries(this.REGION_CODES)) {
      if (c === code) return name;
    }
    return null;
  }

  /**
   * 에러 응답 확인
   */
  private static isErrorResponse(data: unknown): data is RoneErrorResponse {
    const obj = data as Record<string, unknown> | null;
    return typeof obj?.error_code === 'string' && obj.error_code.startsWith('ERROR');
  }

  /**
   * 정보성 응답 확인 (INFO-200: 데이터 없음)
   */
  private static isInfoResponse(data: unknown): boolean {
    const obj = data as Record<string, unknown> | null;
    return obj?.error_code === 'INFO-200';
  }

  /**
   * 에러 메시지 생성
   */
  private static getErrorMessage(errorCode: string): string {
    return this.ERROR_CODES[errorCode] || `알 수 없는 오류: ${errorCode}`;
  }

  /**
   * 통계목록 조회 응답 정규화 (SttsApiTbl.do)
   */
  static normalizeTableListResponse(
    data: unknown
  ): RoneNormalizedResponse<RoneTableListItem> {
    // 에러 응답 처리
    if (this.isErrorResponse(data)) {
      return {
        success: false,
        totalCount: 0,
        page: 1,
        pageSize: 0,
        data: [],
        error: {
          code: data.error_code,
          message: this.getErrorMessage(data.error_code),
        },
        _raw: data,
      };
    }

    // 데이터 없음 (INFO-200)
    if (this.isInfoResponse(data)) {
      return {
        success: true,
        totalCount: 0,
        page: 1,
        pageSize: 0,
        data: [],
        _raw: data,
      };
    }

    // baseConnector에서 이미 정규화된 배열 형태인 경우
    if (Array.isArray(data)) {
      return {
        success: true,
        totalCount: data.length,
        page: 1,
        pageSize: data.length,
        data: data.map((item) => this.normalizeTableListItem(item)),
        _raw: data,
      };
    }

    // 응답 구조 파싱
    // Actual API returns: {"SttsApiTbl":[{"head":[...]},{"row":[...]}]}
    const obj = data as Record<string, unknown>;
    let items: unknown[] = [];
    if (obj?.SttsApiTbl && Array.isArray(obj.SttsApiTbl)) {
      // Find the row object in the array
      const rowObj = (obj.SttsApiTbl as Array<Record<string, unknown>>).find((item) => item.row);
      if (rowObj && rowObj.row) {
        items = Array.isArray(rowObj.row) ? rowObj.row : [rowObj.row];
      }
    } else if (obj?.list) {
      // Fallback to documented structure
      items = Array.isArray(obj.list) ? obj.list : [obj.list];
    }

    return {
      success: true,
      totalCount: items.length,
      page: 1,
      pageSize: items.length,
      data: items.map((item) => this.normalizeTableListItem(item)),
      _raw: data,
    };
  }

  /**
   * 통계목록 항목 정규화
   *
   * Note: The actual API uses different field names than documented:
   * - STATBL_ID instead of TBL_ID
   * - STATBL_NM instead of TBL_NM
   * - DTACYCLE_CD/DTACYCLE_NM instead of CYCLE/CYCLE_NM
   * - TOP_ORG_NM instead of ORG_NM
   * - DATA_START_YY/DATA_END_YY instead of FRM_PRD/TO_PRD
   */
  private static normalizeTableListItem(item: unknown): RoneTableListItem {
    const raw = item as Record<string, unknown>;
    const cycle = (raw.CYCLE as string) || (raw.DTACYCLE_CD as string) || '';
    // Support both documented field names and actual API field names
    return {
      TBL_ID: (raw.TBL_ID as string) || (raw.STATBL_ID as string) || '',
      TBL_NM: (raw.TBL_NM as string) || (raw.STATBL_NM as string) || '',
      ORG_ID: (raw.ORG_ID as string) || (raw.STAT_ID as string) || '',
      ORG_NM: (raw.ORG_NM as string) || (raw.TOP_ORG_NM as string) || '',
      CLS_ID: (raw.CLS_ID as string) || '',
      CLS_NM: (raw.CLS_NM as string) || '',
      LST_DT: (raw.LST_DT as string) || '',
      CYCLE: cycle,
      CYCLE_NM: (raw.CYCLE_NM as string) || (raw.DTACYCLE_NM as string) || this.CYCLE_CODES[cycle] || '',
      KEY_YN: (raw.KEY_YN as string) || (raw.OPEN_STATE === 'Y' ? 'Y' : 'N'),
      AREA_YN: (raw.AREA_YN as string) || 'N',
      FRM_PRD: (raw.FRM_PRD as string) || (raw.DATA_START_YY as string) || '',
      TO_PRD: (raw.TO_PRD as string) || (raw.DATA_END_YY as string) || '',
    };
  }

  /**
   * 통계 세부항목 조회 응답 정규화 (SttsApiTblItm.do)
   */
  static normalizeTableItemsResponse(
    data: unknown
  ): RoneNormalizedResponse<RoneTableItemsItem> {
    // 에러 응답 처리
    if (this.isErrorResponse(data)) {
      return {
        success: false,
        totalCount: 0,
        page: 1,
        pageSize: 0,
        data: [],
        error: {
          code: data.error_code,
          message: this.getErrorMessage(data.error_code),
        },
        _raw: data,
      };
    }

    // 데이터 없음 (INFO-200)
    if (this.isInfoResponse(data)) {
      return {
        success: true,
        totalCount: 0,
        page: 1,
        pageSize: 0,
        data: [],
        _raw: data,
      };
    }

    // baseConnector에서 이미 정규화된 배열 형태인 경우
    if (Array.isArray(data)) {
      return {
        success: true,
        totalCount: data.length,
        page: 1,
        pageSize: data.length,
        data: data.map((item) => this.normalizeTableItemsItem(item)),
        _raw: data,
      };
    }

    // 응답 구조 파싱
    const obj = data as Record<string, unknown>;
    const tblItm = obj?.SttsApiTblItm as Record<string, unknown> | undefined;
    const list = tblItm?.list || obj?.list || [];
    const items: unknown[] = Array.isArray(list) ? list : [list];

    return {
      success: true,
      totalCount: items.length,
      page: 1,
      pageSize: items.length,
      data: items.map((item) => this.normalizeTableItemsItem(item)),
      _raw: data,
    };
  }

  /**
   * 통계 세부항목 정규화
   */
  private static normalizeTableItemsItem(item: unknown): RoneTableItemsItem {
    const raw = item as Record<string, unknown>;
    return {
      TBL_ID: (raw.TBL_ID as string) || '',
      ITM_ID: (raw.ITM_ID as string) || '',
      ITM_NM: (raw.ITM_NM as string) || '',
      C1: raw.C1 as string | undefined,
      C1_NM: raw.C1_NM as string | undefined,
      C2: raw.C2 as string | undefined,
      C2_NM: raw.C2_NM as string | undefined,
      C3: raw.C3 as string | undefined,
      C3_NM: raw.C3_NM as string | undefined,
      C4: raw.C4 as string | undefined,
      C4_NM: raw.C4_NM as string | undefined,
      UNIT: raw.UNIT as string | undefined,
    };
  }

  /**
   * 통계 데이터 조회 응답 정규화 (SttsApiTblData.do)
   */
  static normalizeTableDataResponse(
    data: unknown
  ): RoneNormalizedResponse<RoneTableDataItem> {
    // 에러 응답 처리
    if (this.isErrorResponse(data)) {
      return {
        success: false,
        totalCount: 0,
        page: 1,
        pageSize: 0,
        data: [],
        error: {
          code: data.error_code,
          message: this.getErrorMessage(data.error_code),
        },
        _raw: data,
      };
    }

    // 데이터 없음 (INFO-200)
    if (this.isInfoResponse(data)) {
      return {
        success: true,
        totalCount: 0,
        page: 1,
        pageSize: 0,
        data: [],
        _raw: data,
      };
    }

    // baseConnector에서 이미 정규화된 배열 형태인 경우
    if (Array.isArray(data)) {
      return {
        success: true,
        totalCount: data.length,
        page: 1,
        pageSize: data.length,
        data: data.map((item) => this.normalizeTableDataItem(item)),
        _raw: data,
      };
    }

    // 응답 구조 파싱
    // Actual API returns: {"SttsApiTblData":[{"head":[...]},{"row":[...]}]}
    const obj = data as Record<string, unknown>;
    let items: unknown[] = [];
    if (obj?.SttsApiTblData && Array.isArray(obj.SttsApiTblData)) {
      // Find the row object in the array
      const rowObj = (obj.SttsApiTblData as Array<Record<string, unknown>>).find((item) => item.row);
      if (rowObj && rowObj.row) {
        items = Array.isArray(rowObj.row) ? rowObj.row : [rowObj.row];
      }
    } else if (obj?.list) {
      // Fallback to documented structure
      items = Array.isArray(obj.list) ? obj.list : [obj.list];
    }

    return {
      success: true,
      totalCount: items.length,
      page: 1,
      pageSize: items.length,
      data: items.map((item) => this.normalizeTableDataItem(item)),
      _raw: data,
    };
  }

  /**
   * 통계 데이터 항목 정규화
   *
   * Note: The actual API uses different field names than documented:
   * - STATBL_ID instead of TBL_ID
   * - DTA_VAL instead of DTA
   * - WRTTIME_IDTFR_ID, WRTTIME_DESC instead of DT, DT_NM
   * - UI_NM instead of UNIT
   * - CLS_ID/CLS_NM, GRP_ID/GRP_NM instead of C1/C1_NM, etc.
   */
  private static normalizeTableDataItem(item: unknown): RoneTableDataItem {
    const raw = item as Record<string, unknown>;
    return {
      TBL_ID: (raw.TBL_ID as string) || (raw.STATBL_ID as string) || '',
      ITM_ID: (raw.ITM_ID as string) || '',
      ITM_NM: (raw.ITM_NM as string) || '',
      DT: (raw.DT as string) || (raw.WRTTIME_IDTFR_ID as string) || '',
      DT_NM: (raw.DT_NM as string) || (raw.WRTTIME_DESC as string) || '',
      C1: (raw.C1 as string) || (raw.GRP_ID as string) || (raw.CLS_ID as string | undefined),
      C1_NM: (raw.C1_NM as string) || (raw.GRP_NM as string) || (raw.CLS_NM as string | undefined),
      C2: (raw.C2 as string) || (raw.CLS_ID as string | undefined),
      C2_NM: (raw.C2_NM as string) || (raw.CLS_NM as string | undefined),
      C3: raw.C3 as string | undefined,
      C3_NM: raw.C3_NM as string | undefined,
      C4: raw.C4 as string | undefined,
      C4_NM: raw.C4_NM as string | undefined,
      UNIT: (raw.UNIT as string) || (raw.UI_NM as string | undefined),
      DTA: (raw.DTA as string) || (raw.DTA_VAL as string | undefined),
    };
  }

  /**
   * 파라미터 검증 - 통계목록 조회
   */
  static validateTableListParams(params: Record<string, unknown>): {
    valid: boolean;
    errors?: string[];
  } {
    const errors: string[] = [];

    // Type은 defaultParams로 처리되므로 선택적
    if (params.Type && !['json', 'xml'].includes(params.Type as string)) {
      errors.push('Type은 json 또는 xml이어야 합니다');
    }

    // pIndex 검증 (선택적, 기본값 1)
    if (params.pIndex && (isNaN(Number(params.pIndex)) || Number(params.pIndex) < 1)) {
      errors.push('pIndex는 1 이상의 숫자여야 합니다');
    }

    // pSize 검증 (선택적, 기본값 100)
    if (params.pSize && (isNaN(Number(params.pSize)) || Number(params.pSize) < 1)) {
      errors.push('pSize는 1 이상의 숫자여야 합니다');
    }

    return {
      valid: errors.length === 0,
      errors: errors.length > 0 ? errors : undefined,
    };
  }

  /**
   * 파라미터 검증 - 통계 세부항목 조회
   */
  static validateTableItemsParams(params: Record<string, unknown>): {
    valid: boolean;
    errors?: string[];
  } {
    const errors: string[] = [];

    // TBL_ID 필수
    if (!params.TBL_ID) {
      errors.push('TBL_ID는 필수 파라미터입니다');
    }

    // Type은 defaultParams로 처리되므로 선택적
    if (params.Type && !['json', 'xml'].includes(params.Type as string)) {
      errors.push('Type은 json 또는 xml이어야 합니다');
    }

    // pIndex 검증
    if (params.pIndex && (isNaN(Number(params.pIndex)) || Number(params.pIndex) < 1)) {
      errors.push('pIndex는 1 이상의 숫자여야 합니다');
    }

    // pSize 검증
    if (params.pSize && (isNaN(Number(params.pSize)) || Number(params.pSize) < 1)) {
      errors.push('pSize는 1 이상의 숫자여야 합니다');
    }

    return {
      valid: errors.length === 0,
      errors: errors.length > 0 ? errors : undefined,
    };
  }

  /**
   * 파라미터 검증 - 통계 데이터 조회
   */
  static validateTableDataParams(params: Record<string, unknown>): {
    valid: boolean;
    errors?: string[];
  } {
    const errors: string[] = [];

    // TBL_ID 필수
    if (!params.TBL_ID) {
      errors.push('TBL_ID는 필수 파라미터입니다');
    }

    // ITM_ID 필수
    if (!params.ITM_ID) {
      errors.push('ITM_ID는 필수 파라미터입니다');
    }

    // Type은 defaultParams로 처리되므로 선택적
    if (params.Type && !['json', 'xml'].includes(params.Type as string)) {
      errors.push('Type은 json 또는 xml이어야 합니다');
    }

    // pIndex 검증
    if (params.pIndex && (isNaN(Number(params.pIndex)) || Number(params.pIndex) < 1)) {
      errors.push('pIndex는 1 이상의 숫자여야 합니다');
    }

    // pSize 검증
    if (params.pSize && (isNaN(Number(params.pSize)) || Number(params.pSize) < 1)) {
      errors.push('pSize는 1 이상의 숫자여야 합니다');
    }

    return {
      valid: errors.length === 0,
      errors: errors.length > 0 ? errors : undefined,
    };
  }

  /**
   * 주요 통계만 필터링
   */
  static filterKeyStatistics(
    data: RoneTableListItem[]
  ): RoneTableListItem[] {
    return data.filter((item) => item.KEY_YN === 'Y');
  }

  /**
   * 주기별 필터링
   */
  static filterByCycle(
    data: RoneTableListItem[],
    cycle: 'YY' | 'HY' | 'QY' | 'MM' | 'WK'
  ): RoneTableListItem[] {
    return data.filter((item) => item.CYCLE === cycle);
  }

  /**
   * 분류별 필터링
   */
  static filterByClass(
    data: RoneTableListItem[],
    classId: string
  ): RoneTableListItem[] {
    return data.filter((item) => item.CLS_ID === classId);
  }

  /**
   * 통계표명으로 검색
   */
  static searchByTableName(
    data: RoneTableListItem[],
    keyword: string
  ): RoneTableListItem[] {
    const lowerKeyword = keyword.toLowerCase();
    return data.filter((item) =>
      item.TBL_NM.toLowerCase().includes(lowerKeyword)
    );
  }

  /**
   * 통계 요약 생성
   */
  static generateStatisticsSummary(data: RoneTableListItem[]): {
    totalCount: number;
    byCycle: Record<string, number>;
    byOrganization: Record<string, number>;
    byClass: Record<string, number>;
    keyStatisticsCount: number;
    areaStatisticsCount: number;
  } {
    const byCycle: Record<string, number> = {};
    const byOrganization: Record<string, number> = {};
    const byClass: Record<string, number> = {};
    let keyStatisticsCount = 0;
    let areaStatisticsCount = 0;

    data.forEach((item) => {
      // 주기별 카운트
      byCycle[item.CYCLE] = (byCycle[item.CYCLE] || 0) + 1;

      // 기관별 카운트
      byOrganization[item.ORG_NM] = (byOrganization[item.ORG_NM] || 0) + 1;

      // 분류별 카운트
      byClass[item.CLS_NM] = (byClass[item.CLS_NM] || 0) + 1;

      // 주요 통계 카운트
      if (item.KEY_YN === 'Y') keyStatisticsCount++;

      // 지역별 통계 카운트
      if (item.AREA_YN === 'Y') areaStatisticsCount++;
    });

    return {
      totalCount: data.length,
      byCycle,
      byOrganization,
      byClass,
      keyStatisticsCount,
      areaStatisticsCount,
    };
  }
}
