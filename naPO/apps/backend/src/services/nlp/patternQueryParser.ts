import { ParsedQuery, NLQueryResponse } from '@/types/nlp.types';

/**
 * Pattern-based query parser as fallback when OpenAI is not available
 * Uses regex patterns and keywords to parse natural language queries
 */
export class PatternQueryParser {
  async parseQuery(query: string): Promise<NLQueryResponse> {
    const normalizedQuery = query.toLowerCase().trim();

    // Detect intent
    const intent = this.detectIntent(normalizedQuery);

    // Extract filters
    const filters = this.extractFilters(normalizedQuery);

    // Extract output format
    const output = this.extractOutputFormat(normalizedQuery);

    // Detect source
    const source = this.detectSource(normalizedQuery);

    const parsedQuery: ParsedQuery = {
      rawQuery: query,
      intent,
      confidence: this.calculateConfidence(normalizedQuery, intent, source),
      source,
      filters,
      output,
    };

    return {
      parsedQuery,
      explanation: this.generateExplanation(parsedQuery),
      suggestedActions: this.generateSuggestedActions(parsedQuery),
    };
  }

  private detectIntent(query: string): ParsedQuery['intent'] {
    // Fetch API keywords
    if (
      query.includes('데이터') ||
      query.includes('조회') ||
      query.includes('가져') ||
      query.includes('뽑') ||
      query.includes('검색')
    ) {
      return 'fetch_api';
    }

    // Crawl keywords
    if (query.includes('크롤') || query.includes('스크랩') || query.includes('다운로드')) {
      return 'crawl_site';
    }

    // PDF parsing keywords
    if (query.includes('pdf') || (query.includes('문서') && query.includes('파싱'))) {
      return 'parse_pdf';
    }

    // Analysis keywords
    if (query.includes('분석') || query.includes('통계') || query.includes('요약')) {
      return 'analyze_data';
    }

    // Export keywords
    if (query.includes('내보내') || query.includes('저장') || query.includes('다운로드')) {
      return 'export_data';
    }

    // Default to fetch
    return 'fetch_api';
  }

  private extractFilters(query: string): ParsedQuery['filters'] {
    const filters: ParsedQuery['filters'] = {};

    // Extract date range
    const dateRange = this.extractDateRange(query);
    if (dateRange) {
      filters.dateRange = dateRange;
    }

    // Extract region
    const region = this.extractRegion(query);
    if (region) {
      filters.region = region;
      // 지역 정보를 region 객체로도 설정
      filters.region = { sido: region };
    }

    // Extract keywords
    const keywords = this.extractKeywords(query);
    if (keywords.length > 0) {
      filters.keywords = keywords;
    }

    // Extract election info
    const election = this.extractElectionInfo(query);
    if (election) {
      filters.election = election;

      // sgId 추론 (API에 필요)
      if (election.year) {
        const sgId = this.inferElectionId(election.year, election.type);
        if (sgId) {
          filters.sgId = sgId;
        }
      }

      // sgTypecode 추론
      if (election.type) {
        const sgTypecode = this.getElectionTypeCode(election.type);
        if (sgTypecode) {
          filters.election.sgTypecode = sgTypecode;
        }
      }
    }

    return filters;
  }

  private extractDateRange(query: string): { start: string; end: string } | null {
    // Pattern: "YYYY년부터", "최근 N년", "지난 N년", "최근 N개월", "지난 N개월"

    // "최근 N개월" or "지난 N개월" (NEW)
    const recentMonths = query.match(/(?:최근|지난)\s*(\d+)\s*개월/);
    if (recentMonths && recentMonths[1]) {
      const months = parseInt(recentMonths[1]);
      const endDate = new Date();
      const startDate = new Date();
      startDate.setMonth(endDate.getMonth() - months);

      return {
        start: startDate.toISOString().split('T')[0] as string,
        end: endDate.toISOString().split('T')[0] as string,
      };
    }

    // "최근 N년" or "지난 N년"
    const recentYears = query.match(/(?:최근|지난)\s*(\d+)\s*년/);
    if (recentYears && recentYears[1]) {
      const years = parseInt(recentYears[1]);
      const endDate = new Date();
      const startDate = new Date();
      startDate.setFullYear(endDate.getFullYear() - years);

      return {
        start: startDate.toISOString().split('T')[0] as string,
        end: endDate.toISOString().split('T')[0] as string,
      };
    }

    // "YYYY년부터"
    const fromYear = query.match(/(\d{4})년\s*부터/);
    if (fromYear && fromYear[1]) {
      return {
        start: `${fromYear[1]}-01-01` as string,
        end: new Date().toISOString().split('T')[0] as string,
      };
    }

    // "YYYY년 ~ YYYY년"
    const yearRange = query.match(/(\d{4})년\s*~\s*(\d{4})년/);
    if (yearRange && yearRange[1] && yearRange[2]) {
      return {
        start: `${yearRange[1]}-01-01`,
        end: `${yearRange[2]}-12-31`,
      };
    }

    // Specific year "YYYY년"
    const specificYear = query.match(/(\d{4})년/);
    if (specificYear && specificYear[1]) {
      return {
        start: `${specificYear[1]}-01-01`,
        end: `${specificYear[1]}-12-31`,
      };
    }

    return null;
  }

