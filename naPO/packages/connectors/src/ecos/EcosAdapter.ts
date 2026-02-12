/**
 * ECOS API Adapter
 * 한국은행 경제통계시스템 ECOS Open API 응답 정규화 및 유틸리티
 *
 * API 정보:
 * - 서비스명: 한국은행 경제통계시스템 ECOS API
 * - 제공기관: 한국은행
 * - Base URL: https://ecos.bok.or.kr/api
 * - 인증방식: API Key (Path Parameter)
 * - 응답형식: JSON, XML
 *
 * 주요 엔드포인트 (총 6개):
 * 1. /StatisticSearch - 통계 데이터 조회
 * 2. /StatisticTableList - 통계표 목록 조회
 * 3. /StatisticItemList - 통계 세부항목 목록
 * 4. /KeyStatisticList - 100대 통계지표
 * 5. /StatisticMeta - 통계메타DB
 * 6. /StatisticWord - 통계용어사전
 */

import type { QueryFilters, NormalizedResponse } from '@labgod/core-types';

// ==========================================
// 타입 정의
// ==========================================

export interface EcosStatItem {
  STAT_CODE: string;
  STAT_NAME: string;
  ITEM_CODE1: string;
  ITEM_NAME1: string;
  ITEM_CODE2?: string;
  ITEM_NAME2?: string;
  ITEM_CODE3?: string;
  ITEM_NAME3?: string;
  ITEM_CODE4?: string;
  ITEM_NAME4?: string;
  UNIT_NAME: string;
  TIME: string;
  DATA_VALUE: string;
}

export interface EcosStatTableItem {
  STAT_CODE: string;
  STAT_NAME: string;
  CYCLE: string;
  SRCH_YN: string;
  ORG_NAME?: string;
}

export interface EcosStatItemInfo {
  STAT_CODE: string;
  STAT_NAME: string;
  ITEM_CODE: string;
  ITEM_NAME: string;
  CYCLE: string;
  START_TIME: string;
  END_TIME: string;
  DATA_CNT: number;
}

export interface EcosKeyStatItem {
  CLASS_NAME: string;
  KEYSTAT_NAME: string;
  DATA_VALUE: string;
  UNIT_NAME: string;
  CYCLE: string;
  TIME: string;
}

export interface EcosMetaItem {
  LVL: string;
  P_STAT_CODE: string;
  STAT_CODE: string;
  STAT_NAME: string;
  CYCLE: string;
  ORG_NAME: string;
  SRCH_YN: string;
  CONTENTS?: string;
}

export interface EcosWordItem {
  WORD: string;
  CONTENT: string;
}

export type EcosEndpoint =
  | 'StatisticSearch'
  | 'StatisticTableList'
  | 'StatisticItemList'
  | 'KeyStatisticList'
  | 'StatisticMeta'
  | 'StatisticWord';

// ==========================================
// ECOS Adapter 클래스
// ==========================================

export class EcosAdapter {
  static readonly STAT_CODES: Record<string, { code: string; name: string; cycle: string }> = {
    '기준금리': { code: '722Y001', name: '한국은행 기준금리', cycle: 'D' },
    '콜금리': { code: '817Y002', name: '콜금리(익일물)', cycle: 'D' },
    '국고채': { code: '817Y002', name: '국고채(3년)', cycle: 'D' },
    'CD금리': { code: '817Y002', name: 'CD(91일)', cycle: 'D' },
    '환율': { code: '731Y001', name: '주요국 통화의 대원화 환율', cycle: 'D' },
    '원달러': { code: '731Y001', name: '원/달러 환율', cycle: 'D' },
    '원엔': { code: '731Y001', name: '원/100엔 환율', cycle: 'D' },
    '원유로': { code: '731Y001', name: '원/유로 환율', cycle: 'D' },
    'M1': { code: '101Y004', name: '협의통화(M1)', cycle: 'M' },
    'M2': { code: '101Y003', name: '광의통화(M2)', cycle: 'M' },
    '통화량': { code: '101Y003', name: '통화량', cycle: 'M' },
    'BSI': { code: '512Y014', name: '기업경기실사지수', cycle: 'M' },
    'CSI': { code: '511Y002', name: '소비자동향지수', cycle: 'M' },
    '국제수지': { code: '301Y013', name: '국제수지', cycle: 'M' },
    '경상수지': { code: '301Y013', name: '경상수지', cycle: 'M' },
    '외환보유액': { code: '732Y001', name: '외환보유액', cycle: 'M' },
  };

