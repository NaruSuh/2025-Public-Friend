# 🏛️ naPO
(naru Public Organizor)
공공/정책/ESG 데이터를 체계적으로 수집, 분석, 출력하는 범용 데이터 수집 플랫폼

## Release Note

### Recent Updates

#### Code Quality & Type Safety
- TypeScript strict mode 활성화 (frontend/backend 전체)
- `strictNullChecks`, `noImplicitAny`, `noUncheckedIndexedAccess` 등 엄격한 타입 검사 적용
- 모든 타입 에러 수정 완료 (null 체크, 타입 명시, static method 참조 등)

#### Test Coverage
- Backend: Jest 기반 단위/통합 테스트 32개 추가
  - `encryption.ts` 암호화 라이브러리 테스트 (17개)
  - `auth.routes.ts` 인증 API 테스트 (7개)
  - Rate limiter 미들웨어 테스트 (6개)
  - API 통합 스모크 테스트 (2개)
- Frontend: Vitest 기반 컴포넌트/훅 테스트 35개 추가
  - Zustand store 테스트 (appStore 11개, queryStore 18개)
  - useExport 훅 테스트 (6개)

#### Error Handling
- 전역 에러 핸들러 강화 (`errorHandler.ts`)
  - JSON 파싱 에러, Prisma DB 에러, 일반 API 에러 구분 처리
  - Production 환경에서 내부 구현 세부사항 숨김
- `asyncHandler` 유틸리티 추가 (비동기 라우트 try-catch 보일러플레이트 제거)
- `createApiError` 헬퍼 함수 추가

#### Documentation (JSDoc)
- 핵심 모듈 JSDoc 문서화
  - `BaseParser` 추상 클래스 및 `PdfParser` 인터페이스
  - `encryption.ts` 암호화 유틸리티 (encrypt, decrypt, hash, verifyHash, maskSensitiveData)
  - `useExport` 훅 (CSV, JSON, Excel 내보내기)
  - `errorHandler` 미들웨어

#### Linting & Code Style
- ESLint 설정 추가 (`.eslintrc.json`)
  - TypeScript 지원 (@typescript-eslint)
  - React/React Hooks 지원
  - 테스트 파일 예외 처리
- Prettier + lint-staged 통합 (pre-commit hook)

#### Bug Fixes
- `encryption.ts`: 빈 문자열 암호화 시 복호화 에러 수정
- API 키 환경변수 누출 방지 (스크립트에서 하드코딩 제거)
- Static method `this` 참조 에러 수정 (PartyPolicyAdapter, WinnerInfoAdapter)

#### Data Collection
- 2018/2022 지방선거 공약 데이터 수집 스크립트 추가 (`collectLocalElectionPledges.ts`)
- 공공데이터포털 API 연동 개선 (ElecPrmsInfoInqireService, PofelcddInfoInqireService)

### 주요 기능
- 자연어 쿼리 → 구조화(의도·필터·출력) 후 API 호출 또는 크롤링 실행 (`apps/backend/src/api/routes/query.routes.ts`, `services/nlp/queryEngine.ts`).
- 공공데이터포털·R-ONE 등 API 연동 및 정규화: 선거공약/당선인/정당정책/후보자/부동산 통계 등 (`config/apis.ts` + 어댑터).
- 웹 크롤링: 선거정보도서관·정책 페이지·정당 사이트·커스텀 URL을 Puppeteer/cheerio로 수집, 잡 기록 및 실패 내역 포함 (`services/crawler/*`, `api/routes/crawl.routes.ts`).
- PDF/OCR 파싱: PyMuPDF(텍스트 추출) + Clova OCR/Google Vision/Dolphin 자동 선택 (`services/parser/parserFactory.ts`, `api/routes/parse.routes.ts`).
- 데이터 미리보기/정렬/필터 및 CSV·JSON·Excel 내보내기 (프론트 `Dashboard.tsx`, `hooks/useExport.ts` + 백엔드 `api/routes/export.routes.ts`).
- 쿼리/작업 히스토리 조회 및 사이드 패널에서 최근 작업/히스토리 확인 (`History.tsx`, `RightNav.tsx`, `api/routes/history.routes.ts`).
- 테마·내비게이션 상태·기능 플래그 표시 등 사용자 설정 (`Settings.tsx`).

### 주요 컴포넌트 및 라이브러리
- 프론트엔드: React 18 + Vite, 상태(Zustand), 서버 상태(@tanstack/react-query), 테이블(@tanstack/react-table), 폼(react-hook-form), 알림(react-hot-toast), 차트(Recharts), 아이콘(lucide-react), 내보내기(file-saver, xlsx), 라우팅(react-router-dom).
- 백엔드: Express + TypeScript, Prisma(PostgreSQL/Supabase), axios, fast-xml-parser, Bull(잡 큐), Puppeteer/cheerio(크롤러), pdf-parse/PyMuPDF & 외부 OCR 파서, csv/json 변환(@json2csv/plainjs, papaparse), 인증/JWT(jsonwebtoken), 유효성검사(zod, express-validator), 보안/성능(helmet, cors, compression, rate-limit), 로깅(winston + morgan), Sentry 연동.
- AI: Gemini(우선) 또는 패턴 기반 파서로 자연어 쿼리 구조화; OpenAI 클라이언트 포함으로 확장 가능 (`services/nlp/queryEngine.ts`, `config/env.ts`).
- 인프라/스크립트: Docker Compose, Vercel 설정, pnpm workspace, Turbo repo.

