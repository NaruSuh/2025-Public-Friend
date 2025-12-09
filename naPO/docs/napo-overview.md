# naPO 개요 (정책 연구자용)

## 1. 주요 기능
- 자연어 쿼리 → 구조화(의도·필터·출력 형태) 후 API 호출 또는 크롤링 실행 (`apps/backend/src/api/routes/query.routes.ts`, `services/nlp/queryEngine.ts`).
- 공공데이터포털·R-ONE 등 API 연동 및 정규화: 선거공약/당선인/정당정책/후보자/부동산 통계 등(`config/apis.ts` + 어댑터).
- 웹 크롤링: 선거정보도서관·정책 페이지·정당 사이트·커스텀 URL을 Puppeteer/cheerio로 수집, 잡 기록 및 실패 내역 포함(`services/crawler/*`, `api/routes/crawl.routes.ts`).
- PDF/OCR 파싱: PyMuPDF(텍스트 추출) + Clova OCR/Google Vision/Dolphin 자동 선택(`services/parser/parserFactory.ts`, `api/routes/parse.routes.ts`).
- 데이터 미리보기/정렬/필터 및 CSV·JSON·Excel 내보내기(프론트 `Dashboard.tsx`, `hooks/useExport.ts` + 백엔드 `api/routes/export.routes.ts`).
- 쿼리/작업 히스토리 조회 및 사이드 패널에서 최근 작업/히스토리 확인(`History.tsx`, `RightNav.tsx`, `api/routes/history.routes.ts`).
- 테마·내비게이션 상태·기능 플래그 표시 등 사용자 설정(`Settings.tsx`).

## 2. 주요 컴포넌트 및 라이브러리
- 프론트엔드: React 18 + Vite, 상태(Zustand), 서버 상태(@tanstack/react-query), 테이블(@tanstack/react-table), 폼(react-hook-form), 알림(react-hot-toast), 차트(Recharts), 아이콘(lucide-react), 내보내기(file-saver, xlsx), 라우팅(react-router-dom).
- 백엔드: Express + TypeScript, Prisma(PostgreSQL/Supabase), axios, fast-xml-parser, Bull(잡 큐), Puppeteer/cheerio(크롤러), pdf-parse/PyMuPDF & 외부 OCR 파서, csv/json 변환(@json2csv/plainjs, papaparse), 인증/JWT(jsonwebtoken), 유효성검사(zod, express-validator), 보안/성능(helmet, cors, compression, rate-limit), 로깅(winston + morgan), Sentry 연동.
- AI: Gemini(우선) 또는 패턴 기반 파서로 자연어 쿼리 구조화; OpenAI 클라이언트도 포함되어 확장 가능(`services/nlp/queryEngine.ts`, `config/env.ts`).
- 인프라/스크립트: Docker Compose, Vercel 설정, pnpm workspace, Turbo repo.

## 3. 사용 범위와 취지
- 공공/정책/ESG 데이터의 **수집( API·크롤러·PDF)** → **정규화** → **내보내기**까지 단일 인터페이스로 제공하는 리서치 워크스테이션.
- 정책 연구자가 자연어로 질의(“2024 총선 서울 득표율”, “국민의힘 경제 공약”)하면 적합한 데이터 소스를 자동 선택하고 결과를 표/파일로 제공.
- 수집 과정(잡·히스토리·키 관리)을 투명하게 노출해 재현성과 협업을 높이는 목적.

## 4. 알면 좋은 사실
- 기능 플래그: `.env`의 `ENABLE_NL_QUERY`, `ENABLE_OCR_PARSING`, `ENABLE_CRAWLING`으로 주요 기능 on/off; 프론트 Settings 화면에 상태 표시.
- 보안/안정성: Helmet CSP, 압축, CORS, 전역 rate limit(`/api`), Sentry 로깅, 50MB 업로드 제한 및 PDF 타입 필터.
- 테스트/미구현 처리: 테스트 환경에서는 API/크롤러 스텁 데이터를 반환; `parse_pdf` 인텐트와 R-ONE NLP 적응은 TODO로 명시(`query.routes.ts`).
- 잡/데이터 적재: 모든 크롤링·쿼리 실행은 `DataJob`/`DataRecord`/`QueryHistory`로 DB에 기록하여 추적 가능(`prisma/schema.prisma`).
- 프런트 UI: 좌측 소스/크롤러/파서 탐색, 상단 자연어 쿼리 바(⌘/Ctrl+K), 우측 패널에서 내보내기·작업 상태·히스토리·파서 선택.

## 5. API 키 구조(저장·사용 방식)
- 스키마: `ApiSource`(소스 메타/인증 방식) ↔ `ApiKey`(여러 키, 활성여부/만료 포함) 관계로 관리(`prisma/schema.prisma`).
- 저장/복호화: `apiKeyHelper.ts`가 AES-256-GCM으로 키를 암호화해 DB에 저장하고, 조회 시 복호화(`ENCRYPTION_KEY` 미설정 시 개발용 키 경고). 로깅에는 마스킹된 키만 노출.
- 키 등록/토글 API: `/api/v1/sources/apis/:id/keys` POST(추가), PATCH 활성화 토글, DELETE 비활성화. 실제 키 값은 목록 조회 시 반환하지 않음(`api/routes/sources.routes.ts`).
- 사용 흐름: 자연어 쿼리 실행 시 `parsedQuery.source.id`로 `ApiRegistry`에서 소스 설정을 가져오고, DB에서 활성 키를 복호화해 커넥터에 주입 후 호출(`query.routes.ts` + `ApiConnectorFactory`).
- 시드 및 환경 연동: `prisma/seed-api-sources.ts`가 공공데이터·R-ONE·YouTube 등 기본 소스를 생성하고, `.env`의 `NABOSTATS_API_KEY`, `NEC_MANIFESTO_API_KEY`, `RONE_API_KEY`, `YOUTUBE_API_KEY`가 있으면 초기 키로 저장.
- 프론트 관리: `API SOURCES` 화면(`/sources/api`)에서 키 추가/활성화 토글/만료 확인 가능하며, 실제 키 문자열은 프런트에 노출되지 않음.
