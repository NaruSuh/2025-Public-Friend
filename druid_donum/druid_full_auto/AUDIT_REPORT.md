# 코드 감사 보고서

## 개요
- 검사 대상: `/home/naru/work/2025-Public-Friend/druid_donum/druid_full_auto`
- 검사 일시: 2025-10-05
- 감사자: 자동 감사(도구 기반 수집) — 보고서는 수동 검토 및 실행 가능한 권고 포함
- 범위: 소스 파일 전수(`main.py`, `app.py`), 의존성(`requirements.txt`), 문서(`README.md`, `prompt.md`), 배포 가이드 일부

## 감사 방식
- 코드 읽기(정적 분석), 주요 함수 실행 경로 추적, Streamlit 앱 코드와 CLI 엔진의 비교 검토
- 중점: 현재 의도대로 작동하지 않을 가능성이 높은 코드, 확인된 버그, 잠재적 버그, 보안/성능/운영 리스크

## 요약 (상위 5개)
1. 견고성/예외 처리 부족 (High) — 네트워크 실패, HTML 구조 변경, 비표준 콘텐츠에 대한 방어로직 미흡
2. Streamlit 캐시/데이터 직렬화 취약성 (Medium) — DataFrame <-> dict 직렬화 및 캐시 키 사용 문제 가능
3. HTML 셀렉터/인덱스 가정 (High) — 테이블 열 인덱스 하드코딩으로 사이트 구조 변경 시 파싱 실패
4. 로깅/디버깅 부족 (Medium) — 대부분 print, 스트림릿 앱에서는 예외를 광범위하게 잡아내어 원인 파악이 어려움
5. 배포/환경 이슈 (Low) — requirements에 lxml 포함 등 불필요 또는 누락 가능성, Brotli('br') 인코딩 처리 미확인

---

## 상세 발견 사항

### A. 치명적 / High

- 문제: 리스트/상세 파싱에서 HTML 요소 인덱스를 하드코딩(`td:nth-of-type(1)`, `td:nth-of-type(3)` 등)
  - 파일: `main.py::parse_list_page`
  - 증상: 테이블 컬럼 순서가 바뀌거나 광고/공지 행이 섞이면 잘못된 값(예: 날짜 대신 제목)이 추출될 수 있음
  - 재현: 사이트의 테이블 구조가 변경되면 즉시 재현됨
  - 권장조치: 셀렉터를 더 구체적으로(예: 클래스 기반) 작성하거나 각 행의 헤더를 먼저 읽어 인덱스 매핑을 수행하도록 변경

- 문제: `post_date` 파싱 실패 처리 미흡
  - 파일: `main.py::parse_list_page`
  - 증상: 날짜 포맷이 다른 경우 `post_date`가 None으로 남고 이후 날짜 비교에서 TypeError 발생 가능
  - 권장조치: 날짜 파싱 실패 시 원본 문자열을 보존하거나 `dateutil.parser.parse` 같은 유연한 파서 사용 및 실패 시 로깅


### B. 중요 / Medium

- 문제: Streamlit 캐시 사용 시 비직렬화 가능 인자 전달 위험
  - 파일: `app.py::generate_excel_data`, `generate_csv_data`
  - 증상: `st.cache_data`는 인자 해시화를 사용하므로, 큰 dict/데이터프레임 구조를 캐시 키로 전달하면 의도치 않은 캐시 미스 또는 오류가 날 수 있음
  - 권장조치: 캐시 키로는 단순 불변값(예: timestamp, 문자열 해시)을 전달하고, 데이터 자체는 캐시 내부에서 로컬 캐시(파일 또는 bytes)로 관리

- 문제: `selected_history['data'].to_dict()` 후 `generate_excel_data(df_dict, ...)` 로 변환하는 로직
  - 파일: `app.py` 사이드바
  - 증상: DataFrame.to_dict() 포맷(orient)에 따라 재구성 시 컬럼-레코드 정렬이 바뀔 수 있음. 또한 큰 데이터는 메모리/성능 문제 유발
  - 권장조치: 캐시 저장 시 `DataFrame.to_records()` 또는 `pickle`/parquet 직렬화를 사용하여 안정적으로 보존

- 문제: 예외 처리에서 너무 넓은 except 사용 및 상세 예외 로깅 부족
  - 파일: `app.py`, `main.py`
  - 증상: 오류 원인 파악이 어려움 (특히 Streamlit 사용자 화면에서)
  - 권장조치: 예외별로 처리하고 traceback/컨텍스트를 로깅. Streamlit에서는 사용자친화적 메시지와 함께 내부 로그에 상세 스택 트레이스를 기록


### C. 경미 / Low

- 코드 중복: `import re`가 여러 위치에 반복
  - 권장조치: 모듈 상단으로 이동

- 헤더 'Accept-Encoding'에 'br' 포함
  - 설명: Brotli( br ) 디코딩은 requests에 기본 포함되지 않을 수 있음(파이썬 환경에 따라). 서버가 br로 응답할 경우 응답이 제대로 디코딩되지 않는 상황 발생 가능
  - 권장조치: headers에서 'br' 제거하거나 `brotli` 패키지 설치/확인, 또는 requests가 제대로 디코딩하는지 테스트