### 사용 범위와 취지
- 공공/정책/ESG 데이터의 **수집(API·크롤러·PDF)** → **정규화** → **내보내기**까지 단일 인터페이스로 제공하는 리서치 워크스테이션.
- 정책 연구자가 자연어로 질의(“2024 총선 서울 득표율”, “국민의힘 경제 공약”)하면 적합한 데이터 소스를 자동 선택하고 결과를 표/파일로 제공.
- 수집 과정(잡·히스토리·키 관리)을 투명하게 노출해 재현성과 협업을 높이는 목적.

### 알면 좋은 사실
- 기능 플래그: `.env`의 `ENABLE_NL_QUERY`, `ENABLE_OCR_PARSING`, `ENABLE_CRAWLING`으로 주요 기능 on/off; 프론트 Settings 화면에 상태 표시.
- 보안/안정성: Helmet CSP, 압축, CORS, 전역 rate limit(`/api`), Sentry 로깅, 50MB 업로드 제한 및 PDF 타입 필터.
- 테스트/미구현 처리: 테스트 환경에서는 API/크롤러 스텁 데이터를 반환; `parse_pdf` 인텐트와 R-ONE NLP 적응은 TODO로 명시 (`query.routes.ts`).
- 잡/데이터 적재: 모든 크롤링·쿼리 실행은 `DataJob`/`DataRecord`/`QueryHistory`로 DB에 기록하여 추적 가능 (`prisma/schema.prisma`).
- 프런트 UI: 좌측 소스/크롤러/파서 탐색, 상단 자연어 쿼리 바(⌘/Ctrl+K), 우측 패널에서 내보내기·작업 상태·히스토리·파서 선택.

### API 키 구조(저장·사용 방식)
- 스키마: `ApiSource`(소스 메타/인증 방식) ↔ `ApiKey`(여러 키, 활성여부/만료 포함) 관계로 관리 (`prisma/schema.prisma`).
- 저장/복호화: `apiKeyHelper.ts`가 AES-256-GCM으로 키를 암호화해 DB에 저장하고, 조회 시 복호화 (`ENCRYPTION_KEY` 미설정 시 개발용 키 경고). 로깅에는 마스킹된 키만 노출.
- 키 등록/토글 API: `/api/v1/sources/apis/:id/keys` POST(추가), PATCH 활성화 토글, DELETE 비활성화. 실제 키 값은 목록 조회 시 반환하지 않음 (`api/routes/sources.routes.ts`).
- 사용 흐름: 자연어 쿼리 실행 시 `parsedQuery.source.id`로 `ApiRegistry`에서 소스 설정을 가져오고, DB에서 활성 키를 복호화해 커넥터에 주입 후 호출 (`query.routes.ts` + `ApiConnectorFactory`).
- 시드 및 환경 연동: `prisma/seed-api-sources.ts`가 공공데이터·R-ONE·YouTube 등 기본 소스를 생성하고, `.env`의 `NABOSTATS_API_KEY`, `NEC_MANIFESTO_API_KEY`, `RONE_API_KEY`, `YOUTUBE_API_KEY`가 있으면 초기 키로 저장.
- 프론트 관리: `API SOURCES` 화면(`/sources/api`)에서 키 추가/활성화 토글/만료 확인 가능하며, 실제 키 문자열은 프론트에 노출되지 않음.

## ✨ Features

- **🔌 API Connector**: 공공데이터포털(선거공약/당선인/정당정책/후보자)·R-ONE·재정통계 등 다중 API 연동
- **🕷️ Web Crawler**: 선거정보도서관·정당 정책 페이지·커스텀 URL 크롤링 (Puppeteer/cheerio)
- **📄 PDF Parser**: PyMuPDF(텍스트) + Clova OCR/Google Vision/Dolphin 선택적 OCR
- **💬 NL Query**: Gemini 우선 자연어 쿼리 파싱 + 패턴 매칭 백업 (OpenAI 확장 가능)
- **📊 Data Export**: CSV, JSON, Excel 출력

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/napo.git
cd napo

# Install dependencies
pnpm install

# Prepare env files (copy and edit with your keys)
cp .env.example .env
cp .env.example apps/backend/.env

# (Optional) bring up local Postgres via Docker & migrate
# docker-compose up -d postgres && pnpm db:push

