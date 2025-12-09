import { env } from '@/config/env';
import {
  ParsedQuery,
  NLQueryResponse,
  QueryIntent,
  QueryFilters,
  OutputConfig,
} from '@/types/nlp.types';
import { ApiRegistry } from '@/config/apis';
import { CrawlerFactory } from '@/services/crawler/crawlerFactory';
import { PatternQueryParser } from './patternQueryParser';
import { GeminiClient } from '@/lib/geminiClient';
import { logger } from '@/config/logger';

export class NLQueryEngine {
  private gemini: GeminiClient | null;
  private fallbackParser: PatternQueryParser;

  constructor() {
    this.fallbackParser = new PatternQueryParser();

    // Gemini를 우선 사용
    if (env.GEMINI_API_KEY && env.GEMINI_API_KEY.length > 20) {
      logger.info('Using Gemini API for natural language queries');
      this.gemini = new GeminiClient(env.GEMINI_API_KEY, {
        maxRetries: 3,
        initialDelayMs: 1000,
        maxDelayMs: 30000,
      });
    } else {
      logger.warn('Gemini API key not configured - using pattern matching fallback');
      this.gemini = null;
    }
  }

  async isAvailable(): Promise<boolean> {
    return this.gemini !== null;
  }

  async parseQuery(naturalLanguageQuery: string): Promise<NLQueryResponse> {
    if (this.gemini) {
      try {
        return await this.parseQueryWithGemini(naturalLanguageQuery);
      } catch (error: any) {
        logger.error('Gemini API error, falling back to pattern matching:', { error: error.message });
        return await this.fallbackParser.parseQuery(naturalLanguageQuery);
      }
    }

    logger.debug('Using pattern-based query parser (Gemini unavailable)');
    return await this.fallbackParser.parseQuery(naturalLanguageQuery);
  }