  static readonly CYCLE_CODES: Record<string, string> = {
    'D': '일', 'W': '주', 'M': '월', 'Q': '분기', 'S': '반기', 'A': '연',
  };

  private static readonly ERROR_CODES: Record<string, string> = {
    '000': '정상 처리',
    '100': '서비스 점검중',
    '200': '일일 트래픽 제한 초과',
    '300': '인증키 오류',
    '400': '필수 파라미터 누락',
    '500': '데이터 없음',
    '999': '시스템 오류',
  };

  static adaptFilters(filters: QueryFilters): Record<string, unknown> {
    const params: Record<string, unknown> = {
      language: 'kr',
      reqType: 'json',
      startCount: 1,
      endCount: 100,
    };

    if (filters.keywords) {
      const statInfo = this.inferStatFromKeywords(filters.keywords);
      if (statInfo) {
        params.statCode = statInfo.code;
        params.cycle = statInfo.cycle;
        params._statName = statInfo.name;
      }
    }

    const cycle = (params.cycle as string) || 'M';
    if (filters.dateRange) {
      if (filters.dateRange.start) {
        params.startTime = this.formatDate(filters.dateRange.start, cycle);
      }
      if (filters.dateRange.end) {
        params.endTime = this.formatDate(filters.dateRange.end, cycle);
      }
    } else {
      const endDate = new Date();
      const startDate = new Date();
      startDate.setFullYear(endDate.getFullYear() - 1);
      params.endTime = this.formatDate(endDate.toISOString().split('T')[0] || '', cycle);
      params.startTime = this.formatDate(startDate.toISOString().split('T')[0] || '', cycle);
    }

    if (filters.custom?.statCode) params.statCode = filters.custom.statCode;
    if (filters.custom?.itemCode1) params.itemCode1 = filters.custom.itemCode1;
    if (filters.custom?.cycle) params.cycle = filters.custom.cycle;

    return params;
  }

  private static formatDate(dateStr: string, cycle: string): string {
    const date = dateStr.replace(/-/g, '');
    switch (cycle) {
      case 'D': return date.substring(0, 8);
      case 'M': return date.substring(0, 6);
      case 'Q': {
        const quarter = Math.ceil(parseInt(date.substring(4, 6)) / 3);
        return `${date.substring(0, 4)}Q${quarter}`;
      }
      case 'A': return date.substring(0, 4);
      default: return date.substring(0, 6);
    }
  }

  private static inferStatFromKeywords(keywords: string[]): { code: string; name: string; cycle: string } | null {
    const text = keywords.join(' ');
    for (const [keyword, info] of Object.entries(this.STAT_CODES)) {
      if (text.includes(keyword)) return info;
    }
    if (text.includes('금리') || text.includes('이자율')) return this.STAT_CODES['기준금리'] || null;
    if (text.includes('환율') || text.includes('달러')) return this.STAT_CODES['환율'] || null;
    if (text.includes('통화') || text.includes('화폐')) return this.STAT_CODES['M2'] || null;
    if (text.includes('경기') || text.includes('실사')) return this.STAT_CODES['BSI'] || null;
    return null;
  }

  static normalizeDataResponse(data: unknown): NormalizedResponse<EcosStatItem> {
    const dataObj = data as Record<string, unknown>;

    if (dataObj.RESULT) {
      const result = dataObj.RESULT as { CODE: string; MESSAGE: string };
      if (result.CODE !== '000') {
        return {
          success: false, totalCount: 0, page: 1, pageSize: 0, data: [],
          error: { code: result.CODE, message: this.getErrorMessage(result.CODE) },
          _raw: data,
        };
      }
    }

    if (dataObj.StatisticSearch) {
      const searchResult = dataObj.StatisticSearch as { list_total_count?: number; row?: unknown[] };
      const rows = searchResult.row || [];
      return {
        success: true,
        totalCount: searchResult.list_total_count || rows.length,
        page: 1,
        pageSize: rows.length,
        data: rows.map(item => this.normalizeStatItem(item)),
        _raw: data,
      };
    }

    if (Array.isArray(data)) {
      return {
        success: true, totalCount: data.length, page: 1, pageSize: data.length,
        data: data.map(item => this.normalizeStatItem(item)), _raw: data,
      };
    }

    return { success: true, totalCount: 0, page: 1, pageSize: 0, data: [], _raw: data };
  }

