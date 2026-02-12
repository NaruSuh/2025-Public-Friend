/**
 * NABOSTATS API Adapter
 * 국회예산정책처 재정경제통계시스템 Open API 응답 정규화 및 유틸리티
 *
 * API 정보:
 * - 서비스명: NABOSTATS 재정경제통계시스템 Open API
 * - 제공기관: 국회예산정책처 (NABO)
 * - Base URL: https://www.nabostats.go.kr/openapi
 * - 인증방식: API Key (Query Parameter: Key)
 *
 * 주요 엔드포인트:
 * - /Sttsapitbl.do: 서비스 통계 목록
 * - /Sttsapitblitm.do: 통계 세부항목 조회
 * - /Sttsapitbldata.do: 통계 데이터 조회
 * - /DicApiList.do: 통계 용어사전 조회
 */

import type { QueryFilters } from '@labgod/core-types';

// ==========================================
// 타입 정의
// ==========================================

export interface NaboTableItem {
  CATE_FULLNM: string;      // 분류체계
  STATBL_ID: string;        // 통계표ID
  STATBL_NM: string;        // 통계표명
  DTACYCLE_NM: string;      // 통계주기명
  TOP_ORG_NM: string;       // 제공기관
  ORG_NM: string | null;    // 부서명
  USR_NM: string;           // 담당자명
  LOAD_DATE: string;        // 최종적재일자
  OPEN_DATE: string;        // 공개일자
  DATA_START_YY: string;    // 통계자료시작년도
  DATA_END_YY: string;      // 통계자료종료년도
  STATBL_CMMT: string;      // 통계표주석
  SRV_URL: string;          // 서비스URL
}

export interface NaboTableItemDetail {
  STATBL_ID: string;
  ITM_TAG: string;
  ITM_ID: number;
  PAR_ITM_ID: number;
  ITM_NM: string;
  ITM_FULLNM: string;
  UI_NM: string;
  ITM_CMMT_IDTFR: string | null;
  ITM_CMMT_CONT: string | null;
  V_ORDER: number;
}

export interface NaboDataItem {
  STATBL_ID: string;
  DTACYCLE_CD: string;
  WRTTIME_IDTFR_ID: string;
  GRP_ID: string | null;
  GRP_NM: string | null;
  CLS_ID: string | null;
  CLS_NM: string | null;
  ITM_ID: number;
  ITM_NM: string;
  UI_NM: string;
  DTA_VAL: number;
  DTA_SVAL: string | null;
}

export interface NaboDictionaryItem {
  DIC_SEQ: number;
  DIC_TITLE: string;
  DIC_CONTENT: string;
}

export interface NaboNormalizedResponse<T> {
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

export type NaboEndpointType = 'tableList' | 'tableItems' | 'tableData' | 'dictionary';

// ==========================================
// NABOSTATS Adapter 클래스
// ==========================================

export class NaboStatsAdapter {
  static readonly DATA_CYCLE_CODES: Record<string, string> = {
    '년': 'YY',
    '연': 'YY',
    '분기': 'QQ',
    '월': 'MM',
    '일': 'DD',
  };

  static readonly ENDPOINTS: Record<NaboEndpointType, string> = {
    tableList: '/Sttsapitbl.do',
    tableItems: '/Sttsapitblitm.do',
    tableData: '/Sttsapitbldata.do',
    dictionary: '/DicApiList.do',
  };

  static readonly ENDPOINT_NAMES: Record<NaboEndpointType, string> = {
    tableList: '서비스 통계 목록',
    tableItems: '통계 세부항목',
    tableData: '통계 데이터',
    dictionary: '통계 용어사전',
  };

  private static readonly ERROR_CODES: Record<string, string> = {
    'INFO-000': '정상 처리되었습니다',
    'INFO-200': '해당하는 데이터가 없습니다',
    'INFO-300': '관리자에 의해 인증키 사용이 제한되었습니다',
    'ERROR-290': '인증키가 유효하지 않습니다',
    'ERROR-300': '필수 값이 누락되어 있습니다',
    'ERROR-336': '데이터요청은 한번에 최대 1,000건을 넘을 수 없습니다',
    'ERROR-337': '일별 트래픽 제한을 넘은 호출입니다',
  };

