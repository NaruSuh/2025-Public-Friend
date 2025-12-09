import { QueryFilters } from '@/types/nlp.types';

/**
 * 중앙선거관리위원회 정당정책 정보 조회 API Adapter
 *
 * API 정보:
 * - 서비스명: 정당정책 정보 조회 서비스 (PartyPlcInfoInqireService)
 * - Endpoint: getPartyPlcInfoInqire (정당정책 정보 조회)
 * - Base URL: http://apis.data.go.kr/9760000/PartyPlcInfoInqireService
 * - 인증: Service Key (공공데이터포털 발급)
 *
 * 주요 파라미터:
 * - sgId: 선거ID (예: 20220309)
 * - partyName: 정당명 (예: 00당)
 *
 * 응답 필드:
 * - sgId: 선거ID
 * - partyName: 정당명
 * - prmsCnt: 공약개수
 * - prmsOrd1~10: 공약순번 1~10
 * - prmsRealmName1~10: 공약분야명 1~10
 * - prmsTitle1~10: 공약제목명 1~10
 * - prmsCont1~10: 공약내용 1~10
 *
 * 특징:
 * - 한 정당당 최대 10개의 공약을 포함
 * - 정당마다 공약 개수가 다를 수 있음
 * - 매 선거 종료 후 두 달 이내 데이터 갱신
 */
export class PartyPolicyAdapter {
  // 주요 정당 목록 (기본값으로 사용)
  static readonly MAJOR_PARTIES = [
    '더불어민주당',
    '국민의힘',
    '정의당',
    '국민의당',
    '기본소득당',
    '진보당',
    '녹색당',
  ] as const;

  // 최근 주요 선거 ID 목록
  static readonly RECENT_ELECTIONS = {
    '20240410': { name: '제22대 국회의원선거', type: '2' },
    '20220601': { name: '제8회 전국동시지방선거', type: '3' },
    '20220309': { name: '제20대 대통령선거', type: '1' },
    '20200415': { name: '제21대 국회의원선거', type: '2' },
    '20180613': { name: '제7회 전국동시지방선거', type: '3' },
    '20170509': { name: '제19대 대통령선거', type: '1' },
  } as const;

  // 정당명 별칭 매핑
  static readonly PARTY_ALIASES: Record<string, string> = {
    '민주당': '더불어민주당',
    '더민주': '더불어민주당',
    '국힘': '국민의힘',
    '국민의당': '국민의당',
    '정의당': '정의당',
    '기본소득': '기본소득당',
    '진보당': '진보당',
    '녹색당': '녹색당',
  };

  /**
   * QueryFilters를 정당정책 API 파라미터로 변환
   */
  static adaptFilters(filters: QueryFilters): Record<string, any> {
    const params: Record<string, any> = {
      pageNo: 1,
      numOfRows: 100,
      resultType: 'json',
    };

    // 선거 ID 추출 - 다양한 소스에서 시도
    if (filters.sgId) {
      params.sgId = Array.isArray(filters.sgId) ? filters.sgId[0] : filters.sgId;
    } else if (filters.dateRange?.start) {
      params.sgId = filters.dateRange.start.replace(/-/g, '');
    } else if (filters.keywords) {
      const sgId = this.inferElectionIdFromKeywords(filters.keywords);
      if (sgId) {
        params.sgId = sgId;
      }
    }

    // 정당명 추출
    if (filters.partyName) {
      params.partyName = this.normalizePartyName(
        Array.isArray(filters.partyName) ? filters.partyName[0] : filters.partyName
      );
    } else if (filters.keywords) {
      const partyName = this.extractPartyFromKeywords(filters.keywords);
      if (partyName) {
        params.partyName = partyName;
      }
    }

    return params;
  }

  /**
   * 키워드에서 선거 ID 추론
   */
  private static inferElectionIdFromKeywords(keywords: string[]): string | null {
    const text = keywords.join(' ');

    // 연도와 선거 종류로 매핑
    if (text.includes('2024') && (text.includes('총선') || text.includes('국회의원'))) {
      return '20240410';
    }
    if (text.includes('2022') && (text.includes('지방선거') || text.includes('지방'))) {
      return '20220601';
    }
    if (text.includes('2022') && (text.includes('대선') || text.includes('대통령'))) {
      return '20220309';
    }
    if (text.includes('2020') && (text.includes('총선') || text.includes('국회의원'))) {
      return '20200415';
    }
    if (text.includes('2018') && (text.includes('지방선거') || text.includes('지방'))) {
      return '20180613';
    }
    if (text.includes('2017') && (text.includes('대선') || text.includes('대통령'))) {
      return '20170509';
    }

    // "최근" 키워드 처리
    if (text.includes('최근')) {
      if (text.includes('지방')) return '20220601';
      if (text.includes('대선') || text.includes('대통령')) return '20220309';
      if (text.includes('총선') || text.includes('국회')) return '20240410';
      return '20220601'; // 기본: 가장 최근 지방선거
    }

    return null;
  }