- 의존성 가이드
  - `requirements.txt`에 `lxml`이 포함되어 있으나 코드에서는 `html.parser`를 사용. lxml을 사용하려면 BeautifulSoup 파서 인자로 명시적으로 'lxml'을 사용할 것을 권장


## 권장 수정사항 (우선순위별)

우선순위: P1(시급), P2(중간), P3(권장)

- P1: 튼튼한 파싱 방어
  - 변경 내용: `parse_list_page()` 와 `parse_detail_page()` 에서 각 필드를 선택할 때 예외 케이스(누락 필드, 다른 태그 구조)를 다루는 방어 코드 추가
  - 예: 각 row에서 셀 개수를 체크하고, title/링크/날짜를 찾을 때 여러 셀 후보를 시도

- P1: 날짜 파싱 개선
  - 변경 내용: `dateutil.parser.parse` 사용(설치 필요: python-dateutil은 보통 기본 포함), 실패 시 원본 문자열을 `post_date_str`에 남기고 `post_date`에는 None 저장

- P1: 로깅 개선
  - 변경 내용: 모듈 레벨에서 `logging` 사용(파일/콘솔 핸들러), Streamlit에서 사용자 메시지는 `st.info/error`로, 내부 로그는 파일 또는 세션 상태에 남김

- P2: Streamlit 캐시 안정화
  - 변경 내용: `st.cache_data` 인자는 소형 불변(예: timestamp str)만 사용. 데이터 캐시는 bytes(parquet/excel)로 만들어 캐시하거나 로컬 임시 파일을 사용

- P2: 예외 스택트레이스 보존
  - 변경 내용: 광범위한 except 블록에서 `traceback.format_exc()`을 로깅에 포함

- P3: 의존성 및 환경 문서 정리
  - 변경 내용: `requirements.txt` 정리(실제 사용되는 라이브러리만 유지), `README.md`에 권장 Python 버전(3.10+)과 가상환경 사용법 추가


## 빠른 재현 및 테스트 체크리스트
1. 유닛/통합 테스트 추가(권장 최소 3개)
   - parse_list_page: HTML 스니펫 1~2개로 제목/링크/날짜/조회수/첨부 여부 검증
   - parse_detail_page: 정보 블록에서 담당부서/담당자/연락처/첨부 추출 검증
   - save_to_excel: 샘플 데이터프레임으로 파일 생성 및 컬럼 라벨 검증

2. 수동 검증
   - `python3 main.py`로 CLI 실행(짧은 기간(days=7)로 제한)하여 콘솔 출력과 엑셀 결과 확인
   - `streamlit run app.py` 실행 후 UI에서 크롤링 수행(요청 수 작게 설정)하여 Streamlit 로그/다운로드 동작 점검


## 권고 구현 예시(요약)
- 날짜 파싱 (권장):

```py
from dateutil import parser as date_parser
try:
    post_date = date_parser.parse(date_str, dayfirst=False)
except Exception:
    post_date = None
```

- 안전한 views 추출 예시:

```py
views_numbers = re.findall(r'\d+', views_text.replace(',', ''))
views = int(views_numbers[0]) if views_numbers else 0
```


## 품질 게이트 체크리스트 (권장)
- [ ] Lint 통과 (flake8/ruff)
- [ ] Type/typing 기본 적용 (선택)
- [ ] 유닛 테스트: parse_list_page, parse_detail_page, save_to_excel
- [ ] 의존성 설치로 실행 가능한 환경 문서화


## 파일별 검사 결과 요약
- `main.py` — 핵심 크롤러. 기능적 흐름은 명확하나, HTML 구조 변경에 취약하고 예외 처리/로깅이 약함. (Action: P1 다수 권고)
- `app.py` — Streamlit UI. UX는 잘 구성되어 있으나 캐시 사용과 DataFrame 직렬화 관련 잠재적 오류 존재. (Action: P2 권고)
- `requirements.txt` — 주요 의존성 포함. 환경 가이드 보완 필요. (Action: P3 권고)
- `README.md`, `prompt.md` — 문서화 양호. 배포/운영 섹션 보완 권장.


## 다음 단계 (권장 실행 순서)
1. (개발) P1 우선 수정: 파싱 방어, 날짜 파서, 예외 로깅 개선
2. (테스트) 로컬에서 샘플 HTML로 단위 테스트 3개 추가 및 실행
3. (검증) 수정 후 `python3 main.py --days 7` 로 동작 확인, `streamlit run app.py`로 UI 확인
4. (문서) `README.md`에 환경 설치 및 테스트 방법 추가

---

요약: 현재 코드베이스는 기능적 크롤링 엔진(대부분의 케이스에서 동작 가능)을 갖추고 있으나, 운영시나리오(HTML 변경, 네트워크 불안정, 대형 데이터)에서 취약한 부분이 있습니다. 우선 파싱 방어와 로깅 개선을 적용하면 안정성이 크게 향상됩니다. 필요하면 제가 직접 P1 변경사항을 코드로 제안/적용해 드리겠습니다.
