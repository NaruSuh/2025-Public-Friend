import { QueryFilters } from '@/types/nlp.types';

/**
 * 중앙선거관리위원회 선거공약 정보 API Adapter
 *
 * API 정보:
 * - 서비스명: 선거공약 정보 조회 서비스 (ElecPrmsInfoInqireService)
 * - Endpoint: getCnddtElecPrmsInfoInqire (후보자 선거공약 정보 조회)
 * - Base URL: http://apis.data.go.kr/9760000/ElecPrmsInfoInqireService
 * - 인증: Service Key (공공데이터포털 발급)
 *
 * 주요 파라미터:
 * - sgId: 선거ID (예: 20220309)
 * - sgTypecode: 선거종류코드
 *   1: 대통령선거
 *   3: 시·도지사선거
 *   4: 구·시·군의장선거
 *   11: 교육감선거
 * - cnddtId: 후보자ID (후보자/당선인 정보 조회서비스에서 획득)
 *
 * 제약사항:
 * - 선거종료 전: 후보자 공약 정보 제공
 * - 선거종료 후: 당선인 공약만 제공
 * - 국회의원선거(2)는 선거공보 제출로 이 API에서 제공 안함
 * - 후보자가 공약 미제출 시 데이터 없을 수 있음
 */
export class NecManifestoAdapter {
  // 선거종류코드 매핑
  static readonly ELECTION_TYPE_CODES = {
    president: '1',          // 대통령선거
    governor: '3',           // 시·도지사선거
    mayor: '4',              // 구·시·군의장선거
    superintendent: '11',    // 교육감선거
  } as const;

  // 최근 주요 선거 ID 목록 (선거공약 API 지원 선거)
  static readonly RECENT_ELECTIONS = {
    '20220601': { name: '제8회 전국동시지방선거', type: '3' },
    '20220309': { name: '제20대 대통령선거', type: '1' },
    '20180613': { name: '제7회 전국동시지방선거', type: '3' },
    '20170509': { name: '제19대 대통령선거', type: '1' },
    '20140604': { name: '제6회 전국동시지방선거', type: '3' },
  } as const;

  // 유명 정치인 매핑 (후보자명 → 관련 선거 정보)
  static readonly KNOWN_CANDIDATES: Record<string, { name: string; sgId: string; sgTypecode: string }> = {
    '윤석열': { name: '윤석열', sgId: '20220309', sgTypecode: '1' },
    '이재명': { name: '이재명', sgId: '20220309', sgTypecode: '1' },
    '심상정': { name: '심상정', sgId: '20220309', sgTypecode: '1' },
    '안철수': { name: '안철수', sgId: '20220309', sgTypecode: '1' },
    '문재인': { name: '문재인', sgId: '20170509', sgTypecode: '1' },
    '홍준표': { name: '홍준표', sgId: '20170509', sgTypecode: '1' },
    '유승민': { name: '유승민', sgId: '20170509', sgTypecode: '1' },
    '오세훈': { name: '오세훈', sgId: '20220601', sgTypecode: '3' },
    '박형준': { name: '박형준', sgId: '20220601', sgTypecode: '3' },
    '김동연': { name: '김동연', sgId: '20220601', sgTypecode: '3' },
  };