  static normalizeTableListResponse(data: unknown): NormalizedResponse<EcosStatTableItem> {
    const dataObj = data as Record<string, unknown>;
    if (dataObj.StatisticTableList) {
      const tableList = dataObj.StatisticTableList as { list_total_count?: number; row?: unknown[] };
      const rows = tableList.row || [];
      return {
        success: true,
        totalCount: tableList.list_total_count || rows.length,
        page: 1,
        pageSize: rows.length,
        data: rows.map(item => this.normalizeTableItem(item)),
        _raw: data,
      };
    }
    return { success: true, totalCount: 0, page: 1, pageSize: 0, data: [], _raw: data };
  }

  static normalizeKeyStatResponse(data: unknown): NormalizedResponse<EcosKeyStatItem> {
    const dataObj = data as Record<string, unknown>;
    if (dataObj.RESULT) {
      const result = dataObj.RESULT as { CODE: string; MESSAGE: string };
      if (result.CODE !== '000') {
        return {
          success: false, totalCount: 0, page: 1, pageSize: 0, data: [],
          error: { code: result.CODE, message: this.getErrorMessage(result.CODE) },
          _raw: data,
        };
      }
    }
    if (dataObj.KeyStatisticList) {
      const keyStatResult = dataObj.KeyStatisticList as { list_total_count?: number; row?: unknown[] };
      const rows = keyStatResult.row || [];
      return {
        success: true,
        totalCount: keyStatResult.list_total_count || rows.length,
        page: 1,
        pageSize: rows.length,
        data: rows.map(item => this.normalizeKeyStatItem(item)),
        _raw: data,
      };
    }
    return { success: true, totalCount: 0, page: 1, pageSize: 0, data: [], _raw: data };
  }

  private static getErrorMessage(errorCode: string): string {
    return this.ERROR_CODES[errorCode] || `알 수 없는 오류: ${errorCode}`;
  }

  private static normalizeStatItem(item: unknown): EcosStatItem {
    const obj = item as Record<string, unknown>;
    return {
      STAT_CODE: String(obj.STAT_CODE || ''),
      STAT_NAME: String(obj.STAT_NAME || ''),
      ITEM_CODE1: String(obj.ITEM_CODE1 || ''),
      ITEM_NAME1: String(obj.ITEM_NAME1 || ''),
      ITEM_CODE2: obj.ITEM_CODE2 ? String(obj.ITEM_CODE2) : undefined,
      ITEM_NAME2: obj.ITEM_NAME2 ? String(obj.ITEM_NAME2) : undefined,
      ITEM_CODE3: obj.ITEM_CODE3 ? String(obj.ITEM_CODE3) : undefined,
      ITEM_NAME3: obj.ITEM_NAME3 ? String(obj.ITEM_NAME3) : undefined,
      ITEM_CODE4: obj.ITEM_CODE4 ? String(obj.ITEM_CODE4) : undefined,
      ITEM_NAME4: obj.ITEM_NAME4 ? String(obj.ITEM_NAME4) : undefined,
      UNIT_NAME: String(obj.UNIT_NAME || ''),
      TIME: String(obj.TIME || ''),
      DATA_VALUE: String(obj.DATA_VALUE || ''),
    };
  }

  private static normalizeTableItem(item: unknown): EcosStatTableItem {
    const obj = item as Record<string, unknown>;
    return {
      STAT_CODE: String(obj.STAT_CODE || ''),
      STAT_NAME: String(obj.STAT_NAME || ''),
      CYCLE: String(obj.CYCLE || ''),
      SRCH_YN: String(obj.SRCH_YN || 'N'),
      ORG_NAME: obj.ORG_NAME ? String(obj.ORG_NAME) : undefined,
    };
  }

  private static normalizeKeyStatItem(item: unknown): EcosKeyStatItem {
    const obj = item as Record<string, unknown>;
    return {
      CLASS_NAME: String(obj.CLASS_NAME || ''),
      KEYSTAT_NAME: String(obj.KEYSTAT_NAME || ''),
      DATA_VALUE: String(obj.DATA_VALUE || ''),
      UNIT_NAME: String(obj.UNIT_NAME || ''),
      CYCLE: String(obj.CYCLE || ''),
      TIME: String(obj.TIME || ''),
    };
  }