  static adaptFilters(filters: QueryFilters): Record<string, unknown> {
    const params: Record<string, unknown> = {
      Type: 'json',
      pIndex: 1,
      pSize: 100,
    };

    if (filters.custom?.tableId) {
      params.STATBL_ID = filters.custom.tableId;
    }

    if (filters.custom?.tableName) {
      params.STATBL_NM = filters.custom.tableName;
    }

    if (filters.custom?.dataCycle) {
      const cycleCode = this.DATA_CYCLE_CODES[filters.custom.dataCycle as string];
      if (cycleCode) {
        params.DTACYCLE_CD = cycleCode;
      }
    }

    if (filters.dateRange?.start) {
      params.WRTTIME_IDTFR_ID = filters.dateRange.start.substring(0, 4);
    } else if (filters.custom?.year) {
      params.WRTTIME_IDTFR_ID = filters.custom.year;
    }

    if (filters.keywords && filters.keywords.length > 0 && !params.STATBL_NM) {
      params.STATBL_NM = filters.keywords[0];
    }

    return params;
  }

  /**
   * 공통 응답 정규화 로직
   */
  private static normalizeResponse<T>(
    data: unknown,
    normalizeItem: (item: unknown) => T
  ): NaboNormalizedResponse<T> {
    const dataObj = data as Record<string, unknown>;

    // 에러 응답 확인
    if (dataObj.RESULT) {
      const result = dataObj.RESULT as { CODE: string; MESSAGE: string };
      if (!result.CODE.startsWith('INFO-0')) {
        return {
          success: false,
          totalCount: 0,
          page: 1,
          pageSize: 0,
          data: [],
          error: {
            code: result.CODE,
            message: result.MESSAGE || this.ERROR_CODES[result.CODE] || '알 수 없는 오류',
          },
          _raw: data,
        };
      }
    }

    // NABOSTATS 표준 응답 구조 처리
    const datasetKey = Object.keys(dataObj).find(k => k !== 'RESULT');
    if (datasetKey && Array.isArray(dataObj[datasetKey])) {
      const dataset = dataObj[datasetKey] as Array<Record<string, unknown>>;

      const headObj = dataset.find(item => item.head);
      const head = headObj?.head as Array<Record<string, unknown>> | undefined;

      if (head) {
        const resultInfo = head.find(h => h.RESULT) as { RESULT?: { CODE: string; MESSAGE: string } } | undefined;
        const countInfo = head.find(h => h.list_total_count !== undefined) as { list_total_count?: number } | undefined;

        if (resultInfo?.RESULT && !resultInfo.RESULT.CODE.startsWith('INFO-0')) {
          return {
            success: false,
            totalCount: 0,
            page: 1,
            pageSize: 0,
            data: [],
            error: {
              code: resultInfo.RESULT.CODE,
              message: resultInfo.RESULT.MESSAGE || this.ERROR_CODES[resultInfo.RESULT.CODE] || '알 수 없는 오류',
            },
            _raw: data,
          };
        }

        const rowObj = dataset.find(item => item.row);
        const rows = (rowObj?.row as unknown[]) || [];
        const totalCount = countInfo?.list_total_count || rows.length;

        return {
          success: true,
          totalCount,
          page: 1,
          pageSize: rows.length,
          data: rows.map(item => normalizeItem(item)),
          _raw: data,
        };
      }
    }

    return {
      success: true,
      totalCount: 0,
      page: 1,
      pageSize: 0,
      data: [],
      _raw: data,
    };
  }

  private static normalizeTableItem(item: unknown): NaboTableItem {
    const obj = item as Record<string, unknown>;
    return {
      CATE_FULLNM: String(obj.CATE_FULLNM || ''),
      STATBL_ID: String(obj.STATBL_ID || ''),
      STATBL_NM: String(obj.STATBL_NM || ''),
      DTACYCLE_NM: String(obj.DTACYCLE_NM || ''),
      TOP_ORG_NM: String(obj.TOP_ORG_NM || ''),
      ORG_NM: obj.ORG_NM ? String(obj.ORG_NM) : null,
      USR_NM: String(obj.USR_NM || ''),
      LOAD_DATE: String(obj.LOAD_DATE || ''),
      OPEN_DATE: String(obj.OPEN_DATE || ''),
      DATA_START_YY: String(obj.DATA_START_YY || ''),
      DATA_END_YY: String(obj.DATA_END_YY || ''),
      STATBL_CMMT: String(obj.STATBL_CMMT || ''),
      SRV_URL: String(obj.SRV_URL || ''),
    };
  }

