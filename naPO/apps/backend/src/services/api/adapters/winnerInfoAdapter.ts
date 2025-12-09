import { QueryFilters } from '@/types/nlp.types';

/**
 * 중앙선거관리위원회 당선인 정보 API Adapter
 *
 * API 정보:
 * - 서비스명: 당선인정보 조회 서비스 (WinnerInfoInqireService2)
 * - Endpoint: getWinnerInfoInqire (당선인 정보 조회)
 * - Base URL: http://apis.data.go.kr/9760000/WinnerInfoInqireService2
 * - 인증: Service Key (공공데이터포털 발급)
 *
 * 주요 파라미터:
 * - sgId: 선거ID (예: 20220601)
 * - sgTypecode: 선거종류코드
 *   1: 대통령선거
 *   2: 국회의원선거
 *   3: 시·도지사선거
 *   4: 구·시·군의장선거
 *   5: 시·도의원선거
 *   6: 구·시·군의원선거
 *   11: 교육감선거
 * - sdName: 시도명 (선택)
 * - wiwName: 구시군명 (선택)
 */
export class WinnerInfoAdapter {
  // 선거종류코드 매핑
  static readonly ELECTION_TYPE_CODES = {
    president: '1',       // 대통령선거
    assembly: '2',        // 국회의원선거
    governor: '3',        // 시·도지사선거
    mayor: '4',           // 구·시·군의장선거
    provincial: '5',      // 시·도의원선거
    council: '6',         // 구·시·군의원선거
    superintendent: '11', // 교육감선거
  } as const;

  // 최근 주요 선거 ID 목록
  static readonly RECENT_ELECTIONS = {
    '20240410': { name: '제22대 국회의원선거', type: '2' },
    '20220601': { name: '제8회 전국동시지방선거', type: '3' },
    '20220309': { name: '제20대 대통령선거', type: '1' },
    '20200415': { name: '제21대 국회의원선거', type: '2' },
    '20180613': { name: '제7회 전국동시지방선거', type: '3' },
  } as const;

  // 가장 최근 선거 (유형별)
  static readonly LATEST_ELECTIONS = {
    default: '20240410',      // 가장 최근 전체 선거
    대선: '20220309',
    대통령: '20220309',
    총선: '20240410',
    국회: '20240410',
    지방선거: '20220601',
    지방: '20220601',
  } as const;

  // 알려진 후보자/정당 이름 (득표율 조회용)
  static readonly KNOWN_CANDIDATES: Record<string, { sgId: string; sgTypecode: string }> = {
    '윤석열': { sgId: '20220309', sgTypecode: '1' },
    '이재명': { sgId: '20220309', sgTypecode: '1' },
    '심상정': { sgId: '20220309', sgTypecode: '1' },
    '안철수': { sgId: '20220309', sgTypecode: '1' },
  };

  // 정당명 패턴
  static readonly PARTY_PATTERNS: Record<string, string[]> = {
    '더불어민주당': ['민주당', '더민주', '민주'],
    '국민의힘': ['국힘', '국민의힘'],
    '정의당': ['정의당'],
  };