  static buildApiUrl(apiKey: string, endpoint: EcosEndpoint, params: Record<string, unknown>): string {
    const base = `https://ecos.bok.or.kr/api/${endpoint}`;

    if (endpoint === 'StatisticSearch') {
      const parts = [
        apiKey, params.language || 'kr', params.reqType || 'json',
        params.startCount || 1, params.endCount || 100,
        params.statCode, params.cycle || 'M', params.startTime, params.endTime,
      ];
      if (params.itemCode1) parts.push(params.itemCode1);
      if (params.itemCode2) parts.push(params.itemCode2);
      if (params.itemCode3) parts.push(params.itemCode3);
      if (params.itemCode4) parts.push(params.itemCode4);
      return `${base}/${parts.join('/')}`;
    }

    if (endpoint === 'StatisticTableList') {
      const parts = [apiKey, params.language || 'kr', params.reqType || 'json', params.startCount || 1, params.endCount || 1000];
      if (params.statCode) parts.push(params.statCode);
      return `${base}/${parts.join('/')}`;
    }

    if (endpoint === 'StatisticItemList') {
      const parts = [apiKey, params.language || 'kr', params.reqType || 'json', params.startCount || 1, params.endCount || 1000, params.statCode];
      return `${base}/${parts.join('/')}`;
    }

    if (endpoint === 'KeyStatisticList') {
      const parts = [apiKey, params.language || 'kr', params.reqType || 'json', params.startCount || 1, params.endCount || 100];
      return `${base}/${parts.join('/')}`;
    }

    return base;
  }

  static buildInterestRateParams(startDate?: string, endDate?: string): Record<string, unknown> {
    const end = endDate || new Date().toISOString().split('T')[0] || '';
    const start = startDate || (() => { const d = new Date(); d.setFullYear(d.getFullYear() - 1); return d.toISOString().split('T')[0] || ''; })();
    return {
      statCode: '722Y001', cycle: 'D',
      startTime: this.formatDate(start, 'D'),
      endTime: this.formatDate(end, 'D'),
      itemCode1: '0101000',
    };
  }

  static buildExchangeRateParams(currency: '달러' | '엔' | '유로' = '달러', startDate?: string, endDate?: string): Record<string, unknown> {
    const currencyCodes: Record<string, string> = { '달러': '0000001', '엔': '0000002', '유로': '0000003' };
    const end = endDate || new Date().toISOString().split('T')[0] || '';
    const start = startDate || (() => { const d = new Date(); d.setMonth(d.getMonth() - 3); return d.toISOString().split('T')[0] || ''; })();
    return {
      statCode: '731Y001', cycle: 'D',
      startTime: this.formatDate(start, 'D'),
      endTime: this.formatDate(end, 'D'),
      itemCode1: currencyCodes[currency] || currencyCodes['달러'],
    };
  }

  /**
   * 데이터 요약 생성
   */
  static generateSummary(data: EcosStatItem[]): {
    totalRecords: number;
    statName: string;
    dateRange: { start: string; end: string } | null;
    latestValue: { time: string; value: string; unit: string } | null;
    minValue: { time: string; value: string } | null;
    maxValue: { time: string; value: string } | null;
  } {
    if (data.length === 0) {
      return {
        totalRecords: 0,
        statName: '',
        dateRange: null,
        latestValue: null,
        minValue: null,
        maxValue: null,
      };
    }

    const sortedByTime = [...data].sort((a, b) => a.TIME.localeCompare(b.TIME));
    const numericData = data
      .map(d => ({ time: d.TIME, value: parseFloat(d.DATA_VALUE) }))
      .filter(d => !isNaN(d.value));

    if (numericData.length === 0 || sortedByTime.length === 0) {
      return {
        totalRecords: data.length,
        statName: data[0]?.STAT_NAME || '',
        dateRange: null,
        latestValue: null,
        minValue: null,
        maxValue: null,
      };
    }

    const firstNumeric = numericData[0]!;
    const minItem = numericData.reduce((min, curr) => curr.value < min.value ? curr : min, firstNumeric);
    const maxItem = numericData.reduce((max, curr) => curr.value > max.value ? curr : max, firstNumeric);
    const latest = sortedByTime[sortedByTime.length - 1];
    const first = sortedByTime[0];

    return {
      totalRecords: data.length,
      statName: data[0]?.STAT_NAME || '',
      dateRange: first && latest ? {
        start: first.TIME,
        end: latest.TIME,
      } : null,
      latestValue: latest ? {
        time: latest.TIME,
        value: latest.DATA_VALUE,
        unit: latest.UNIT_NAME,
      } : null,
      minValue: minItem ? { time: minItem.time, value: String(minItem.value) } : null,
      maxValue: maxItem ? { time: maxItem.time, value: String(maxItem.value) } : null,
    };
  }
}