  /**
   * 키워드에서 정당명 추출
   */
  private static extractPartyFromKeywords(keywords: string[]): string | null {
    const text = keywords.join(' ');

    // 별칭을 포함한 모든 정당명 체크
    for (const [alias, fullName] of Object.entries(this.PARTY_ALIASES)) {
      if (text.includes(alias)) {
        return fullName;
      }
    }

    // 주요 정당 직접 매칭
    for (const party of this.MAJOR_PARTIES) {
      if (text.includes(party)) {
        return party;
      }
    }

    return null;
  }

  /**
   * 정당명 정규화 (별칭 → 정식명칭)
   */
  static normalizePartyName(name: string): string {
    const normalized = name.trim();
    return this.PARTY_ALIASES[normalized] || normalized;
  }

  /**
   * 누락된 파라미터 추론
   */
  static inferMissingParams(
    params: Record<string, any>,
    context?: { keywords?: string[]; query?: string }
  ): Record<string, any> {
    const inferred = { ...params };

    // sgId가 없으면 최근 선거로 기본 설정
    if (!inferred.sgId) {
      if (context?.keywords) {
        const sgId = this.inferElectionIdFromKeywords(context.keywords);
        if (sgId) {
          inferred.sgId = sgId;
          inferred._inferred = inferred._inferred || {};
          inferred._inferred.sgId = `추론됨: ${PartyPolicyAdapter.RECENT_ELECTIONS[sgId as keyof typeof PartyPolicyAdapter.RECENT_ELECTIONS]?.name || sgId}`;
        }
      }

      // 여전히 없으면 기본값
      if (!inferred.sgId) {
        inferred.sgId = '20220601'; // 2022 지방선거
        inferred._inferred = inferred._inferred || {};
        inferred._inferred.sgId = '기본값: 제8회 전국동시지방선거 (20220601)';
      }
    }

    // partyName이 없으면 주요 정당 전체 조회 표시
    if (!inferred.partyName) {
      inferred._queryAllMajorParties = true;
      inferred._inferred = inferred._inferred || {};
      inferred._inferred.partyName = `주요 정당 전체 조회: ${this.MAJOR_PARTIES.slice(0, 3).join(', ')} 등`;
    }

    return inferred;
  }

  /**
   * 주요 정당 목록 반환 (조회용)
   */
  static getMajorParties(): string[] {
    return [...this.MAJOR_PARTIES];
  }

  /**
   * 최근 선거 ID 목록 반환
   */
  static getRecentElectionIds(): string[] {
    return Object.keys(this.RECENT_ELECTIONS);
  }
  /**
   * API 응답 정규화
   */
  static normalizeResponse(data: any): any {
    // baseConnector에서 이미 정규화된 배열 형태인 경우
    if (Array.isArray(data)) {
      return {
        success: true,
        totalCount: data.length,
        pageNo: 1,
        numOfRows: data.length,
        data: data.map(this.normalizeItem),
      };
    }

    // XML/JSON 응답 처리
    if (data?.response) {
      const response = data.response;

      // 에러 체크
      if (response.header) {
        const { resultCode, resultMsg } = response.header;
        if (resultCode !== '00' && resultCode !== 'INFO-00') {
          return {
            success: false,
            error: {
              code: resultCode,
              message: resultMsg,
            },
          };
        }
      }

      // 정상 응답
      if (response.body?.items) {
        const items = Array.isArray(response.body.items.item)
          ? response.body.items.item
          : response.body.items.item
          ? [response.body.items.item]
          : [];

        return {
          success: true,
          totalCount: response.body.totalCount || items.length,
          pageNo: response.body.pageNo || 1,
          numOfRows: response.body.numOfRows || 10,
          data: items.map(this.normalizeItem),
        };
      }

      // items가 없는 경우 (데이터 없음)
      return {
        success: true,
        totalCount: 0,
        pageNo: response.body?.pageNo || 1,
        numOfRows: response.body?.numOfRows || 10,
        data: [],
      };
    }

    // 원본 데이터 반환
    return data;
  }