  /**
   * QueryFilters를 당선인 API 파라미터로 변환
   */
  static adaptFilters(filters: QueryFilters): Record<string, any> {
    const params: Record<string, any> = {
      pageNo: 1,
      numOfRows: 100,
      resultType: 'json',
    };

    // 선거 ID 추출 - 다양한 소스에서 시도
    if (filters.sgId) {
      // 직접 지정된 경우
      params.sgId = Array.isArray(filters.sgId) ? filters.sgId[0] : filters.sgId;
    } else if (filters.dateRange?.start) {
      // 날짜 범위에서 추출
      params.sgId = filters.dateRange.start.replace(/-/g, '');
    } else if (filters.keywords) {
      // 키워드에서 선거 ID 추론
      const sgId = this.inferElectionIdFromKeywords(filters.keywords);
      if (sgId) {
        params.sgId = sgId;
      }
    }

    // 선거종류코드 추출
    if (filters.election?.type) {
      params.sgTypecode = this.mapElectionType(filters.election.type);
    } else if (filters.keywords) {
      const sgTypecode = this.inferElectionTypeFromKeywords(filters.keywords);
      if (sgTypecode) {
        params.sgTypecode = sgTypecode;
      }
    }

    // 지역 필터
    if (filters.region) {
      if (typeof filters.region === 'object') {
        if (filters.region.sido) {
          params.sdName = filters.region.sido;
        }
        if (filters.region.sigungu) {
          params.wiwName = filters.region.sigungu;
        }
      } else if (typeof filters.region === 'string') {
        // 문자열인 경우 sido로 처리
        params.sdName = filters.region;
      }
    }

    // 키워드에서 지역명 추출 시도
    if (!params.sdName && filters.keywords) {
      const region = this.extractRegionFromKeywords(filters.keywords);
      if (region.sido) params.sdName = region.sido;
      if (region.sigungu) params.wiwName = region.sigungu;
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

    // "최근" 키워드가 있으면 가장 최근 선거
    if (text.includes('최근')) {
      // 선거 유형별로 가장 최근 선거 매핑
      if (text.includes('지방') || text.includes('시장') || text.includes('지사')) {
        return this.LATEST_ELECTIONS['지방선거'];
      }
      if (text.includes('대선') || text.includes('대통령')) {
        return this.LATEST_ELECTIONS['대선'];
      }
      if (text.includes('총선') || text.includes('국회') || text.includes('의원')) {
        return this.LATEST_ELECTIONS['총선'];
      }
      // "최근 선거", "최근 선거 결과" 등 유형 미지정 시 가장 최근 전체 선거
      return this.LATEST_ELECTIONS['default'];
    }

    // 선거 종류만 언급한 경우 (연도 없이)
    if (text.includes('지방선거') || (text.includes('시장') && text.includes('선거'))) {
      return this.LATEST_ELECTIONS['지방선거'];
    }
    if (text.includes('대선') || text.includes('대통령선거')) {
      return this.LATEST_ELECTIONS['대선'];
    }
    if (text.includes('총선') || text.includes('국회의원선거')) {
      return this.LATEST_ELECTIONS['총선'];
    }

    return null;
  }

  /**
   * 키워드에서 선거 종류 추론
   */
  private static inferElectionTypeFromKeywords(keywords: string[]): string | null {
    const text = keywords.join(' ');

    if (text.includes('대통령') || text.includes('대선')) {
      return this.ELECTION_TYPE_CODES.president;
    }
    if (text.includes('국회의원') || text.includes('총선')) {
      return this.ELECTION_TYPE_CODES.assembly;
    }
    if (text.includes('시장') || text.includes('군수') || text.includes('구청장')) {
      return this.ELECTION_TYPE_CODES.mayor;
    }
    if (text.includes('도지사') || text.includes('지사') || text.includes('광역')) {
      return this.ELECTION_TYPE_CODES.governor;
    }
    if (text.includes('교육감')) {
      return this.ELECTION_TYPE_CODES.superintendent;
    }
    if (text.includes('도의원') || text.includes('시의원') && text.includes('광역')) {
      return this.ELECTION_TYPE_CODES.provincial;
    }
    if (text.includes('구의원') || text.includes('군의원')) {
      return this.ELECTION_TYPE_CODES.council;
    }

    // 지방선거 키워드가 있으면 기본적으로 시도지사
    if (text.includes('지방선거') || text.includes('지방')) {
      return this.ELECTION_TYPE_CODES.governor;
    }

    return null;
  }

  /**
   * 키워드에서 지역명 추출
   */
  private static extractRegionFromKeywords(keywords: string[]): { sido?: string; sigungu?: string } {
    const text = keywords.join(' ');
    const result: { sido?: string; sigungu?: string } = {};

    // 광역시/도 추출
    const sidoPatterns = [
      '서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종',
      '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주',
    ];

    for (const sido of sidoPatterns) {
      if (text.includes(sido)) {
        result.sido = sido;
        break;
      }
    }

    return result;
  }

  /**
   * 선거 종류 텍스트를 코드로 매핑
   */
  private static mapElectionType(type: string): string {
    const normalized = type.toLowerCase().replace(/\s+/g, '');

    if (normalized.includes('대통령') || normalized === 'president') {
      return this.ELECTION_TYPE_CODES.president;
    }
    if (normalized.includes('국회') || normalized.includes('총선') || normalized === 'assembly') {
      return this.ELECTION_TYPE_CODES.assembly;
    }
    if (normalized.includes('도지사') || normalized.includes('지사') || normalized === 'governor') {
      return this.ELECTION_TYPE_CODES.governor;
    }
    if (normalized.includes('시장') || normalized.includes('군수') || normalized.includes('구청장') || normalized === 'mayor') {
      return this.ELECTION_TYPE_CODES.mayor;
    }
    if (normalized.includes('교육감') || normalized === 'superintendent') {
      return this.ELECTION_TYPE_CODES.superintendent;
    }
    if (normalized.includes('도의원') || normalized === 'provincial') {
      return this.ELECTION_TYPE_CODES.provincial;
    }
    if (normalized.includes('구의원') || normalized.includes('군의원') || normalized === 'council') {
      return this.ELECTION_TYPE_CODES.council;
    }

    // 지방선거 기본값
    if (normalized.includes('지방')) {
      return this.ELECTION_TYPE_CODES.governor;
    }

    return this.ELECTION_TYPE_CODES.governor; // 기본값
  }

  /**
   * 파라미터 검증
   */
  static validateParams(params: Record<string, any>): { valid: boolean; errors: string[]; warnings: string[] } {
    const errors: string[] = [];
    const warnings: string[] = [];

    // 필수 파라미터 검증
    if (!params.sgId) {
      errors.push('sgId (선거ID) is required. Format: YYYYMMDD (예: 20220601)');
    } else if (!/^\d{8}$/.test(params.sgId)) {
      errors.push(`Invalid sgId format: ${params.sgId}. Must be 8 digits (YYYYMMDD)`);
    }

    if (!params.sgTypecode) {
      warnings.push('sgTypecode not specified. Will return all election types for the given election.');
    } else {
      const validCodes = ['1', '2', '3', '4', '5', '6', '11'];
      if (!validCodes.includes(params.sgTypecode)) {
        errors.push(`Invalid sgTypecode: ${params.sgTypecode}. Must be one of: ${validCodes.join(', ')}`);
      }
    }

    // 페이지 번호 검증
    if (params.pageNo && (params.pageNo < 1 || params.pageNo > 100000)) {
      errors.push('pageNo must be between 1 and 100000');
    }

    // 목록 건수 검증
    if (params.numOfRows && (params.numOfRows < 1 || params.numOfRows > 100)) {
      warnings.push('numOfRows adjusted to max 100');
      params.numOfRows = Math.min(params.numOfRows, 100);
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings,
    };
  }

  /**
   * API 응답 정규화
   */
  static normalizeResponse(data: any): any {
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
              message: resultMsg || this.interpretErrorCode(resultCode),
            },
          };
        }
      }

      // 정상 응답
      if (response.body?.items) {
        let items = response.body.items.item;

        // 단일 객체인 경우 배열로 변환
        if (!Array.isArray(items)) {
          items = items ? [items] : [];
        }

        return {
          success: true,
          totalCount: response.body.totalCount || items.length,
          pageNo: response.body.pageNo || 1,
          numOfRows: response.body.numOfRows || 100,
          data: items.map((item: any) => this.normalizeItem(item)),
        };
      }

      // items가 없는 경우 (데이터 없음)
      return {
        success: true,
        totalCount: 0,
        pageNo: response.body?.pageNo || 1,
        numOfRows: response.body?.numOfRows || 100,
        data: [],
        message: '해당 조건에 맞는 당선인 정보가 없습니다.',
      };
    }

    // 원본 데이터 반환
    return data;
  }

  /**
   * 개별 아이템 정규화
   */
  private static normalizeItem(item: any): any {
    return {
      // 선거 정보
      electionId: item.sgId,
      electionName: item.sgName,
      electionType: item.sgTypecode,
      electionTypeName: this.getElectionTypeName(item.sgTypecode),

      // 선거구 정보
      constituencyName: item.sggName,
      sido: item.sdName,
      sigungu: item.wiwName,

      // 당선인 정보
      candidateNumber: item.giho,
      party: item.jdName,
      nameKr: item.name,
      nameCn: item.hanjaName,
      gender: item.gender,
      birthDate: item.birthday,
      age: item.age,
      address: item.addr,

      // 학력/경력
      education: item.edu,
      career: item.career?.split('\n').filter((c: string) => c.trim()),

      // 득표 정보
      voteCount: item.dugsu ? parseInt(item.dugsu, 10) : null,
      voteRate: item.dugyul ? parseFloat(item.dugyul) : null,

      // 상태
      status: item.status,

      // 원본 데이터 보존
      _raw: item,
    };
  }

  /**
   * 선거종류코드를 이름으로 변환
   */
  private static getElectionTypeName(code: string): string {
    const names: Record<string, string> = {
      '1': '대통령선거',
      '2': '국회의원선거',
      '3': '시·도지사선거',
      '4': '구·시·군의장선거',
      '5': '시·도의원선거',
      '6': '구·시·군의원선거',
      '11': '교육감선거',
    };
    return names[code] || `선거종류 ${code}`;
  }

  /**
   * 에러 코드 해석
   */
  static interpretErrorCode(code: string): string {
    const errorMessages: Record<string, string> = {
      // 공공데이터포털 에러
      '1': '어플리케이션 에러',
      '04': 'HTTP 에러',
      '12': '해당 오픈API 서비스가 없거나 폐기됨',
      '20': '서비스 접근 거부',
      '22': '서비스 요청 제한 횟수 초과',
      '30': '등록되지 않은 서비스키',
      '31': '활용기간 만료',
      '32': '등록되지 않은 IP',
      '99': '기타 에러',
      // 제공기관 에러
      'ERROR-03': '데이터 정보가 없습니다',
      'ERROR-301': '파일타입 값이 누락 혹은 유효하지 않습니다',
      'ERROR-310': '해당하는 서비스를 찾을 수 없습니다',
      'ERROR-333': '요청위치 값의 타입이 유효하지 않습니다',
      'ERROR-340': '필수 파라미터가 누락되었습니다',
      'ERROR-500': '서버 오류입니다',
      'ERROR-601': 'SQL 문장 오류입니다',
    };

    return errorMessages[code] || `알 수 없는 에러 (${code})`;
  }

  /**
   * 기본 선거 ID 목록 반환 (최근 선거들)
   */
  static getDefaultElectionIds(): string[] {
    return Object.keys(this.RECENT_ELECTIONS);
  }

  /**
   * 누락된 파라미터 추론
   * 컨텍스트(키워드, 원본 쿼리)를 기반으로 sgId, sgTypecode 추론
   */
  static inferMissingParams(
    params: Record<string, any>,
    context?: { keywords?: string[]; query?: string }
  ): Record<string, any> {
    const inferred = { ...params };
    inferred._inferred = inferred._inferred || {};

    // sgId 추론
    if (!inferred.sgId) {
      if (context?.keywords) {
        const sgId = this.inferElectionIdFromKeywords(context.keywords);
        if (sgId) {
          inferred.sgId = sgId;
          const electionInfo = WinnerInfoAdapter.RECENT_ELECTIONS[sgId as keyof typeof WinnerInfoAdapter.RECENT_ELECTIONS];
          inferred._inferred.sgId = `추론됨: ${electionInfo?.name || sgId}`;
        }
      }

      // 원본 쿼리에서도 추론 시도
      if (!inferred.sgId && context?.query) {
        const queryKeywords = context.query.split(/\s+/);
        const sgId = this.inferElectionIdFromKeywords(queryKeywords);
        if (sgId) {
          inferred.sgId = sgId;
          const electionInfo = WinnerInfoAdapter.RECENT_ELECTIONS[sgId as keyof typeof WinnerInfoAdapter.RECENT_ELECTIONS];
          inferred._inferred.sgId = `쿼리에서 추론됨: ${electionInfo?.name || sgId}`;
        }
      }

      // 여전히 없으면 기본값 설정
      if (!inferred.sgId) {
        // 컨텍스트에서 선거 종류 힌트 찾기
        const text = (context?.keywords?.join(' ') || '') + ' ' + (context?.query || '');
        if (text.includes('대선') || text.includes('대통령')) {
          inferred.sgId = '20220309';
          inferred._inferred.sgId = '기본값: 제20대 대통령선거 (20220309)';
        } else if (text.includes('총선') || text.includes('국회')) {
          inferred.sgId = '20240410';
          inferred._inferred.sgId = '기본값: 제22대 국회의원선거 (20240410)';
        } else {
          inferred.sgId = '20220601';
          inferred._inferred.sgId = '기본값: 제8회 전국동시지방선거 (20220601)';
        }
      }
    }

    // sgTypecode 추론
    if (!inferred.sgTypecode) {
      if (context?.keywords) {
        const sgTypecode = this.inferElectionTypeFromKeywords(context.keywords);
        if (sgTypecode) {
          inferred.sgTypecode = sgTypecode;
          inferred._inferred.sgTypecode = `추론됨: ${this.getElectionTypeNamePublic(sgTypecode)}`;
        }
      }

      // 원본 쿼리에서도 추론 시도
      if (!inferred.sgTypecode && context?.query) {
        const queryKeywords = context.query.split(/\s+/);
        const sgTypecode = this.inferElectionTypeFromKeywords(queryKeywords);
        if (sgTypecode) {
          inferred.sgTypecode = sgTypecode;
          inferred._inferred.sgTypecode = `쿼리에서 추론됨: ${this.getElectionTypeNamePublic(sgTypecode)}`;
        }
      }

      // sgId에서 sgTypecode 추론
      if (!inferred.sgTypecode && inferred.sgId) {
        const electionInfo = WinnerInfoAdapter.RECENT_ELECTIONS[inferred.sgId as keyof typeof WinnerInfoAdapter.RECENT_ELECTIONS];
        if (electionInfo) {
          inferred.sgTypecode = electionInfo.type;
          inferred._inferred.sgTypecode = `sgId에서 추론됨: ${WinnerInfoAdapter.getElectionTypeNamePublic(electionInfo.type)}`;
        }
      }
    }

    // 지역 추론
    if (!inferred.sdName && context?.keywords) {
      const region = this.extractRegionFromKeywords(context.keywords);
      if (region.sido) {
        inferred.sdName = region.sido;
        inferred._inferred.sdName = `추론됨: ${region.sido}`;
      }
      if (region.sigungu) {
        inferred.wiwName = region.sigungu;
        inferred._inferred.wiwName = `추론됨: ${region.sigungu}`;
      }
    }

    // 득표율/투표율 쿼리 감지 및 처리
    const queryText = (context?.keywords?.join(' ') || '') + ' ' + (context?.query || '');
    if (queryText.includes('득표율') || queryText.includes('투표율')) {
      inferred._queryType = 'vote_rate';
      inferred._inferred.queryType = '득표율/투표율 조회';

      // 후보자 이름 추출
      const candidateName = this.extractCandidateName(queryText);
      if (candidateName) {
        inferred._filterCandidate = candidateName;
        inferred._inferred.filterCandidate = `후보자: ${candidateName}`;

        // 알려진 후보자면 선거 정보 설정
        const candidateInfo = this.KNOWN_CANDIDATES[candidateName];
        if (candidateInfo && !inferred.sgId) {
          inferred.sgId = candidateInfo.sgId;
          inferred.sgTypecode = candidateInfo.sgTypecode;
          inferred._inferred.sgId = `후보자에서 추론: ${candidateName} (${candidateInfo.sgId})`;
        }
      }

      // 정당명 추출
      const partyName = this.extractPartyName(queryText);
      if (partyName) {
        inferred._filterParty = partyName;
        inferred._inferred.filterParty = `정당: ${partyName}`;
      }
    }

    return inferred;
  }

  /**
   * 쿼리에서 후보자 이름 추출
   */
  private static extractCandidateName(text: string): string | null {
    const knownCandidates = Object.keys(this.KNOWN_CANDIDATES);
    for (const name of knownCandidates) {
      if (text.includes(name)) {
        return name;
      }
    }
    return null;
  }

  /**
   * 쿼리에서 정당명 추출
   */
  private static extractPartyName(text: string): string | null {
    for (const [fullName, aliases] of Object.entries(this.PARTY_PATTERNS)) {
      for (const alias of aliases) {
        if (text.includes(alias)) {
          return fullName;
        }
      }
      if (text.includes(fullName)) {
        return fullName;
      }
    }
    return null;
  }

  /**
   * 선거종류코드를 이름으로 변환 (public)
   */
  static getElectionTypeNamePublic(code: string): string {
    const names: Record<string, string> = {
      '1': '대통령선거',
      '2': '국회의원선거',
      '3': '시·도지사선거',
      '4': '구·시·군의장선거',
      '5': '시·도의원선거',
      '6': '구·시·군의원선거',
      '11': '교육감선거',
    };
    return names[code] || `선거종류 ${code}`;
  }

  /**
   * 최근 선거 정보 조회
   */
  static getRecentElection(sgId: string): { name: string; type: string } | undefined {
    return this.RECENT_ELECTIONS[sgId as keyof typeof this.RECENT_ELECTIONS];
  }
}
