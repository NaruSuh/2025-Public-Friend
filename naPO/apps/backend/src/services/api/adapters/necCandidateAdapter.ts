import { QueryFilters } from '@/types/nlp.types';

/**
 * 중앙선거관리위원회 후보자 정보 조회 API Adapter
 *
 * API 정보:
 * - 서비스명: 후보자 정보 조회 서비스 (PofelcddInfoInqireService)
 * - Endpoint: getPofelcddRegistSttusInfoInqire (후보자 정보 조회)
 * - Base URL: http://apis.data.go.kr/9760000/PofelcddInfoInqireService
 * - 인증: Service Key (공공데이터포털 발급)
 *
 * 주요 파라미터:
 * - sgId: 선거ID (예: 20220309)
 * - sgTypecode: 선거종류코드 (1=대통령, 3=시도지사, 4=구시군의장, 11=교육감)
 * - sggName: 선거구명 (옵션)
 * - sdName: 시도명 (옵션)
 *
 * 응답 필드:
 * - huboid: 후보자ID (10자리) ⚠️ 공약 API의 cnddtId와 매핑됨
 * - name: 한글성명
 * - jdName: 정당명
 * - giho: 기호
 *
 * 제약사항:
 * - 선거 종료 후 후보자 주소는 제공되지 않음
 * - 실시간으로 정보 변경 가능
 */
export class NecCandidateAdapter {
  // 선거종류코드 매핑 (NecManifestoAdapter와 동일)
  static readonly ELECTION_TYPE_CODES = {
    president: '1',          // 대통령선거
    governor: '3',           // 시·도지사선거
    mayor: '4',              // 구·시·군의장선거
    superintendent: '11',    // 교육감선거
  } as const;

  /**
   * QueryFilters를 후보자 API 파라미터로 변환
   */
  static adaptFilters(filters: QueryFilters): Record<string, any> {
    const params: Record<string, any> = {
      pageNo: 1,
      numOfRows: 100, // 후보자가 많을 수 있으므로 넉넉하게
      resultType: 'json',
    };

    // 선거 ID 추출 (날짜 범위에서)
    if (filters.dateRange?.start) {
      // "2022-03-09" → "20220309"
      params.sgId = filters.dateRange.start.replace(/-/g, '');
    }

    // 선거종류코드 추출
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

    // 선거구명 (옵션)
    if (filters.region) {
      // 지역명을 선거구명 또는 시도명으로 설정
      // 대통령 선거: sggName="대한민국", sdName="전국"
      if (params.sgTypecode === '1') {
        params.sggName = '대한민국';
        params.sdName = '전국';
      } else {
        // 지방선거: 지역명을 시도명으로 설정
        // region이 string 또는 object일 수 있으므로 타입 가드 적용
        if (typeof filters.region === 'string') {
          params.sdName = this.extractSdName(filters.region);
        } else if (filters.region.sido) {
          params.sdName = this.extractSdName(filters.region.sido);
        } else if (filters.region.sigungu) {
          params.sdName = this.extractSdName(filters.region.sigungu);
        }
      }
    }

    return params;
  }

  /**
   * 선거 종류 텍스트를 코드로 매핑 (NecManifestoAdapter와 동일)
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
   * 지역명에서 시도명 추출
   */
  private static extractSdName(region: string): string {
    // 시도명 목록
    const provinces = [
      '서울특별시', '부산광역시', '대구광역시', '인천광역시',
      '광주광역시', '대전광역시', '울산광역시', '세종특별자치시',
      '경기도', '강원도', '충청북도', '충청남도',
      '전라북도', '전라남도', '경상북도', '경상남도',
      '제주특별자치도'
    ];

    // 시도명 약칭 매핑
    const provinceAbbr: Record<string, string> = {
      '서울': '서울특별시',
      '부산': '부산광역시',
      '대구': '대구광역시',
      '인천': '인천광역시',
      '광주': '광주광역시',
      '대전': '대전광역시',
      '울산': '울산광역시',
      '세종': '세종특별자치시',
      '경기': '경기도',
      '강원': '강원도',
      '충북': '충청북도',
      '충남': '충청남도',
      '전북': '전라북도',
      '전남': '전라남도',
      '경북': '경상북도',
      '경남': '경상남도',
      '제주': '제주특별자치도',
    };

    // 정확한 시도명 매칭
    for (const province of provinces) {
      if (region.includes(province)) {
        return province;
      }
    }

    // 약칭 매칭
    for (const [abbr, fullName] of Object.entries(provinceAbbr)) {
      if (region.includes(abbr)) {
        return fullName;
      }
    }

    // 매칭 실패 시 원본 반환
    return region;
  }

  /**
   * 응답에서 후보자 이름으로 필터링
   * @param data 후보자 목록 배열
   * @param candidateName 검색할 후보자 이름 (예: "윤석열", "이재명")
   * @param partyName 정당명 (옵션, 동명이인 구분용)
   * @returns 매칭된 후보자 정보 또는 null
   */
  static filterByName(
    data: any[],
    candidateName: string,
    partyName?: string
  ): any | null {
    if (!data || data.length === 0) {
      return null;
    }

    // 이름으로 필터링
    const candidates = data.filter((item) => {
      const name = item.name || item.huboCNm || '';
      return name.includes(candidateName);
    });

    if (candidates.length === 0) {
      return null;
    }

    // 동명이인이 있고 정당명이 제공된 경우 정당명으로 추가 필터링
    if (candidates.length > 1 && partyName) {
      const candidateWithParty = candidates.find((item) => {
        const party = item.jdName || item.partyName || '';
        return party.includes(partyName);
      });

      if (candidateWithParty) {
        return candidateWithParty;
      }
    }

    // 첫 번째 매칭 후보자 반환
    return candidates[0];
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
   * 개별 후보자 아이템 정규화
   */
  private static normalizeItem(item: any): any {
    return {
      // 핵심 ID 필드 (공약 API로 전달할 때 사용)
      huboid: item.huboid, // ⚠️ 이 값을 공약 API의 cnddtId로 사용
      candidateId: item.huboid, // 별칭

      // 선거 정보
      electionId: item.sgId,
      electionType: item.sgTypecode,

      // 선거구 정보
      district: item.sggName,
      sido: item.sdName,
      sigungu: item.wiwName,

      // 후보자 기본 정보
      ballotNumber: item.giho, // 기호
      ballotDetail: item.gihoSangse, // 기호상세 (구시군의원)
      party: item.jdName, // 정당명
      nameKr: item.name, // 한글성명
      nameHanja: item.hanjaName, // 한자성명

      // 개인 정보
      gender: item.gender,
      birthday: item.birthday,
      age: item.age,
      address: item.addr,

      // 경력 정보
      jobId: item.jobId,
      job: item.job,
      educationId: item.eduId,
      education: item.edu,
      career1: item.career1,
      career2: item.career2,

      // 등록 상태
      status: item.status, // 등록, 사퇴, 사망, 등록무효

      // 원본 데이터 보존
      _raw: item,
    };
  }

  /**
   * huboid를 cnddtId로 매핑
   * (두 필드는 동일한 후보자ID를 나타내지만 API마다 필드명이 다름)
   */
  static mapHuboidToCnddtId(huboid: string): string {
    return huboid;
  }
}