  private static normalizeTableItemDetail(item: unknown): NaboTableItemDetail {
    const obj = item as Record<string, unknown>;
    return {
      STATBL_ID: String(obj.STATBL_ID || ''),
      ITM_TAG: String(obj.ITM_TAG || ''),
      ITM_ID: Number(obj.ITM_ID || 0),
      PAR_ITM_ID: Number(obj.PAR_ITM_ID || 0),
      ITM_NM: String(obj.ITM_NM || ''),
      ITM_FULLNM: String(obj.ITM_FULLNM || ''),
      UI_NM: String(obj.UI_NM || ''),
      ITM_CMMT_IDTFR: obj.ITM_CMMT_IDTFR ? String(obj.ITM_CMMT_IDTFR) : null,
      ITM_CMMT_CONT: obj.ITM_CMMT_CONT ? String(obj.ITM_CMMT_CONT) : null,
      V_ORDER: Number(obj.V_ORDER || 0),
    };
  }

  private static normalizeDataItem(item: unknown): NaboDataItem {
    const obj = item as Record<string, unknown>;
    return {
      STATBL_ID: String(obj.STATBL_ID || ''),
      DTACYCLE_CD: String(obj.DTACYCLE_CD || ''),
      WRTTIME_IDTFR_ID: String(obj.WRTTIME_IDTFR_ID || ''),
      GRP_ID: obj.GRP_ID ? String(obj.GRP_ID) : null,
      GRP_NM: obj.GRP_NM ? String(obj.GRP_NM) : null,
      CLS_ID: obj.CLS_ID ? String(obj.CLS_ID) : null,
      CLS_NM: obj.CLS_NM ? String(obj.CLS_NM) : null,
      ITM_ID: Number(obj.ITM_ID || 0),
      ITM_NM: String(obj.ITM_NM || ''),
      UI_NM: String(obj.UI_NM || ''),
      DTA_VAL: Number(obj.DTA_VAL || 0),
      DTA_SVAL: obj.DTA_SVAL ? String(obj.DTA_SVAL) : null,
    };
  }

  private static normalizeDictionaryItem(item: unknown): NaboDictionaryItem {
    const obj = item as Record<string, unknown>;
    return {
      DIC_SEQ: Number(obj.DIC_SEQ || 0),
      DIC_TITLE: String(obj.DIC_TITLE || ''),
      DIC_CONTENT: String(obj.DIC_CONTENT || ''),
    };
  }

  static normalizeTableListResponse(data: unknown): NaboNormalizedResponse<NaboTableItem> {
    return this.normalizeResponse(data, this.normalizeTableItem);
  }

  static normalizeTableItemsResponse(data: unknown): NaboNormalizedResponse<NaboTableItemDetail> {
    return this.normalizeResponse(data, this.normalizeTableItemDetail);
  }

  static normalizeTableDataResponse(data: unknown): NaboNormalizedResponse<NaboDataItem> {
    return this.normalizeResponse(data, this.normalizeDataItem);
  }

  static normalizeDictionaryResponse(data: unknown): NaboNormalizedResponse<NaboDictionaryItem> {
    return this.normalizeResponse(data, this.normalizeDictionaryItem);
  }

  static validateParams(
    endpoint: NaboEndpointType,
    params: Record<string, unknown>
  ): { valid: boolean; errors?: string[] } {
    const errors: string[] = [];

    switch (endpoint) {
      case 'tableItems':
        if (!params.STATBL_ID) {
          errors.push('STATBL_ID(통계표ID)는 필수 파라미터입니다');
        }
        break;
      case 'tableData':
        if (!params.STATBL_ID) {
          errors.push('STATBL_ID(통계표ID)는 필수 파라미터입니다');
        }
        if (!params.DTACYCLE_CD) {
          errors.push('DTACYCLE_CD(자료주기)는 필수 파라미터입니다');
        }
        break;
    }

    if (params.pSize && Number(params.pSize) > 1000) {
      errors.push('pSize는 최대 1000까지 가능합니다');
    }

    return {
      valid: errors.length === 0,
      errors: errors.length > 0 ? errors : undefined,
    };
  }
}
