/**
 * Local Finance API Adapter
 * 행정안전부 지방재정365 Open API 응답 정규화 및 유틸리티
 *
 * API 정보:
 * - 서비스명: 지방재정365 Open API
 * - 제공기관: 행정안전부
 * - Base URL: https://www.lofin365.go.kr/lf/hub
 * - 인증방식: API Key (Query Parameter: Key)
 * - 응답형식: JSON, XML
 *
 * 주요 데이터셋 (엔드포인트):
 * - /QWGJK: 세부사업별 세출현황
 * - /RLPZZ: 회계별 세입현황
 * - /QWGJI: 회계별 세출현황
 * - /FNNCI: 재정자립도
 * - /LDEBT: 지방채 현황
 * - /LFUND: 기금 현황
 */

import type { QueryFilters } from '@labgod/core-types';

// ==========================================
// 타입 정의
// ==========================================

export interface LocalFinanceExpItem {
  fyr: string;              // 회계연도
  wa_laf_cd: string;        // 광역자치단체코드
  wa_laf_hg_nm: string;     // 광역자치단체명
  laf_cd: string;           // 자치단체코드
  laf_hg_nm: string;        // 자치단체명
  acnt_dv_cd: string;       // 회계구분코드
  acnt_dv_nm: string;       // 회계구분명
  dept_cd: string;          // 부서코드
  dbiz_cd: string;          // 세부사업코드
  dbiz_nm: string;          // 세부사업명
  exe_ymd: string;          // 집행일자
  bdg_cash_amt: number;     // 예산현액
  bdg_ntep: number;         // 국비
  capep: number;            // 시도비
  sggep: number;            // 시군구비
  etc_amt: number;          // 기타
  ep_amt: number;           // 집행액
  cpl_amt: number;          // 이월액
  fld_cd: string;           // 분야코드
  fld_nm: string;           // 분야명
  ane_part_cd: string;      // 부문코드
  part_nm: string;          // 부문명
  padm_laf_cd: string;      // 행정동코드
}

export interface LocalFinanceRatioItem {
  FSCL_YY: string;          // 회계연도
  OFFC_NM: string;          // 자치단체명
  OFFC_CD: string;          // 자치단체코드
  FNNC_IDP_RT: number;      // 재정자립도 (%)
  FNNC_ATMM_RT: number;     // 재정자주도 (%)
  EXPEN_RT?: number;        // 재정력지수
  DEBT_RT?: number;         // 채무비율 (%)
  INTGR_FNNC_RT?: number;   // 통합재정수지비율 (%)
}

export interface LocalFinanceDebtItem {
  FSCL_YY: string;          // 회계연도
  OFFC_NM: string;          // 자치단체명
  OFFC_CD: string;          // 자치단체코드
  DEBT_KIND: string;        // 채무종류
  DEBT_BAL: number;         // 채무잔액 (천원)
  NEW_DEBT?: number;        // 신규채무 (천원)
  REPAY_AMT?: number;       // 상환액 (천원)
}

export interface LocalFinanceBudgetItem {
  FSCL_YY: string;          // 회계연도
  OFFC_NM: string;          // 자치단체명
  OFFC_CD: string;          // 자치단체코드
  ACCT_NM: string;          // 회계명
  SFRND_NM?: string;        // 세부사업명
  BUDGET_AMT: number;       // 예산액 (천원)
  EXCUT_AMT?: number;       // 집행액 (천원)
  REMNDR_AMT?: number;      // 잔액 (천원)
  REALM_NM?: string;        // 분야명
  SECT_NM?: string;         // 부문명
}

export interface LocalFinanceNormalizedResponse<T> {
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

export type LocalFinanceEndpointType =
  | 'expByProject'       // 세부사업별 세출현황
  | 'revByAccount'       // 회계별 세입현황
  | 'expByAccount'       // 회계별 세출현황
  | 'financeIndependence' // 재정자립도
  | 'localDebt'          // 지방채 현황
  | 'fund';              // 기금 현황

// ==========================================
// Local Finance Adapter 클래스
// ==========================================

export class LocalFinanceAdapter {
  // 시도 코드 매핑
  static readonly SIDO_CODES: Record<string, string> = {
    '서울': '1100000',
    '부산': '2100000',
    '대구': '2200000',
    '인천': '2300000',
    '광주': '2400000',
    '대전': '2500000',
    '울산': '2600000',
    '세종': '2900000',
    '경기': '4100000',
    '강원': '4200000',
    '충북': '4300000',
    '충남': '4400000',
    '전북': '4500000',
    '전남': '4600000',
    '경북': '4700000',
    '경남': '4800000',
    '제주': '4900000',
  };