  private extractRegion(query: string): string | undefined {
    // Common Korean regions
    const regions = [
      '서울',
      '부산',
      '대구',
      '인천',
      '광주',
      '대전',
      '울산',
      '세종',
      '경기',
      '강원',
      '충북',
      '충남',
      '전북',
      '전남',
      '경북',
      '경남',
      '제주',
      '강남',
      '강북',
      '강서',
      '송파',
      '마포',
      '용산',
      '종로',
      '중구',
      '서초',
    ];

    for (const region of regions) {
      if (query.includes(region)) {
        return region;
      }
    }

    return undefined;
  }

  private extractKeywords(query: string): string[] {
    const keywords: string[] = [];

    // Remove common words and extract meaningful terms
    const commonWords = [
      '데이터',
      '조회',
      '가져',
      '뽑',
      '보여',
      '주세요',
      '해주',
      '년',
      '월',
      '일',
    ];
    const words = query.split(/\s+/);

    for (const word of words) {
      if (word.length > 1 && !commonWords.includes(word) && !/^\d+$/.test(word)) {
        keywords.push(word);
      }
    }

    return keywords.slice(0, 5); // Limit to 5 keywords
  }

  private extractElectionInfo(query: string): ParsedQuery['filters']['election'] | undefined {
    if (!query.includes('선거') && !query.includes('공약') && !query.includes('후보')) {
      return undefined;
    }

    const election: NonNullable<ParsedQuery['filters']['election']> = {};

    // Extract year
    const yearMatch = query.match(/(\d{4})년/);
    if (yearMatch && yearMatch[1]) {
      election.year = parseInt(yearMatch[1]);
    }

    // Extract election type
    if (query.includes('대통령')) {
      election.type = '대통령선거';
    } else if (query.includes('총선') || query.includes('국회의원')) {
      election.type = '총선';
    } else if (query.includes('지방선거') || query.includes('시장') || query.includes('도지사')) {
      election.type = '지방선거';
    }

    // Extract position
    if (query.includes('시장')) {
      election.position = '시장';
    } else if (query.includes('도지사')) {
      election.position = '도지사';
    } else if (query.includes('구청장')) {
      election.position = '구청장';
    }

    return Object.keys(election).length > 0 ? election : undefined;
  }

  private extractOutputFormat(query: string): ParsedQuery['output'] {
    const output: ParsedQuery['output'] = {
      format: 'table', // Default format
    };

    // Detect format
    if (query.includes('csv')) {
      output.format = 'csv';
    } else if (query.includes('json')) {
      output.format = 'json';
    } else if (query.includes('엑셀') || query.includes('excel')) {
      output.format = 'excel';
    } else if (query.includes('표')) {
      output.format = 'table';
    } else if (query.includes('차트') || query.includes('그래프')) {
      output.format = 'chart';
    }
    // else: keep default 'table' format

    // Extract limit
    const limitMatch = query.match(/(\d+)\s*개/);
    if (limitMatch && limitMatch[1]) {
      output.limit = parseInt(limitMatch[1]);
    } else {
      output.limit = 100; // Default
    }

    return output;
  }

  private detectSource(query: string): ParsedQuery['source'] {
    const source: ParsedQuery['source'] = {
      type: 'unknown',
    };

    // Detect API sources - R-ONE (부동산)
    if (
      query.includes('부동산') ||
      query.includes('집값') ||
      query.includes('아파트') ||
      query.includes('r-one')
    ) {
      source.type = 'api';
      source.id = 'rone';
      return source;
    }

    // YouTube
    if (query.includes('유튜브') || query.includes('youtube')) {
      source.type = 'api';
      source.id = 'youtube';
      return source;
    }

    // 재정/경제통계
    if (query.includes('재정') || query.includes('경제통계')) {
      source.type = 'api';
      source.id = 'nabostats';
      return source;
    }

    // 선거 관련 - 세분화된 라우팅 (우선순위 중요!)
    // 1. 당선자/득표율 → public_data_winner
    if (
      query.includes('당선자') ||
      query.includes('당선인') ||
      query.includes('득표율') ||
      query.includes('득표수') ||
      (query.includes('당선') && !query.includes('공약'))
    ) {
      source.type = 'api';
      source.id = 'public_data_winner';
      return source;
    }

    // 2. 정당 공약/정책 → public_data_party_policy
    if (
      (query.includes('정당') && (query.includes('공약') || query.includes('정책'))) ||
      query.includes('주요정당') ||
      (query.includes('정당별') && query.includes('공약'))
    ) {
      source.type = 'api';
      source.id = 'public_data_party_policy';
      return source;
    }

    // 3. 후보자 목록 (공약 없이) → public_data_candidate
    if (
      (query.includes('후보자') && !query.includes('공약')) ||
      query.includes('후보 목록') ||
      query.includes('출마자')
    ) {
      source.type = 'api';
      source.id = 'public_data_candidate';
      return source;
    }

    // 4. 특정 후보 공약 → public_data_election (NEC Manifesto)
    if (
      query.includes('공약') ||
      (query.includes('후보') && query.includes('공약'))
    ) {
      source.type = 'api';
      source.id = 'public_data_election';
      return source;
    }

    // 5. 일반 선거 정보 → public_data_winner (기본)
    if (query.includes('선거')) {
      source.type = 'api';
      source.id = 'public_data_winner';
      return source;
    }

    // Detect crawler sources - set both id and crawlerType
    if (query.includes('선거정보도서관') || query.includes('선관위')) {
      source.type = 'crawler';
      source.id = 'nec_library';
      source.crawlerType = 'nec_library';
      return source;
    }

    return source;
  }