  /**
   * 개별 정당정책 아이템 정규화
   *
   * 중요: API는 최대 10개의 공약을 prmsOrd1~10, prmsTitle1~10 형태로 반환
   */
  private static normalizeItem(item: any): any {
    // 공약 배열 생성 (1~10)
    const policies = [];
    const prmsCnt = item.prmsCnt || 0;

    for (let i = 1; i <= 10; i++) {
      const ordKey = `prmsOrd${i}`;
      const realmKey = `prmsRealmName${i}`;
      const titleKey = `prmsTitle${i}`;
      const contKey = `prmsCont${i}`;

      // 공약 데이터가 있는 경우에만 추가
      if (item[ordKey] || item[titleKey]) {
        policies.push({
          order: item[ordKey] || i,
          realm: item[realmKey] || null,
          title: item[titleKey] || null,
          content: item[contKey] || null,
        });
      }
    }

    return {
      // 기본 정보
      electionId: item.sgId,
      partyName: item.partyName,
      policyCount: prmsCnt,

      // 공약 배열
      policies,

      // 원본 데이터 보존
      _raw: item,
    };
  }

  /**
   * 정당명으로 필터링
   * @param data 정당정책 목록 배열
   * @param partyKeyword 검색할 정당명 키워드
   * @returns 매칭된 정당정책 배열
   */
  static filterByPartyName(data: any[], partyKeyword: string): any[] {
    if (!data || data.length === 0) {
      return [];
    }

    return data.filter((item) => {
      const partyName = item.partyName || '';
      return partyName.includes(partyKeyword);
    });
  }

  /**
   * 공약 분야로 필터링
   * @param policies 공약 배열
   * @param realmKeyword 검색할 분야 키워드 (예: "노동", "환경")
   * @returns 매칭된 공약 배열
   */
  static filterPoliciesByRealm(policies: any[], realmKeyword: string): any[] {
    if (!policies || policies.length === 0) {
      return [];
    }

    return policies.filter((policy) => {
      const realm = policy.realm || '';
      return realm.includes(realmKeyword);
    });
  }

  /**
   * 공약 제목으로 검색
   * @param policies 공약 배열
   * @param titleKeyword 검색할 제목 키워드
   * @returns 매칭된 공약 배열
   */
  static searchPoliciesByTitle(policies: any[], titleKeyword: string): any[] {
    if (!policies || policies.length === 0) {
      return [];
    }

    return policies.filter((policy) => {
      const title = policy.title || '';
      const content = policy.content || '';
      return title.includes(titleKeyword) || content.includes(titleKeyword);
    });
  }

  /**
   * 파라미터 검증
   */
  static validateParams(params: Record<string, any>): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    // 필수 파라미터 검증
    if (!params.sgId) {
      errors.push('sgId (선거ID) is required. Format: YYYYMMDD (예: 20220309)');
    }

    if (!params.partyName) {
      errors.push('partyName (정당명) is required. (예: 00당)');
    }

    // 페이지 번호 검증
    if (params.pageNo && (params.pageNo < 1 || params.pageNo > 100000)) {
      errors.push('pageNo must be between 1 and 100000');
    }

    // 목록 건수 검증
    if (params.numOfRows && (params.numOfRows < 1 || params.numOfRows > 100)) {
      errors.push('numOfRows must be between 1 and 100');
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  /**
   * 여러 정당의 정책 비교용 데이터 구조 생성
   * @param partyPolicies 여러 정당의 정책 배열
   * @returns 정당별 정책 비교 데이터
   */
  static createComparisonData(partyPolicies: any[]): any {
    const comparison: Record<string, any> = {
      parties: [],
      realms: new Set<string>(),
      comparison: {},
    };

    partyPolicies.forEach((partyPolicy) => {
      const partyName = partyPolicy.partyName;
      comparison.parties.push(partyName);
      comparison.comparison[partyName] = {};

      partyPolicy.policies.forEach((policy: any) => {
        const realm = policy.realm || '기타';
        comparison.realms.add(realm);

        if (!comparison.comparison[partyName][realm]) {
          comparison.comparison[partyName][realm] = [];
        }

        comparison.comparison[partyName][realm].push({
          title: policy.title,
          content: policy.content,
          order: policy.order,
        });
      });
    });

    return {
      parties: comparison.parties,
      realms: Array.from(comparison.realms),
      comparison: comparison.comparison,
    };
  }

  /**
   * 공약 통계 생성
   * @param partyPolicy 정당정책 데이터
   * @returns 공약 통계 정보
   */
  static generatePolicyStats(partyPolicy: any): any {
    const stats: Record<string, any> = {
      partyName: partyPolicy.partyName,
      totalPolicies: partyPolicy.policyCount,
      realmCounts: {},
      hasContent: 0,
      noContent: 0,
    };

    partyPolicy.policies.forEach((policy: any) => {
      const realm = policy.realm || '기타';

      if (!stats.realmCounts[realm]) {
        stats.realmCounts[realm] = 0;
      }
      stats.realmCounts[realm]++;

      if (policy.content) {
        stats.hasContent++;
      } else {
        stats.noContent++;
      }
    });

    return stats;
  }
}