  /**
   * QueryFilters를 중선관위 API 파라미터로 변환
   */
  static adaptFilters(filters: QueryFilters): Record<string, any> {
    const params: Record<string, any> = {
      pageNo: 1,
      numOfRows: 10,
      resultType: 'json',
    };

    // 선거 ID 추출 (날짜 범위에서)
    if (filters.dateRange?.start) {
      // "2022-03-09" → "20220309"
      params.sgId = filters.dateRange.start.replace(/-/g, '');
    }

    // 선거종류코드 추출 (필터의 election 정보 또는 키워드에서)
    if (filters.election?.type) {
      params.sgTypecode = this.mapElectionType(filters.election.type);
    } else if (filters.keywords) {
      // 키워드에서 선거 종류 추론
      const keywords = filters.keywords.join(' ');
      if (keywords.includes('대통령')) {
        params.sgTypecode = this.ELECTION_TYPE_CODES.president;
      } else if (keywords.includes('지사') || keywords.includes('도지사')) {
        params.sgTypecode = this.ELECTION_TYPE_CODES.governor;
      } else if (keywords.includes('시장') || keywords.includes('군수') || keywords.includes('구청장')) {
        params.sgTypecode = this.ELECTION_TYPE_CODES.mayor;
      } else if (keywords.includes('교육감')) {
        params.sgTypecode = this.ELECTION_TYPE_CODES.superintendent;
      }
    }

    // 후보자ID는 별도로 제공되어야 함 (custom 필터에서)
    if (filters.custom?.cnddtId) {
      params.cnddtId = filters.custom.cnddtId;
    }

    // 지역명은 후보자 조회 시 필요 (이 API에서는 직접 사용 안함)
    if (filters.region) {
      params._regionFilter = filters.region;
    }

    return params;
  }