  private async parseQueryWithGemini(naturalLanguageQuery: string): Promise<NLQueryResponse> {
    if (!this.gemini) {
      throw new Error('Gemini not initialized');
    }

    const systemPrompt = this.buildSystemPrompt();

    // Gemini API 호출
    const parsed = await this.gemini.generateJSON({
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: naturalLanguageQuery },
      ],
      temperature: 0.3,
    }) as ParsedQuery;

    parsed.rawQuery = naturalLanguageQuery;

    return {
      parsedQuery: parsed,
      explanation: this.generateExplanation(parsed),
      suggestedActions: this.generateSuggestedActions(parsed),
    };
  }

  private buildSystemPrompt(): string {
    return `당신은 한국 정책/선거 데이터 시스템의 자연어 쿼리 파서입니다.
마크다운 코드블록이나 설명 없이 오직 유효한 JSON만 출력하세요.

## 역할 및 경계
- 입력: 한국어 자연어 질의
- 출력: 구조화된 ParsedQuery JSON
- 직접 API를 호출하지 않고, API 호출에 필요한 파라미터를 추출합니다

## 유효한 인텐트 (이것만 사용)
- "fetch_api": 정부 API에서 데이터 조회 (기본값, 95% 이상)
- "crawl_site": 웹사이트 크롤링
- "parse_pdf": PDF 파싱
- "analyze_data": 데이터 분석 (미구현)
- "export_data": 데이터 내보내기 (미구현)

## 데이터 소스 (중요!)

### 소스 선택 의사결정 트리:
1. "당선자", "당선인", "선거 결과", "득표율", "투표율" → public_data_winner
2. 특정 후보자 이름 + "공약" (예: "윤석열 공약") → public_data_election
3. "후보자 목록", "후보자 정보" → public_data_candidate
4. "정당 공약", "정당 정책", "민주당/국힘 정책" → public_data_party_policy
5. "부동산", "아파트 가격", "매매 시세" → rone
6. "예산", "재정" → nabostats

### 소스 상세:
- "public_data_winner": 당선인 정보 (선거 결과, 득표율, 당선자)
- "public_data_election": 특정 후보자 공약 (cnddtId 필요)
- "public_data_party_policy": 정당별 정책/공약
- "public_data_candidate": 후보자 정보/목록
- "rone": 부동산 통계
- "nabostats": 예산/재정 통계

## 한국 선거 날짜 (sgId로 사용)
- 2024 총선: 20240410 (국회의원, sgTypecode: 2)
- 2022 지방선거: 20220601 (시도지사, sgTypecode: 3)
- 2022 대선: 20220309 (대통령, sgTypecode: 1)
- 2020 총선: 20200415 (국회의원, sgTypecode: 2)
- 2018 지방선거: 20180613 (시도지사, sgTypecode: 3)
- 2017 대선: 20170509 (대통령, sgTypecode: 1)

## 선거종류코드 (sgTypecode)
- "1": 대통령선거
- "2": 국회의원선거
- "3": 시도지사선거
- "4": 구시군의장선거
- "5": 시도의원선거
- "6": 구시군의원선거
- "11": 교육감선거

## 응답 형식
{
  "intent": "fetch_api",
  "confidence": 0.95,
  "source": {
    "type": "api",
    "id": "public_data_winner"
  },
  "filters": {
    "sgId": "20220601",
    "dateRange": { "start": "20220601", "end": "20220601" },
    "election": { "type": "지방선거", "year": 2022, "sgTypecode": "3" },
    "keywords": ["당선자", "서울시장"]
  },
  "output": { "format": "table", "limit": 100 }
}

## Few-shot 예시

### 예시 1: 당선인 조회
입력: "2022년 지방선거 서울시장 당선자"
출력:
{
  "intent": "fetch_api",
  "confidence": 0.95,
  "source": { "type": "api", "id": "public_data_winner" },
  "filters": {
    "sgId": "20220601",
    "dateRange": { "start": "20220601", "end": "20220601" },
    "election": { "type": "지방선거", "year": 2022, "sgTypecode": "3" },
    "region": { "sido": "서울" },
    "keywords": ["당선자", "서울시장"]
  },
  "output": { "format": "table", "limit": 100 }
}

### 예시 2: 정당 정책 조회
입력: "국민의힘 경제 공약"
출력:
{
  "intent": "fetch_api",
  "confidence": 0.9,
  "source": { "type": "api", "id": "public_data_party_policy" },
  "filters": {
    "sgId": "20220601",
    "partyName": "국민의힘",
    "keywords": ["경제", "공약"]
  },
  "output": { "format": "table", "limit": 100 }
}

### 예시 3: 특정 후보자 공약
입력: "윤석열 대선 공약"
출력:
{
  "intent": "fetch_api",
  "confidence": 0.9,
  "source": { "type": "api", "id": "public_data_election" },
  "filters": {
    "sgId": "20220309",
    "dateRange": { "start": "20220309", "end": "20220309" },
    "election": { "type": "대통령선거", "year": 2022, "sgTypecode": "1" },
    "keywords": ["윤석열", "공약"]
  },
  "output": { "format": "table", "limit": 100 }
}

### 예시 4: 모호한 질문 (정당 정책으로 기본 라우팅)
입력: "공약 알려줘"
출력:
{
  "intent": "fetch_api",
  "confidence": 0.6,
  "source": { "type": "api", "id": "public_data_party_policy" },
  "filters": {
    "sgId": "20220601",
    "keywords": ["공약"]
  },
  "output": { "format": "table", "limit": 100 }
}

### 예시 5: 선거 결과/투표율
입력: "2024년 총선 투표율"
출력:
{
  "intent": "fetch_api",
  "confidence": 0.95,
  "source": { "type": "api", "id": "public_data_winner" },
  "filters": {
    "sgId": "20240410",
    "dateRange": { "start": "20240410", "end": "20240410" },
    "election": { "type": "국회의원선거", "year": 2024, "sgTypecode": "2" },
    "keywords": ["투표율", "총선"]
  },
  "output": { "format": "table", "limit": 100 }
}

## 중요 규칙
1. "분석", "요약" 키워드가 있어도 intent는 "fetch_api" 사용 (analyze_data 미구현)
2. 선거 날짜는 반드시 위 목록에서 정확한 값 사용
3. "최근" → 해당 선거 종류의 가장 최근 날짜 사용
4. 모호한 경우 confidence를 낮추고 (0.6-0.7) public_data_party_policy로 기본 라우팅
5. 키워드에 후보자 이름이 있으면 해당 이름을 keywords에 포함`;
  }

  private generateExplanation(parsed: ParsedQuery): string {
    const parts: string[] = [];
    if (parsed.filters.dateRange) {
      parts.push(`기간: ${parsed.filters.dateRange.start} ~ ${parsed.filters.dateRange.end}`);
    }
    if (parsed.filters.region) {
      parts.push(`지역: ${parsed.filters.region}`);
    }
    return parts.join(' | ');
  }

  private generateSuggestedActions(parsed: ParsedQuery): string[] {
    return [];
  }

  async analyzeData(data: any[], query: string): Promise<string> {
    if (!this.gemini) {
      return JSON.stringify({ message: 'Gemini 미사용', totalRecords: data.length }, null, 2);
    }
    return 'Analysis result';
  }
}
