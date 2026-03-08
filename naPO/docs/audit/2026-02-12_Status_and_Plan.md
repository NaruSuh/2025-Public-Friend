# naPO 현황/이력/다음 단계 정리 (2026-02-12)

## 1) 지금까지 한 일 (주요 변경)
- GIS 제거: `packages/connectors`에서 SGIS 전부 삭제, `core-types` 정리.
- RAG 파이프라인(로컬 SQLite) 추가: `services/rag/*`, ingest 스크립트 `apps/backend/scripts/ingest-rag.ts`.
- 로컬 임베딩 지원: `@xenova/transformers`, `RAG_EMBED_PROVIDER=local`, 기본 모델 `Xenova/all-MiniLM-L6-v2`.
- 챗봇 백엔드/프론트 연동:
  - API: `apps/backend/src/api/routes/chat.routes.ts` (`POST /api/v1/chat`)
  - 프론트: `ChatPanel.tsx` → API 호출, citations/신뢰도 표시.
  - Gemini 채팅 모델 기본값을 `models/gemini-2.5-flash`, `GEMINI_API_VERSION=v1`로 보정.
- 인제스트: 회의록(51GB) 제외, 선거정보자료만 사용. DB `apps/backend/data/rag.sqlite`(약 94MB) 생성. 회의록 124건 유입되었으나 삭제 완료 → 현재 `documents` 1,639개(전부 선거정보자료), `chunks` 4,359개.
- 로그 개선: ingest 시작/진행/종료 로그, 로컬 임베딩 모델 로드 로그 추가.
- 편의 스크립트: `start.sh` 추가(백엔드 ts-node + 프론트 vite 동시 실행, dev 용).
- 버그 리포트 추가: `docs/audit/2026-02-12_Bug_Report_for_Codex.md`.

## 2) 현재 상태
- RAG DB: `apps/backend/data/rag.sqlite` (회의록 제외, 선거정보자료만).
- 환경변수 예시: `.env.example`에 로컬 임베딩/제미나이 모델/버전 포함.
- API 동작: `curl -X POST http://127.0.0.1:3100/api/v1/chat ...` 테스트 성공(답변+citations 반환).
- 프론트: ChatPanel이 API 연동됨. KeyInfoCards 등 추가 UI 존재.
- 포트/실행: sandbox에서 tsx watch는 IPC 파이프 EPERM 발생 가능. ts-node --transpile-only 방식은 포트 3100에서 정상 동작 확인. Vite는 포트 바인딩이 EPERM 날 수 있음(환경 의존).

## 3) 실행 방법 (로컬 개발)
백엔드 단독:
```bash
cd /home/naru/dev/naID/naPO/apps/backend
PORT=3001 GEMINI_CHAT_MODEL=models/gemini-2.5-flash GEMINI_API_VERSION=v1 \
RAG_EMBED_PROVIDER=local RAG_EXCLUDE_PATHS="1. 지방의회 회의록" RAG_SKIP_PDF=true \
pnpm exec ts-node --require tsconfig-paths/register --prefer-ts-exts --transpile-only src/index.ts
```
헬스 체크: `curl http://127.0.0.1:3001/health`

프론트(dev): `pnpm --filter @napo/frontend dev -- --host --port 5173` (환경에 따라 EPERM 발생 시 로컬 환경에서 실행 권장)

start.sh(dev 동시 실행):
```bash
cd /home/naru/dev/naID/naPO
BACKEND_PORT=3001 FRONTEND_PORT=5173 ./start.sh
```
(참고: Vite 포트 바인딩이 안 되는 환경이 있을 수 있음)

## 4) 인제스트
- 현재 DB는 회의록 제외본(선거정보자료만)으로 완성. 재인제스트 필요 시:
```bash
pnpm -C /home/naru/dev/naID/naPO/apps/backend rag:ingest "/home/naru/dev/naID/naPO_DB"
# 설정 예: RAG_EMBED_PROVIDER=local RAG_EXCLUDE_PATHS="1. 지방의회 회의록" RAG_SKIP_PDF=true
```
- 진행 로그가 찍히므로 오래 걸려도 동작 확인 가능. 로컬 임베딩 첫 실행 시 모델 다운로드 로그 표시.

## 5) 배포(일반 서버/Nginx 권장)
- 프론트 빌드: `pnpm --filter @napo/frontend build` → `apps/frontend/dist` 정적 서빙.
- 백엔드 빌드/실행: `pnpm --filter @napo/backend build` → `node apps/backend/dist/index.js` (환경변수 설정 필수).
- 역프록시: Nginx 등으로 `/api` → 백엔드(3001 등), `/` → 정적 dist.
- RAG: 미리 생성한 `rag.sqlite`를 배포 서버에 배치(회의록 제외본). 서버에서 인제스트 재실행하지 않는 쪽이 Streamlit Cloud 대비 안정.

## 6) Streamlit Cloud에 올리고 싶을 때 (추천 시나리오)
- Node/React는 그대로는 불가 → Python 단일 앱 필요.
- 전략:
  1) 현 `rag.sqlite`(회의록 제외, 94MB 정도)를 LFS/외부 URL에 올려두고 Streamlit에서 다운로드 후 read-only 사용.
  2) Python에서 sqlite3로 FTS+임베딩(JSON) 읽어 코사인 유사도 계산 → topK 컨텍스트 생성.
  3) 생성은 Gemini Chat API만 호출(키는 secrets.toml). 임베딩 재생성은 하지 않음(모델 다운로드/메모리 문제 회피).
  4) UI: `st.chat_message`로 답변/인용/신뢰도 표시.
- 리소스 제약(1~3GB RAM) 때문에 “미리 구운 DB”만 사용해야 함. 인제스트/모델 다운로드는 Cloud에서 하면 실패 가능성 높음.

## 7) 알려진 이슈/주의
- tsx watch IPC EPERM: 일부 환경에서 `/tmp/tsx-1000/*.pipe` listen 에러. ts-node --transpile-only로 우회 가능.
- Vite 포트 EPERM: sandbox에서 0.0.0.0:5173/5174 바인딩 거부 사례 있음. 로컬/다른 포트 또는 역프록시 환경에서 실행 권장.
- Gemini 키 권한: 제공된 키는 embedContent 미지원 → 현재 로컬 임베딩 사용. Chat은 `models/gemini-2.5-flash` v1로 테스트 성공.
- 대용량 데이터: 회의록 51GB는 인덱싱 제외. 데이터 원본을 배포에 포함하지 말 것(.gitignore 추가).

## 8) 다음 액션 제안
- (필수) 배포용 환경에 맞춰 백엔드/프론트 빌드 후 Nginx 등으로 호스팅, rag.sqlite 배포.
- (선택) Streamlit Cloud PoC: Python 앱으로 rag.sqlite 읽는 경량 챗봇 작성.
- (선택) Vite 포트 바인딩 문제 해결: 로컬/서버 환경에서 포트 권한/방화벽 확인.
- (선택) Gemini embed 지원 키 확보 시 RAG_EMBED_PROVIDER를 gemini로 전환 후 재인제스트.
