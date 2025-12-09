/**
 * 중앙선거관리위원회 코드관리 API Adapter
 *
 * API 정보:
 * - 서비스명: 코드 정보 조회 서비스 (CommonCodeService)
 * - Base URL: http://apis.data.go.kr/9760000/CommonCodeService
 * - 인증: Service Key (공공데이터포털 발급)
 *
 * 주요 Endpoints:
 * 1. getCommonSgCodeList - 선거코드 조회
 * 2. getCommonGusigunCodeList - 시군구코드 조회
 * 3. getCommonSggCodeList - 선거구코드 조회
 * 4. getCommonPartyCodeList - 정당코드 조회
 * 5. getCommonJobCodeList - 직업코드 조회
 * 6. getCommonEduBckgrdCodeList - 학력코드 조회
 *
 * 응답 형식:
 * - response.header.resultCode: 결과코드 (00=정상, INFO-00=정상, INFO-03=데이터없음)
 * - response.body.items.item: 결과 데이터 배열
 * - response.body.totalCount: 전체 건수
 */
export class CommonCodeAdapter {
  /**
   * 선거종류코드 매핑
   */
  static readonly ELECTION_TYPE_CODES = {
    representative: '0',      // 대표선거명
    president: '1',          // 대통령선거
    national_assembly: '2',  // 국회의원선거
    governor: '3',           // 시·도지사선거
    mayor: '4',              // 구·시·군장선거
    provincial_council: '5', // 시·도의원선거
    local_council: '6',      // 구·시·군의회의원선거
    proportional_1: '7',     // 비례대표시·도의원선거
    proportional_2: '8',     // 비례대표구·시·군의회의원선거
    proportional_3: '9',     // 비례대표국회의원선거
    education_council: '10', // 교육의원선거
    superintendent: '11',    // 교육감선거
  } as const;

  /**
   * API 응답 정규화 (공통)
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
          data: items,
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
   * 선거코드 응답 정규화
   *
   * 응답 필드:
   * - sgId: 선거ID (YYYYMMDD)
   * - sgTypecode: 선거종류코드
   * - sgName: 선거명
   * - sgVotedate: 선거일
   */
  static normalizeElectionCodeResponse(data: any): any {
    const normalized = this.normalizeResponse(data);

    if (normalized.success && normalized.data) {
      normalized.data = normalized.data.map((item: any) => ({
        electionId: item.sgId,
        electionTypeCode: item.sgTypecode,
        electionName: item.sgName,
        voteDate: item.sgVotedate,
        _raw: item,
      }));
    }

    return normalized;
  }

  /**
   * 시군구코드 응답 정규화
   *
   * 응답 필드:
   * - wiwName: 읍면동명
   * - sdName: 시도명
   * - wOrder: 읍면동 순서
   */
  static normalizeDistrictCodeResponse(data: any): any {
    const normalized = this.normalizeResponse(data);

    if (normalized.success && normalized.data) {
      normalized.data = normalized.data.map((item: any) => ({
        districtName: item.wiwName,
        provinceName: item.sdName,
        order: item.wOrder,
        _raw: item,
      }));
    }

    return normalized;
  }

  /**
   * 선거구코드 응답 정규화
   *
   * 응답 필드:
   * - sggName: 선거구명
   * - sdName: 시도명
   * - wiwName: 읍면동명
   * - sggJungsu: 선거구정수
   * - sOrder: 선거구 순서
   */
  static normalizeConstituencyCodeResponse(data: any): any {
    const normalized = this.normalizeResponse(data);

    if (normalized.success && normalized.data) {
      normalized.data = normalized.data.map((item: any) => ({
        constituencyName: item.sggName,
        provinceName: item.sdName,
        districtName: item.wiwName,
        seatCount: item.sggJungsu,
        order: item.sOrder,
        _raw: item,
      }));
    }

    return normalized;
  }

  /**
   * 정당코드 응답 정규화
   *
   * 응답 필드:
   * - jdName: 정당명
   * - pOrder: 정당 순서
   */
  static normalizePartyCodeResponse(data: any): any {
    const normalized = this.normalizeResponse(data);

    if (normalized.success && normalized.data) {
      normalized.data = normalized.data.map((item: any) => ({
        partyName: item.jdName,
        order: item.pOrder,
        _raw: item,
      }));
    }

    return normalized;
  }

