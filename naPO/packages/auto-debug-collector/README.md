# @napo/auto-debug-collector

자동 디버깅 오류 수집 시스템 - Gemini API를 사용하여 테스트 프롬프트를 생성하고 naPO에 자동 질의하여 엣지케이스 및 오류를 수집합니다.

## 목적

- LLM 기반 시스템의 확률적 응답을 자동으로 테스트
- 엣지케이스 및 오류 패턴 식별
- 양질의 시행착오 데이터 수집
- 재사용 가능한 모듈로 다른 앱에서도 활용 가능

## 설치

```bash
# 패키지 설치
pnpm install

# 빌드
pnpm build
```

## 사용법

### CLI 실행

```bash
# 기본 실행 (100 iterations)
npx tsx scripts/run-auto-debug.ts

# 옵션 사용
npx tsx scripts/run-auto-debug.ts --iterations 50 --rate 4 --verbose --cleanup
```

### 코드에서 사용

```typescript
import { AutoDebugCollector } from '@napo/auto-debug-collector';

const collector = new AutoDebugCollector({
  geminiApiKey: process.env.GEMINI_API_KEY!,
  napoBaseUrl: 'http://localhost:3001/api/v1',
  promptsPerMinute: 4,
  testTempDir: './test_temp',
  maxIterations: 100,
  domains: ['election', 'policy', 'candidate', 'party'],
  verbose: true,
});

// 시작
await collector.start();

// 통계 확인
const stats = collector.getStats();
console.log(stats);

// 정리
await collector.cleanup();
```

## 구성 요소

### AutoDebugCollector (메인 오케스트레이터)

전체 수집 프로세스를 조율합니다:
- 프롬프트 생성 → 테스트 실행 → 결과 분석 → CSV 저장

### PromptGenerator

Gemini API를 사용하여 다양한 테스트 프롬프트를 생성합니다:
- 선거 정보 질문
- 정당 정책 질문
- 후보자 관련 질문
- 엣지케이스 (모호한 질문, 오타, 복합 질문)

### QueryTester

생성된 프롬프트로 naPO API를 테스트합니다:
- Parse 단계: 자연어 → 구조화된 쿼리
- Execute 단계: 쿼리 실행 및 결과 수집

### ResultAnalyzer

테스트 결과를 분석하고 CSV로 저장합니다:
- 성공/실패 통계
- 인텐트/소스 매칭률
- 오류 패턴 식별
- 카테고리별 분석

### RateLimiter

API 호출 속도를 제어합니다:
- Gemini API: 분당 10회 제한
- Token bucket 알고리즘

## 출력 파일

실행 후 `test_temp/` 폴더에 다음 파일이 생성됩니다:

```
test_temp/
├── test_document_1st.csv    # 분석 결과 (메인 출력)
├── summary.json             # 요약 통계
├── prompts/                 # 생성된 프롬프트 JSON
│   ├── prompt_001.json
│   └── ...
├── responses/               # API 응답 JSON
│   ├── prompt_001.json
│   └── ...
└── logs/
    └── run.log              # 실행 로그
```

### CSV 컬럼

| 컬럼 | 설명 |
|------|------|
| test_id | 테스트 ID |
| timestamp | 실행 시간 |
| query | 생성된 질문 |
| category | 카테고리 (election, policy 등) |
| difficulty | 난이도 (easy, medium, hard, edge_case) |
| parse_success | 파싱 성공 여부 |
| parse_intent | 파싱된 인텐트 |
| parse_source | 파싱된 데이터 소스 |
| parse_confidence | 파싱 신뢰도 |
| parse_error | 파싱 오류 메시지 |
| parse_time_ms | 파싱 시간 (ms) |
| execute_success | 실행 성공 여부 |
| execute_row_count | 반환된 데이터 수 |
| execute_error | 실행 오류 메시지 |
| execute_time_ms | 실행 시간 (ms) |
| expected_intent | 예상 인텐트 |
| expected_source | 예상 데이터 소스 |
| intent_match | 인텐트 일치 여부 |
| source_match | 소스 일치 여부 |
| is_edge_case | 엣지케이스 여부 |
| prompt_file | 프롬프트 파일 경로 |
| response_file | 응답 파일 경로 |

## Rate Limit 계산

Gemini API는 분당 10회 호출 제한이 있습니다:

- 프롬프트 생성: 1회/batch (4개 프롬프트 생성)
- naPO Parse: 4회/batch (각 프롬프트 테스트)
- 총: 5회/batch

기본 설정 (4 prompts/min)에서는:
- 분당 약 8회 Gemini 호출 (여유분 2회)
- 시간당 약 240개 테스트 실행

## 커스터마이징

### 프롬프트 생성기 확장

```typescript
import { PromptGenerator } from '@napo/auto-debug-collector';

class MyPromptGenerator extends PromptGenerator {
  protected getSystemPrompt(): string {
    return `
      Custom system prompt for your domain...
    `;
  }
}
```

### 커스텀 카테고리 추가

```typescript
const collector = new AutoDebugCollector({
  // ...
  domains: ['election', 'policy', 'my_custom_category'],
});
```

## 환경 변수

| 변수 | 필수 | 설명 |
|------|------|------|
| GEMINI_API_KEY | ✓ | Gemini API 키 |
| NAPO_API_URL | - | naPO API URL (기본: http://localhost:3001/api/v1) |

## 라이센스

MIT