  /**
   * 선거 종류 텍스트를 코드로 매핑
   */
  private static mapElectionType(type: string): string {
    const normalized = type.toLowerCase().replace(/\s+/g, '');

    if (normalized.includes('대통령') || normalized === 'president') {
      return this.ELECTION_TYPE_CODES.president;
    }
    if (normalized.includes('교육감') || normalized === 'superintendent') {
      return this.ELECTION_TYPE_CODES.superintendent;
    }
    if (normalized.includes('도지사') || normalized.includes('지사') || normalized === 'governor') {
      return this.ELECTION_TYPE_CODES.governor;
    }
    // Check for 구시군의장 (mayor/district head) - must check full pattern
    if (
      normalized.includes('구시군의장') ||
      normalized.includes('시군구의장') ||
      normalized.includes('시장') ||
      normalized.includes('군수') ||
      normalized.includes('구청장') ||
      normalized === 'mayor'
    ) {
      return this.ELECTION_TYPE_CODES.mayor;
    }

    // 기본값: 대통령선거
    return this.ELECTION_TYPE_CODES.president;
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

    if (!params.sgTypecode) {
      errors.push('sgTypecode (선거종류코드) is required. Valid values: 1(대통령), 3(시도지사), 4(구시군의장), 11(교육감)');
    } else {
      const validCodes = ['1', '3', '4', '11'];
      if (!validCodes.includes(params.sgTypecode)) {
        errors.push(`Invalid sgTypecode: ${params.sgTypecode}. Must be one of: ${validCodes.join(', ')}`);
      }
    }

    if (!params.cnddtId) {
      errors.push('cnddtId (후보자ID) is required. Must be obtained from candidate info service');
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
              message: resultMsg,
            },
          };
        }
      }

      // 정상 응답
      if (response.body?.items) {
        const items = Array.isArray(response.body.items.item)
          ? response.body.items.item
          : [response.body.items.item];

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
   * 개별 아이템 정규화
   */
  private static normalizeItem(item: any): any {
    // 공약 정보 추출 (prmsOrd1~10, prmsTitle1~10, prmsCont1~10)
    const pledges: Array<{
      order: number;
      realm?: string;
      title: string;
      content?: string;
    }> = [];

    const prmsCnt = parseInt(item.prmsCnt || '0');
    for (let i = 1; i <= Math.min(prmsCnt, 10); i++) {
      const order = item[`prmsOrd${i}`];
      const realm = item[`prmsRealmName${i}`];
      const title = item[`prmsTitle${i}`];
      const content = item[`prmsCont${i}`];

      if (title) {
        pledges.push({
          order: parseInt(order || i),
          realm,
          title,
          content,
        });
      }
    }

    return {
      // 기본 정보
      electionId: item.sgId,
      electionType: item.sgTypecode,
      candidateId: item.cnddtId,

      // 선거구 정보
      district: item.sggName,
      sido: item.sidoName,
      sigungu: item.wiwName,

      // 후보자 정보
      party: item.partyName,
      nameKr: item.krName,
      nameCn: item.cnName,

      // 공약 정보
      pledgeCount: prmsCnt,
      pledges,

      // 원본 데이터 보존
      _raw: item,
    };
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
   * 누락된 파라미터 추론
   */
  static inferMissingParams(
    params: Record<string, any>,
    context?: { keywords?: string[]; query?: string }
  ): Record<string, any> {
    const inferred = { ...params };

    // 키워드에서 후보자명 추출 및 선거 정보 추론
    if (context?.keywords) {
      const text = context.keywords.join(' ');

      // 알려진 후보자에서 선거 정보 추론
      for (const [name, info] of Object.entries(this.KNOWN_CANDIDATES)) {
        if (text.includes(name)) {
          if (!inferred.sgId) {
            inferred.sgId = info.sgId;
            inferred._inferred = inferred._inferred || {};
            inferred._inferred.sgId = `후보자 "${name}"으로부터 추론: ${this.RECENT_ELECTIONS[info.sgId as keyof typeof this.RECENT_ELECTIONS]?.name || info.sgId}`;
          }
          if (!inferred.sgTypecode) {
            inferred.sgTypecode = info.sgTypecode;
            inferred._inferred = inferred._inferred || {};
            inferred._inferred.sgTypecode = `후보자 "${name}"으로부터 추론`;
          }
          inferred._candidateName = name;
          break;
        }
      }

      // 연도 + 선거 종류로 추론
      if (!inferred.sgId) {
        if (text.includes('2022') && text.includes('대선')) {
          inferred.sgId = '20220309';
          inferred.sgTypecode = '1';
          inferred._inferred = { ...inferred._inferred, sgId: '키워드 "2022 대선"으로부터 추론' };
        } else if (text.includes('2022') && text.includes('지방')) {
          inferred.sgId = '20220601';
          inferred.sgTypecode = '3';
          inferred._inferred = { ...inferred._inferred, sgId: '키워드 "2022 지방"으로부터 추론' };
        } else if (text.includes('2017') && text.includes('대선')) {
          inferred.sgId = '20170509';
          inferred.sgTypecode = '1';
          inferred._inferred = { ...inferred._inferred, sgId: '키워드 "2017 대선"으로부터 추론' };
        }
      }

      // "최근" 키워드 처리
      if (!inferred.sgId && text.includes('최근')) {
        if (text.includes('대선') || text.includes('대통령')) {
          inferred.sgId = '20220309';
          inferred.sgTypecode = '1';
        } else {
          inferred.sgId = '20220601'; // 기본: 최근 지방선거
          inferred.sgTypecode = '3';
        }
        inferred._inferred = { ...inferred._inferred, sgId: '키워드 "최근"으로부터 추론' };
      }
    }

    // sgId가 있지만 sgTypecode가 없으면 선거 정보에서 추론
    if (inferred.sgId && !inferred.sgTypecode) {
      const electionInfo = this.RECENT_ELECTIONS[inferred.sgId as keyof typeof this.RECENT_ELECTIONS];
      if (electionInfo) {
        inferred.sgTypecode = electionInfo.type;
        inferred._inferred = inferred._inferred || {};
        inferred._inferred.sgTypecode = `선거 ID ${inferred.sgId}로부터 추론`;
      }
    }

    // cnddtId가 없으면 API Chain이 필요함을 표시
    if (!inferred.cnddtId) {
      inferred._needsCandidateLookup = true;
      inferred._inferred = inferred._inferred || {};
      inferred._inferred.cnddtId = '후보자 ID가 필요합니다. API Chain을 통해 후보자 정보를 먼저 조회합니다.';
    }

    return inferred;
  }

  /**
   * 알려진 후보자 목록 반환
   */
  static getKnownCandidates(): string[] {
    return Object.keys(this.KNOWN_CANDIDATES);
  }

  /**
   * 선거 ID가 이 API에서 지원되는지 확인
   * 국회의원선거(2)는 지원 안함
   */
  static isElectionSupported(sgId: string, sgTypecode: string): boolean {
    const validCodes = ['1', '3', '4', '11'];
    return validCodes.includes(sgTypecode);
  }
}