# Start development server
pnpm dev
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React + Vite)                │
│  ┌─────────┬────────────────────────────────┬─────────────┐ │
│  │LeftNav  │         Main Content           │  RightNav   │ │
│  │         │  ┌──────────────────────────┐  │             │ │
│  │ Sources │  │     NL Query Bar         │  │  Export     │ │
│  │ Crawlers│  ├──────────────────────────┤  │  Settings   │ │
│  │ Parsers │  │     Data Table/Charts    │  │  History    │ │
│  │         │  └──────────────────────────┘  │             │ │
│  └─────────┴────────────────────────────────┴─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend (Express + TypeScript)            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
│  │ NL Query │  │ Crawler  │  │ Parser   │  │ API          │ │
│  │ Engine   │  │ Engine   │  │ Engine   │  │ Connector    │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 PostgreSQL (Supabase / Local)               │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
napo/
├── apps/
│   ├── frontend/          # React + Vite
│   └── backend/           # Express + TypeScript
├── packages/
│   ├── types/             # Shared TypeScript types
│   └── utils/             # Shared utilities
├── docs/                  # Documentation
├── scripts/               # Setup & deployment scripts
├── docker-compose.yml     # Development environment
└── vercel.json           # Vercel deployment config
```

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://...
DATABASE_PROVIDER=supabase  # or 'local'

# Server
PORT=3001
FRONTEND_URL=http://localhost:5173

# AI / NLP
GEMINI_API_KEY=...
OPENAI_API_KEY=...   # optional fallback

# Public Data / External APIs
PUBLIC_DATA_API_KEY=...
NEC_MANIFESTO_API_KEY=...
RONE_API_KEY=...
NABOSTATS_API_KEY=...
YOUTUBE_API_KEY=...

# OCR / Parser Services
CLOVA_OCR_API_URL=...
CLOVA_OCR_SECRET_KEY=...
GOOGLE_APPLICATION_CREDENTIALS=./google-credentials.json
DOLPHIN_SERVICE_URL=...

# Feature Flags
ENABLE_NL_QUERY=true
ENABLE_OCR_PARSING=true
ENABLE_CRAWLING=true
```

## 📖 Usage Examples

### 자연어 쿼리

```
"2024 총선 서울 득표율 정당별로 보여줘"
"2022 지방선거 서울시장 당선인 공약 CSV로 뽑아줘"
"국민의힘 경제 공약만 모아서 엑셀로 내려줘"
"2018 지방선거 주요 정당 공약 다운로드"
"윤석열 대선 공약 텍스트로 정리해줘"
```

### API 연동

```typescript
// 커스텀 API 추가
const customApi = {
  id: 'my_api',
  name: 'My Custom API',
  baseUrl: 'https://api.example.com',
  authType: 'api_key',
  authConfig: { keyParamName: 'apiKey', keyLocation: 'query' },
};
```

## 🚢 Deployment

### Vercel (Recommended)

```bash
./scripts/deploy.sh prod
```

### Docker

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 📄 License

MIT

## 🔧 Auto Debug Collector (자동 디버깅 오류 수집)
- 목적: Gemini로 테스트 프롬프트를 생성하고 naPO에 자동 질의해 엣지케이스·오류를 수집/분석하는 모듈(`packages/auto-debug-collector`).
- 구조도:
```
┌─────────────────────────────────────────────────────────────────────┐
│                    AutoDebugCollector (Orchestrator)                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │ PromptGenerator │───▶│   QueryTester   │───▶│  ResultAnalyzer │ │
│  │  (Gemini 2.0/2.5│    │  (naPO parse/   │    │   (CSV/summary  │ │
│  │   + RateLimiter)│    │   execute)      │    │    writer)      │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│         │                       │                       │          │
│         ▼                       ▼                       ▼          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     RateLimiter (10/min)                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│         │                       │                       │          │
│         ▼                       ▼                       ▼          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                test_temp/ (임시 데이터 저장)                  │   │
│  │  - prompts/         (생성된 프롬프트)                        │   │
│  │  - responses/       (API 응답)                              │   │
│  │  - logs/            (실행 로그)                              │   │
│  │  - test_document_1st.csv  (분석 결과)                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```
- 아키텍처: PromptGenerator(Gemini 2.0 Flash 기본, 2.5 Flash fallback, 10회/분 RateLimiter) → QueryTester(naPO `/query`→`/query/execute`) → ResultAnalyzer(CSV/summary 작성) → AutoDebugCollector(오케스트레이션).
- 기본 설정: 라이브러리 기본 `promptsPerMinute` 3회(구성 파일), 스크립트 기본 4회(`apps/backend/scripts/run-auto-debug.ts --rate 4`), `maxIterations` 100, `domains` `['election','policy','candidate','party']`, 출력 경로 `apps/backend/test_temp/`.
- 출력물: `test_temp/test_document_1st.csv`, `summary.json`, `prompts/`, `responses/`, `logs/run.log` 등. `cleanup` 옵션으로 기존 결과 삭제 가능.
- 실행: `GEMINI_API_KEY` 필수, `NAPO_API_URL` 옵션(기본 `http://localhost:3001/api/v1`). 예) `npx tsx scripts/run-auto-debug.ts --iterations 50 --rate 3 --verbose --cleanup`.
- 커스터마이징: 카테고리/도메인 추가(`domains`), 모델 설정(`modelConfig`), 프롬프트 시스템 프롬프트 수정(`config.ts`), 결과 포맷/CSV 헤더(`config.ts`의 `CSV_HEADER`).