  // 엔드포인트 경로 매핑
  static readonly ENDPOINTS: Record<LocalFinanceEndpointType, string> = {
    expByProject: '/QWGJK',
    revByAccount: '/RLPZZ',
    expByAccount: '/QWGJI',
    financeIndependence: '/FNNCI',
    localDebt: '/LDEBT',
    fund: '/LFUND',
  };

  // 엔드포인트별 한글 설명
  static readonly ENDPOINT_NAMES: Record<LocalFinanceEndpointType, string> = {
    expByProject: '세부사업별 세출현황',
    revByAccount: '회계별 세입현황',
    expByAccount: '회계별 세출현황',
    financeIndependence: '재정자립도',
    localDebt: '지방채 현황',
    fund: '기금 현황',
  };

  /**
   * QueryFilters를 지방재정365 API 파라미터로 변환
   */
  static adaptFilters(filters: QueryFilters): Record<string, unknown> {
    const params: Record<string, unknown> = {
      Type: 'json',
      pIndex: 1,
      pSize: 100,
    };

    // 연도 필터 (필수)
    if (filters.dateRange?.start) {
      params.fyr = filters.dateRange.start.substring(0, 4);
    } else if (filters.custom?.year) {
      params.fyr = filters.custom.year;
    } else {
      params.fyr = String(new Date().getFullYear() - 1);
    }

    // 지역 필터
    if (filters.region) {
      let sidoCode: string | undefined;
      if (typeof filters.region === 'object' && filters.region.sido) {
        sidoCode = this.SIDO_CODES[filters.region.sido];
      } else if (typeof filters.region === 'string') {
        sidoCode = this.SIDO_CODES[filters.region];
      }
      if (sidoCode) {
        params.wa_laf_cd = sidoCode;
      }
    }

    // 키워드에서 지역 추출
    if (filters.keywords && !params.wa_laf_cd) {
      const sidoCode = this.extractSidoFromKeywords(filters.keywords);
      if (sidoCode) {
        params.wa_laf_cd = sidoCode;
      }
    }

    return params;
  }

  private static extractSidoFromKeywords(keywords: string[]): string | null {
    const text = keywords.join(' ');
    for (const [sido, code] of Object.entries(this.SIDO_CODES)) {
      if (text.includes(sido)) {
        return code;
      }
    }
    return null;
  }