  /**
   * 직업코드 응답 정규화
   *
   * 응답 필드:
   * - jobId: 직업ID
   * - jobName: 직업명
   * - jOrder: 직업 순서
   */
  static normalizeJobCodeResponse(data: any): any {
    const normalized = this.normalizeResponse(data);

    if (normalized.success && normalized.data) {
      normalized.data = normalized.data.map((item: any) => ({
        jobId: item.jobId,
        jobName: item.jobName,
        order: item.jOrder,
        _raw: item,
      }));
    }

    return normalized;
  }

  /**
   * 학력코드 응답 정규화
   *
   * 응답 필드:
   * - eduId: 학력ID
   * - eduName: 학력명
   * - eOrder: 학력 순서
   */
  static normalizeEducationCodeResponse(data: any): any {
    const normalized = this.normalizeResponse(data);

    if (normalized.success && normalized.data) {
      normalized.data = normalized.data.map((item: any) => ({
        educationId: item.eduId,
        educationName: item.eduName,
        order: item.eOrder,
        _raw: item,
      }));
    }

    return normalized;
  }

  /**
   * 선거ID로 선거 정보 필터링
   * @param data 선거코드 배열
   * @param electionId 선거ID (예: "20220309")
   */
  static filterElectionById(data: any[], electionId: string): any | null {
    if (!data || data.length === 0) return null;
    return data.find((item) => item.electionId === electionId) || null;
  }

  /**
   * 선거명으로 선거 정보 필터링
   * @param data 선거코드 배열
   * @param keyword 검색 키워드 (예: "대통령", "2022")
   */
  static filterElectionByName(data: any[], keyword: string): any[] {
    if (!data || data.length === 0) return [];
    return data.filter((item) => item.electionName?.includes(keyword));
  }

  /**
   * 시도명으로 시군구 필터링
   * @param data 시군구코드 배열
   * @param provinceName 시도명 (예: "서울특별시")
   */
  static filterDistrictByProvince(data: any[], provinceName: string): any[] {
    if (!data || data.length === 0) return [];
    return data.filter((item) => item.provinceName === provinceName);
  }

  /**
   * 정당명으로 정당 필터링
   * @param data 정당코드 배열
   * @param keyword 검색 키워드 (예: "민주", "국민의힘")
   */
  static filterPartyByName(data: any[], keyword: string): any[] {
    if (!data || data.length === 0) return [];
    return data.filter((item) => item.partyName?.includes(keyword));
  }

  /**
   * 선거종류 텍스트를 코드로 변환
   */
  static mapElectionTypeToCode(type: string): string {
    const normalized = type.toLowerCase().replace(/\s+/g, '');

    if (normalized.includes('대통령') || normalized === 'president') {
      return this.ELECTION_TYPE_CODES.president;
    }
    if (normalized.includes('국회의원') || normalized === 'nationalassembly') {
      return this.ELECTION_TYPE_CODES.national_assembly;
    }
    if (normalized.includes('교육감') || normalized === 'superintendent') {
      return this.ELECTION_TYPE_CODES.superintendent;
    }
    if (normalized.includes('교육의원') || normalized === 'educationcouncil') {
      return this.ELECTION_TYPE_CODES.education_council;
    }
    if (normalized.includes('도지사') || normalized.includes('지사') || normalized === 'governor') {
      return this.ELECTION_TYPE_CODES.governor;
    }
    if (
      normalized.includes('시장') ||
      normalized.includes('군수') ||
      normalized.includes('구청장') ||
      normalized === 'mayor'
    ) {
      return this.ELECTION_TYPE_CODES.mayor;
    }
    if (normalized.includes('시도의원') || normalized === 'provincialcouncil') {
      return this.ELECTION_TYPE_CODES.provincial_council;
    }
    if (normalized.includes('시군구의회의원') || normalized === 'localcouncil') {
      return this.ELECTION_TYPE_CODES.local_council;
    }

    // 기본값: 대통령선거
    return this.ELECTION_TYPE_CODES.president;
  }

  /**
   * 선거종류 코드를 이름으로 변환
   */
  static mapElectionCodeToName(code: string): string {
    const codeMap: Record<string, string> = {
      '0': '대표선거명',
      '1': '대통령선거',
      '2': '국회의원선거',
      '3': '시·도지사선거',
      '4': '구·시·군장선거',
      '5': '시·도의원선거',
      '6': '구·시·군의회의원선거',
      '7': '비례대표시·도의원선거',
      '8': '비례대표구·시·군의회의원선거',
      '9': '비례대표국회의원선거',
      '10': '교육의원선거',
      '11': '교육감선거',
    };

    return codeMap[code] || '알 수 없는 선거';
  }

  /**
   * 파라미터 검증
   */
  static validateParams(params: Record<string, any>): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

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
}
