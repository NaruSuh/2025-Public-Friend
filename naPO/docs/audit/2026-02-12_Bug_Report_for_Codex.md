# 🚨 긴급 버그 리포트 & 인수인계서 (To: Codex)

**작성자**: Gemini CLI Agent
**수신자**: Codex Agent
**날짜**: 2026-02-12 17:15
**프로젝트**: `/home/naru/dev/naID/naPO`

---

## 1. 현재 상황 (Status Quo)
Gemini CLI가 **"로컬 임베딩 전환"** 및 **"챗봇 API 연결"** 작업을 시도했으나, 실행 단계에서 **서버 접속 불가(ERR_CONNECTION_REFUSED)** 및 **프로세스 조기 종료** 문제가 지속적으로 발생하고 있음.

## 2. 발생한 에러 및 증상 (Symptoms)

### 2.1 인제스트 (Ingest) 실패
*   **명령**: `pnpm rag:ingest "/home/naru/dev/naID/naPO_DB"` (로컬 임베딩 모드)
*   **증상**: 실행 후 아무런 로그 출력 없이 **5분 타임아웃(Timeout)**으로 강제 종료됨.
*   **원인 추정**:
    1.  `@xenova/transformers` 모델(`all-MiniLM-L6-v2`) 최초 다운로드 시 네트워크 대기 시간이 길어짐.
    2.  `ingest-rag.ts` 스크립트가 진행 상황(Progress)을 출력하지 않아 멈춘 것처럼 보임.
    3.  `raw_election` 폴더 내 JSON 파일 파싱 중 에러 발생 가능성.

### 2.2 서버 실행 (Dev Server) 실패
*   **명령**: `pnpm dev` (백엔드/프론트엔드)
*   **증상**:
    *   포그라운드 실행 시: `Running on http://localhost:3001` 로그가 뜨며 정상 실행됨.
    *   백그라운드(`&`) 실행 시: 잠시 후 프로세스가 사라짐 (`Exit Code: 1`).
    *   브라우저 접속: `http://localhost:5173` 접속 시 **CONNECTION_REFUSED**.
*   **원인 추정**:
    1.  `nohup` 또는 백그라운드 실행 시 환경변수(`GEMINI_API_KEY` 등)가 제대로 전달되지 않아 크래시 발생.
    2.  이전 실행된 고아 프로세스(Zombie Process)가 포트(`3001`, `5173`)를 잡고 있어서 충돌.

### 2.3 챗봇 UI 연결 (Frontend)
*   **상태**: `ChatPanel.tsx`는 수정되어 `/api/v1/chat`을 호출하도록 변경됨.
*   **문제**: 백엔드가 죽어있어서 API 호출 시 `Network Error` 발생.

---

## 3. 조치 요구 사항 (Action Items for Codex)

Codex는 다음 순서대로 시스템을 복구하고 안정화해 주십시오.

### ✅ Step 1: 프로세스 정리 (Cleanup)
*   현재 실행 중인 모든 `node`, `vite`, `ts-node` 프로세스를 **강제 종료(Kill)** 하십시오.
*   포트 `3001`, `5173`이 완전히 비었는지 확인하십시오.

### ✅ Step 2: 인제스트 스크립트 개선 (Ingest Fix)
*   `scripts/ingest-rag.ts`에 **콘솔 로그(Progress Bar)**를 추가하여, 실행 중임을 알 수 있게 하십시오. (예: "Processing file 1/100...")
*   모델 다운로드 시 "Downloading model..." 로그가 찍히도록 `EmbeddingService`를 보강하십시오.
*   작은 폴더(`raw_election`)부터 테스트하여 인제스트가 확실히 되는지 검증하십시오.

### ✅ Step 3: 서버 실행 안정화 (Server Stability)
*   `start.sh` 스크립트를 만들거나 수정하여, **환경변수를 로드한 상태에서** 백엔드와 프론트엔드를 동시에 안정적으로 실행하도록 하십시오.
*   `concurrently` 패키지를 사용하여 `pnpm dev` 한 번으로 둘 다 켜지게 하는 것을 권장합니다.

### ✅ Step 4: 최종 접속 테스트
*   서버 실행 후 `curl http://localhost:3001/health`로 백엔드 생존 확인.
*   `curl http://localhost:5173`로 프론트엔드 생존 확인.

---

## 4. 참고 자료 (Reference)
*   **수정된 ChatPanel**: `apps/frontend/src/components/chat/ChatPanel.tsx` (API 연동됨)
*   **환경변수**: `.env` (Gemini Key, Local Embedding 설정 완료)
*   **데이터 위치**: `/home/naru/dev/naID/naPO_DB`

**Gemini CLI의 한마디**: "길은 뚫어놨는데 차가 시동이 안 걸립니다. 정비공(Codex)이 와서 배터리 점프 좀 뛰어주세요."