  /**
   * 선거 ID(sgId) 추론
   * 연도와 선거 유형으로 실제 선거 날짜 반환
   */
  private inferElectionId(year: number, electionType?: string): string | null {
    const electionDates: Record<string, Record<number, string>> = {
      '대통령선거': { 2022: '20220309', 2017: '20170509', 2012: '20121219' },
      '총선': { 2024: '20240410', 2020: '20200415', 2016: '20160413' },
      '지방선거': { 2022: '20220601', 2018: '20180613', 2014: '20140604' },
    };

    if (electionType && electionDates[electionType]?.[year]) {
      return electionDates[electionType][year];
    }

    // 연도만 있으면 가장 가능성 높은 선거 추론
    if (year === 2024) return '20240410'; // 총선
    if (year === 2022) return '20220601'; // 지방선거 (더 데이터 많음)
    if (year === 2020) return '20200415'; // 총선
    if (year === 2017) return '20170509'; // 대선

    return null;
  }

  /**
   * 선거 유형 코드(sgTypecode) 반환
   */
  private getElectionTypeCode(electionType?: string): string | null {
    const typeCodes: Record<string, string> = {
      '대통령선거': '1',
      '총선': '2',
      '국회의원': '2',
      '지방선거': '3',
      '시도지사': '3',
    };

    return electionType ? typeCodes[electionType] || null : null;
  }

  private calculateConfidence(
    query: string,
    intent: string,
    source: ParsedQuery['source']
  ): number {
    let confidence = 0.5; // Base confidence

    // Increase confidence if source is detected
    if (source.type !== 'unknown') {
      confidence += 0.2;
    }

    // Increase confidence if query is specific
    if (query.length > 10) {
      confidence += 0.1;
    }

    // Increase confidence if date range is present
    if (query.match(/\d{4}년/)) {
      confidence += 0.1;
    }

    // Increase confidence if region is present
    if (this.extractRegion(query)) {
      confidence += 0.1;
    }

    return Math.min(confidence, 1.0);
  }

  private generateExplanation(parsed: ParsedQuery): string {
    const parts: string[] = [];

    switch (parsed.intent) {
      case 'fetch_api':
        parts.push(`API에서 데이터를 가져옵니다`);
        if (parsed.source.id) {
          parts.push(`(소스: ${String(parsed.source.id)})`);
        }
        break;
      case 'crawl_site':
        parts.push(`웹사이트를 크롤링합니다`);
        if (parsed.source.id) {
          parts.push(`(${String(parsed.source.id)})`);
        }
        break;
      case 'parse_pdf':
        parts.push('PDF 문서를 파싱합니다');
        break;
      case 'analyze_data':
        parts.push('데이터를 분석합니다');
        break;
      case 'export_data':
        parts.push('데이터를 내보냅니다');
        break;
    }

    if (parsed.filters.dateRange) {
      parts.push(`기간: ${parsed.filters.dateRange.start} ~ ${parsed.filters.dateRange.end}`);
    }
    if (parsed.filters.region) {
      parts.push(`지역: ${parsed.filters.region}`);
    }
    if (parsed.output.format) {
      parts.push(`출력: ${parsed.output.format.toUpperCase()}`);
    }

    return parts.join(' | ');
  }

  private generateSuggestedActions(parsed: ParsedQuery): string[] {
    const actions: string[] = [];

    actions.push('⚠️ 패턴 매칭 모드로 작동 중입니다 (OpenAI 미사용)');

    if (parsed.confidence < 0.7) {
      actions.push('더 구체적인 조건을 추가하면 정확도가 향상됩니다');
    }

    if (parsed.source.type === 'unknown') {
      actions.push('데이터 소스를 명시해주세요 (예: R-ONE, 선거정보도서관)');
    }

    if (!parsed.filters.dateRange) {
      actions.push('기간을 지정하면 더 정확한 결과를 얻을 수 있습니다');
    }

    return actions;
  }
}
