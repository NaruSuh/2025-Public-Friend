/**
 * Auto Debug Collector Configuration
 */

import { AutoDebugConfig, PromptCategory, GeminiModelConfig } from './types';

// Default configuration
// Rate limit reduced from 4 to 3 prompts/min to avoid Gemini API rate limiting
export const DEFAULT_CONFIG: Partial<AutoDebugConfig> = {
  promptsPerMinute: 3,
  testTempDir: './test_temp',
  maxIterations: 100,
  domains: ['election', 'policy', 'candidate', 'party'] as PromptCategory[],
  verbose: false,
};

// Gemini Model Configuration
// Primary: 2.0 Flash (lower token usage)
// Fallback: 2.5 Flash (when 2.0 quota exceeded)
export const DEFAULT_GEMINI_CONFIG: GeminiModelConfig = {
  primaryModel: 'gemini-2.0-flash',
  fallbackModel: 'gemini-2.5-flash-preview-05-20',
  enableFallback: true,
  primaryCooldownMs: 60000, // 1 minute cooldown before retrying primary
};

// Prompt generation system prompt template
// Improved with clearer source mapping rules for better intent/source matching
export const PROMPT_GENERATION_SYSTEM = `당신은 한국 선거 및 정책 데이터 시스템의 QA 테스터입니다.
다양한 난이도와 카테고리의 사용자 질문을 생성해주세요.

## 데이터 소스 선택 규칙 (중요!)
다음 규칙에 따라 expectedSource를 정확히 선택하세요:

1. **public_data_party_policy** - 정당별 정책/공약 조회
   - 키워드: "정당 공약", "정책 방향", "주요정당", "민주당 정책", "국민의힘 공약"
   - 예: "더불어민주당의 복지 정책", "국민의힘 경제 공약"

2. **public_data_election** - 특정 후보자의 선거 공약 조회
   - 키워드: 특정 후보자 이름 + "공약", "선거 공약"
   - 예: "윤석열 후보의 부동산 공약", "이재명 후보 정책"
   - 주의: 후보자 이름이 명시되어야 함

3. **public_data_winner** - 당선자/선거 결과 조회
   - 키워드: "당선자", "당선인", "선거 결과", "득표율", "투표율"
   - 예: "2022년 지방선거 당선자", "서울시장 당선인", "최근 선거 결과"
   - 주의: 선거 결과, 투표율, 득표 관련은 모두 여기!

4. **public_data_candidate** - 후보자 정보/목록 조회
   - 키워드: "후보자 목록", "후보자 정보", "비례대표 후보"
   - 예: "2024년 총선 후보자 목록", "국민의힘 비례대표 후보"

## 인텐트 선택 규칙
- **fetch_api**: 데이터 조회 (95% 이상의 경우)
- **analyze_data**: "분석", "비교", "추이" 키워드가 있을 때
  - 예: "투표율 변화 추이", "정당별 정책 비교 분석"
- **crawl_site**: 웹사이트 크롤링이 필요할 때 (거의 없음)
- **parse_pdf**: PDF 파싱 (거의 없음)

## 선거 일정 정보
- 2024년 총선: 20240410
- 2022년 지방선거: 20220601
- 2022년 대선: 20220309
- 2020년 총선: 20200415
- 2018년 지방선거: 20180613

## 카테고리별 예시
1. **election** (선거 결과/정보):
   - "2022년 지방선거 서울시장 당선자" → public_data_winner
   - "2024년 총선 결과" → public_data_winner
   - "최근 대선 투표율" → public_data_winner

2. **policy** (정당 정책):
   - "국민의힘 경제 공약" → public_data_party_policy
   - "민주당 복지 정책" → public_data_party_policy
   - "정의당 정책 방향" → public_data_party_policy

3. **candidate** (후보자 관련):
   - "윤석열 후보 공약" → public_data_election
   - "이재명 정책 요약" → public_data_election
   - "2024 총선 후보자 목록" → public_data_candidate

4. **party** (정당 정보):
   - "더불어민주당 정보" → public_data_party_policy

5. **edge_case** (모호/복합 질문):
   - "공약 알려줘" → public_data_party_policy
   - "국힘 정책 좀" → public_data_party_policy

## 출력 형식
반드시 다음 JSON 배열 형식으로만 출력하세요 (마크다운 코드블록 없이):
[
  {
    "query": "생성된 한국어 질문",
    "category": "election|policy|candidate|party|edge_case",
    "difficulty": "easy|medium|hard|edge_case",
    "expectedIntent": "fetch_api|analyze_data",
    "expectedSource": "public_data_party_policy|public_data_election|public_data_candidate|public_data_winner"
  }
]`;

// CSV header for analysis output
export const CSV_HEADER = [
  'test_id',
  'timestamp',
  'query',
  'category',
  'difficulty',
  'parse_success',
  'parse_intent',
  'parse_source',
  'parse_confidence',
  'parse_error',
  'parse_time_ms',
  'execute_success',
  'execute_row_count',
  'execute_error',
  'execute_time_ms',
  'expected_intent',
  'expected_source',
  'intent_match',
  'source_match',
  'is_edge_case',
  'prompt_file',
  'response_file',
].join(',');

// Directory structure
export const DIRS = {
  prompts: 'prompts',
  responses: 'responses',
  logs: 'logs',
};

// File names
export const FILES = {
  analysisCSV: 'test_document_1st.csv',
  summaryJSON: 'summary.json',
  runLog: 'run.log',
};
