# 100% 크롤링 달성을 위한 개선 제안 (코드베이스 기반)

이 문서는 `manualAdd-on` 파이프라인과 산출물(`output/basic_minutes`, `output/metro_minutes`)을 실제로 확인한 결과를 바탕으로, **기초지자체 226개 + 광역 17개를 100%에 가깝게 수집하기 위한 실전 개선안**을 정리한 것입니다.

---

## 0) 현재 상태 요약 (코드/산출물 기준)

- 광역 16개(제주 제외)는 `manualAdd-on/metro_crawl_all.py`로 수집하며, `output/metro_minutes`에 결과가 존재함.
- 기초지자체는 `manualAdd-on/crawl_all_basic_parallel.py`로 병렬 수집하며, 상태는 `_summary.json`/`_progress.json`에 기록됨.
- 실패 유형 분류는 `_connection_test.json`과 `council_crawling_status.md`에 정리됨.
- JS 렌더링 사이트 대응을 위해 `manualAdd-on/playwright_crawler.py`가 존재하지만, **메인 파이프라인과 분리되어 있음**.

---

## 1) 100% 달성을 막는 실제 병목

### A. URL 변화/도메인 변경
- DNS 오류 및 404 비율이 큼.
- 현재는 수동 조사(문서/리스트 기반) 의존.

### B. JS 동적 로딩/테이블 숨김
- `requests + BeautifulSoup` 기반 크롤러로는 테이블이 보이지 않는 사이트가 다수.
- Playwright는 별도 스크립트로만 존재.

### C. 이질적 CMS/구현 패턴
- `assembly`, `xcom`, `ems`, `councilbook`, `busan_board` 등 다수 크롤러 타입이 혼재.
- 유형 분류/리라이팅 룰이 지속적으로 추가될 구조.

### D. 실패 감지/재시도 플로우 분리
- 실패는 기록되지만, **실패 유형별 자동 재시도/대체 크롤러**가 메인 플로우에 없음.

---

## 2) 핵심 개선 전략 (실전형)

### 2.1 실패 유형별 “재시도 파이프라인” 도입

현재 병렬 크롤러는 실패 사유를 남기고 종료함.  
이를 다음과 같이 자동 재시도 플로우로 묶어야 함:

1. **DNS/404/연결거부 → URL 리디렉션 탐색 모듈**
   - 공통 패턴 탐색: `council.{city}.go.kr`, `{city}council.go.kr`, `www.{city}.go.kr/council` 등.
   - 전자정부 CMS 도메인 표준 후보 리스트로 자동 탐색 후 검증.
2. **정상 응답 but 빈 테이블 → Playwright 재시도**
   - requests로 table 미검출 → Playwright로 list URL 재진입.
3. **회차 미출력/목록만 있음 → 상세페이지 크롤러 분기**
   - 목록 페이지에서 detail 링크 존재시: 동적 함수 파싱.
   - JS onclick 분석용 정규식 패턴 추가.

이를 위해 `_connection_test.json`과 `_summary.json` 결과를 기반으로 **자동 재시도 큐**를 돌리는 별도 스크립트를 추가하는 것이 효율적입니다.

---

### 2.2 Playwright 통합 (메인 파이프라인 내)

현재 `playwright_crawler.py`는 단독 실행 스크립트입니다.  
`crawl_all_basic_parallel.py` 내에서 다음과 같이 통합해야 함:

- `requests` 실패 유형 중:
  - “테이블 없음”, “응답 크기 너무 작음”, “dynamic loading 추정”
  → Playwright로 재시도 후 저장
- Playwright 결과도 동일한 저장 포맷(`ResultSaver.save_jsonl`, `.save_markdown`)으로 저장

이렇게 하면 JS 기반 8~20개 정도의 “논리적 실패”를 흡수할 수 있습니다.

---

### 2.3 URL 자동 복구 모듈 (패턴 탐색)

도메인 변경은 수작업이 아닌 자동탐색이 필요함.

제안하는 룰:

1. **base_url 후보 생성**
   - `council.{city}.go.kr`
   - `council.{city}.{region}.kr`
   - `www.{city}council.go.kr`
   - `{city}.go.kr/council`
2. **list_url 후보 생성**
   - `/kr/minutes/late.do`
   - `/record/list.do`
   - `/minutes/late.do`
   - `/assembly/minutes/late.do`
3. 후보 조합으로 **HEAD/GET 검사 후 table 검출**

이 모듈은 `basic_councils.yaml` 보완과 병행하면 404/DNS의 상당수를 회수할 수 있습니다.

---

### 2.4 “사이트 유형 판별기” 추가

`crawler_type`가 잘못 매핑되면 404/빈 테이블이 발생합니다.  
자동 판별이 필요합니다:

- `base_url`에서 페이지 `<meta name="generator">`나 `script` 힌트로 CMS 유형 추정
- 특정 DOM 패턴(예: `councilbook`, `busan_board`) 존재 시 자동 분기
- 판별 결과를 `basic_councils.yaml`에 자동 업데이트하는 보조 스크립트 추가

---

### 2.5 재시도 큐 + 실패 사유 강화

현재 실패 사유는 “회의록 없음”으로 뭉뚱그려지는 경우가 많음.  
정확한 실패 이유를 다음과 같이 구분해야 재시도 전략이 명확해집니다:

- `dns_error`
- `http_404`
- `http_403`
- `timeout`
- `no_table`
- `empty_body`
- `parse_error`
- `js_required`

이 분류는 `_summary.json`의 reason 필드에 기록되도록 개선합니다.

---

## 3) 실행 순서 제안

1. **자동 재시도 큐 스크립트 추가**
   - `_summary.json` 기반 실패 유형별 재시도
2. **Playwright 통합**
   - dynamic/empty/table 미검출 대상만 선택 실행
3. **URL 자동 탐색 모듈**
   - DNS/404 대상에 대해 후보 URL 탐색
4. **crawler_type 판별기 도입**
   - 신규로 성공한 사이트 유형 학습 → YAML 업데이트

---

## 4) 기대 효과

- DNS/404의 절반 이상 자동 회수 가능
- JS 기반 사이트 상당수 자동 회수
- “회의록 없음” 오탐을 줄여 실제 실패 원인 파악 가능
- 결과적으로 **100%에 가까운 실수집 성공률** 달성 가능

---

## 5) 바로 적용 가능한 최소 변경안

즉시 반영 가능한 최소 변경은 아래입니다:

1. `crawl_all_basic_parallel.py`에 **Playwright fallback** 추가
2. 실패 사유를 `no_table`, `empty_body`, `http_404` 등으로 분류하도록 수정
3. `_summary.json` 기반의 **재시도 대상 자동 추출** 스크립트 추가

이 3가지만 해도 100%에 가까운 접근률을 확보할 수 있습니다.

---

## 참고 파일

- 크롤러 메인: `manualAdd-on/council_crawler.py`
- 병렬 실행: `manualAdd-on/crawl_all_basic_parallel.py`
- Playwright: `manualAdd-on/playwright_crawler.py`
- 진행상태: `manualAdd-on/output/basic_minutes/_summary.json`
- 실패 분류: `manualAdd-on/output/basic_minutes/_connection_test.json`
- 현황 문서: `manualAdd-on/output/metro_minutes/council_crawling_status.md`