  /**
   * 공통 응답 정규화 로직
   */
  static normalizeResponse<T>(
    data: unknown,
    normalizeItem: (item: unknown) => T
  ): LocalFinanceNormalizedResponse<T> {
    const dataObj = data as Record<string, unknown>;

    // 지방재정365 응답 구조 처리
    const datasetId = Object.keys(dataObj)[0];
    if (datasetId && Array.isArray(dataObj[datasetId])) {
      const dataset = dataObj[datasetId] as Array<Record<string, unknown>>;

      const headObj = dataset.find(item => item.head);
      const head = headObj?.head as Array<Record<string, unknown>> | undefined;

      if (head) {
        const resultInfo = head.find(h => h.RESULT) as { RESULT?: { CODE: string; MESSAGE: string } } | undefined;
        const countInfo = head.find(h => h.list_total_count !== undefined) as { list_total_count?: number } | undefined;

        if (resultInfo?.RESULT && !resultInfo.RESULT.CODE.startsWith('INFO')) {
          return {
            success: false,
            totalCount: 0,
            page: 1,
            pageSize: 0,
            data: [],
            error: {
              code: resultInfo.RESULT.CODE,
              message: resultInfo.RESULT.MESSAGE,
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

    // 배열 형태인 경우
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

    return {
      success: true,
      totalCount: 0,
      page: 1,
      pageSize: 0,
      data: [],
      _raw: data,
    };
  }

  /**
   * 세출현황 항목 정규화
   */
  static normalizeExpItem(item: unknown): LocalFinanceExpItem {
    const obj = item as Record<string, unknown>;
    return {
      fyr: String(obj.fyr || ''),
      wa_laf_cd: String(obj.wa_laf_cd || ''),
      wa_laf_hg_nm: String(obj.wa_laf_hg_nm || ''),
      laf_cd: String(obj.laf_cd || ''),
      laf_hg_nm: String(obj.laf_hg_nm || ''),
      acnt_dv_cd: String(obj.acnt_dv_cd || ''),
      acnt_dv_nm: String(obj.acnt_dv_nm || ''),
      dept_cd: String(obj.dept_cd || ''),
      dbiz_cd: String(obj.dbiz_cd || ''),
      dbiz_nm: String(obj.dbiz_nm || ''),
      exe_ymd: String(obj.exe_ymd || ''),
      bdg_cash_amt: Number(obj.bdg_cash_amt || 0),
      bdg_ntep: Number(obj.bdg_ntep || 0),
      capep: Number(obj.capep || 0),
      sggep: Number(obj.sggep || 0),
      etc_amt: Number(obj.etc_amt || 0),
      ep_amt: Number(obj.ep_amt || 0),
      cpl_amt: Number(obj.cpl_amt || 0),
      fld_cd: String(obj.fld_cd || ''),
      fld_nm: String(obj.fld_nm || ''),
      ane_part_cd: String(obj.ane_part_cd || ''),
      part_nm: String(obj.part_nm || ''),
      padm_laf_cd: String(obj.padm_laf_cd || ''),
    };
  }

  /**
   * 재정지표 항목 정규화
   */
  static normalizeRatioItem(item: unknown): LocalFinanceRatioItem {
    const obj = item as Record<string, unknown>;
    return {
      FSCL_YY: String(obj.FSCL_YY || obj.fscl_yy || ''),
      OFFC_NM: String(obj.OFFC_NM || obj.offc_nm || ''),
      OFFC_CD: String(obj.OFFC_CD || obj.offc_cd || ''),
      FNNC_IDP_RT: Number(obj.FNNC_IDP_RT || obj.fnnc_idp_rt || 0),
      FNNC_ATMM_RT: Number(obj.FNNC_ATMM_RT || obj.fnnc_atmm_rt || 0),
      EXPEN_RT: obj.EXPEN_RT ? Number(obj.EXPEN_RT) : undefined,
      DEBT_RT: obj.DEBT_RT ? Number(obj.DEBT_RT) : undefined,
      INTGR_FNNC_RT: obj.INTGR_FNNC_RT ? Number(obj.INTGR_FNNC_RT) : undefined,
    };
  }

  /**
   * 채무 항목 정규화
   */
  static normalizeDebtItem(item: unknown): LocalFinanceDebtItem {
    const obj = item as Record<string, unknown>;
    return {
      FSCL_YY: String(obj.FSCL_YY || obj.fscl_yy || ''),
      OFFC_NM: String(obj.OFFC_NM || obj.offc_nm || ''),
      OFFC_CD: String(obj.OFFC_CD || obj.offc_cd || ''),
      DEBT_KIND: String(obj.DEBT_KIND || obj.debt_kind || ''),
      DEBT_BAL: Number(obj.DEBT_BAL || obj.debt_bal || 0),
      NEW_DEBT: obj.NEW_DEBT ? Number(obj.NEW_DEBT) : undefined,
      REPAY_AMT: obj.REPAY_AMT ? Number(obj.REPAY_AMT) : undefined,
    };
  }

  static normalizeExpResponse(data: unknown): LocalFinanceNormalizedResponse<LocalFinanceExpItem> {
    return this.normalizeResponse(data, this.normalizeExpItem);
  }

  static normalizeRatioResponse(data: unknown): LocalFinanceNormalizedResponse<LocalFinanceRatioItem> {
    return this.normalizeResponse(data, this.normalizeRatioItem);
  }

  static normalizeDebtResponse(data: unknown): LocalFinanceNormalizedResponse<LocalFinanceDebtItem> {
    return this.normalizeResponse(data, this.normalizeDebtItem);
  }

  /**
   * 예산 항목 정규화
   */
  private static normalizeBudgetItem(item: unknown): LocalFinanceBudgetItem {
    const obj = item as Record<string, unknown>;
    return {
      FSCL_YY: String(obj.FSCL_YY || obj.fscl_yy || obj.fyr || ''),
      OFFC_NM: String(obj.OFFC_NM || obj.offc_nm || obj.laf_hg_nm || ''),
      OFFC_CD: String(obj.OFFC_CD || obj.offc_cd || obj.laf_cd || ''),
      ACCT_NM: String(obj.ACCT_NM || obj.acct_nm || obj.acnt_dv_nm || ''),
      SFRND_NM: obj.SFRND_NM || obj.dbiz_nm ? String(obj.SFRND_NM || obj.dbiz_nm) : undefined,
      BUDGET_AMT: Number(obj.BUDGET_AMT || obj.budget_amt || obj.bdg_cash_amt || 0),
      EXCUT_AMT: obj.EXCUT_AMT || obj.ep_amt ? Number(obj.EXCUT_AMT || obj.ep_amt) : undefined,
      REMNDR_AMT: obj.REMNDR_AMT ? Number(obj.REMNDR_AMT) : undefined,
      REALM_NM: obj.REALM_NM || obj.fld_nm ? String(obj.REALM_NM || obj.fld_nm) : undefined,
      SECT_NM: obj.SECT_NM || obj.part_nm ? String(obj.SECT_NM || obj.part_nm) : undefined,
    };
  }

  /**
   * 예산 응답 정규화
   */
  static normalizeBudgetResponse(data: unknown): LocalFinanceNormalizedResponse<LocalFinanceBudgetItem> {
    return this.normalizeResponse(data, this.normalizeBudgetItem);
  }

  /**
   * 예산 데이터 요약 생성
   */
  static generateBudgetSummary(data: LocalFinanceBudgetItem[]): {
    totalRecords: number;
    fiscalYear: string;
    regions: string[];
    totalBudget: number;
    totalBudgetFormatted: string;
    byAccount: Record<string, number>;
  } {
    if (data.length === 0) {
      return {
        totalRecords: 0,
        fiscalYear: '',
        regions: [],
        totalBudget: 0,
        totalBudgetFormatted: '0원',
        byAccount: {},
      };
    }

    const totalBudget = data.reduce((sum, item) => sum + item.BUDGET_AMT, 0);
    const byAccount: Record<string, number> = {};

    data.forEach(item => {
      if (item.ACCT_NM) {
        byAccount[item.ACCT_NM] = (byAccount[item.ACCT_NM] || 0) + item.BUDGET_AMT;
      }
    });

    return {
      totalRecords: data.length,
      fiscalYear: data[0]?.FSCL_YY || '',
      regions: [...new Set(data.map(d => d.OFFC_NM))],
      totalBudget,
      totalBudgetFormatted: this.formatAmount(totalBudget),
      byAccount,
    };
  }

  /**
   * 파라미터 검증
   */
  static validateParams(params: Record<string, unknown>): {
    valid: boolean;
    errors?: string[];
  } {
    const errors: string[] = [];

    if (!params.fyr) {
      errors.push('fyr(회계연도)는 필수 파라미터입니다');
    }

    if (params.fyr) {
      const year = parseInt(String(params.fyr));
      if (isNaN(year) || year < 2000 || year > new Date().getFullYear()) {
        errors.push('fyr는 2000년부터 현재 연도 사이의 값이어야 합니다');
      }
    }

    return {
      valid: errors.length === 0,
      errors: errors.length > 0 ? errors : undefined,
    };
  }

  /**
   * 금액 포맷팅 (천원 → 억원)
   */
  static formatAmount(amountInThousand: number): string {
    const amountInHundredMillion = amountInThousand / 100000;
    if (amountInHundredMillion >= 10000) {
      return `${(amountInHundredMillion / 10000).toFixed(1)}조원`;
    }
    return `${amountInHundredMillion.toFixed(1)}억원`;
  }
}
