# 🌲 산림청 입찰정보 크롤러

산림청 웹사이트의 입찰공고 정보를 자동으로 수집하여 엑셀/CSV 파일로 저장하는 프로그램입니다.

**Version**: 1.1.1 | **Status**: Production Hardening 90% Complete | **Test Coverage**: ~42%

## ✨ 주요 기능

### 핵심 기능
- 🔍 **연도별 수집 기간 설정** - 1년부터 10년까지 선택 가능 (검증됨)
- 📥 **다중 파일 포맷** - Excel (.xlsx), CSV (.csv) 지원
- 📋 **구조화된 로깅** - 파일 + 콘솔 이중 로깅, 일별 로그 파일
- 💾 **로그 다운로드** - 마크다운(.md) 형식으로 저장 가능
- ⚡ **원터치 자동화** - 크롤링부터 파일 생성까지 한 번에
- 🎨 **웹 기반 UI** - 직관적인 Streamlit 인터페이스

### 🆕 v1.1.1 신규 기능 (2025-10-06)
- ✅ **ParserFactory 스모크 테스트**: 동적 플러그인 로딩 회귀를 방지하는 테스트 추가
- ✅ **스트림릿 히스토리 영속화**: `logs/crawl_history.md`에 최신 수집 결과를 Markdown으로 자동 기록
- ✅ **락 재진입 제거**: JSON read-modify-write가 중첩 타임아웃 없이 실행되도록 개선

### v1.1.0 (2025-10-06)
- ✅ **입력 검증** - 최대 10년 범위, 최소 딜레이 강제
- ✅ **체크포인트/재개** - 중단 시 자동 재개 (JSON 기반)
- ✅ **안전한 날짜 파싱** - 타임존 처리 및 범위 검증
- ✅ **고급 에러 핸들링** - Rate-limit 헤더 인식, 지수 백오프 캡 (60초)
- ✅ **27개 유닛 테스트** - 핵심 기능 테스트 커버리지 ~40%
- ✅ **커스텀 예외** - `CrawlerException`, `ParsingException`

## 🎯 사용 방법

### 🖥️ Streamlit 웹 앱 (권장)

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속

#### 웹 앱 사용법

1. **사이드바에서 설정 조정**
   - 수집 기간: 1~10년 선택
   - 요청 간 딜레이: 0.5~3.0초
   - 페이지 간 딜레이: 0.5~5.0초

2. **크롤링 모드 선택**
   - **🚀 크롤링 시작**: 기본 크롤링 모드
   - **📥 크롤링 및 완료시 엑셀파일 작성**: 원터치 자동화 모드

3. **결과 확인 및 다운로드**
   - 실시간 진행 상황 확인
   - 통계 정보 및 데이터 미리보기
   - Excel/CSV 파일 다운로드
   - 로그 보기 및 다운로드

### 💻 CLI 버전

```bash
python3 main.py
```

## 프로젝트 구조

```
druid_full_auto/
├── main.py                    # 크롤러 엔진 (체크포인트, 로깅 포함)
├── app.py                     # Streamlit 웹 앱
├── requirements.txt           # 프로덕션 의존성
├── requirements-dev.txt       # 개발/테스트 의존성 (NEW)
│
├── tests/                     # 테스트 (NEW)
│   ├── unit/
│   │   ├── test_crawler.py         # 크롤러 테스트 (18 tests)
│   │   ├── test_parsing.py         # 파싱 테스트 (9 tests)
│   │   └── test_parser_factory.py  # ParserFactory 스모크 테스트 (1 test)
│   └── README.md              # 테스트 가이드
│
├── src/core/                  # 코어 추상화 (v2.0 준비)
│   ├── base_crawler.py
│   └── parser_factory.py
│
├── logs/                      # 일별 로그 + crawl_history.md (자동 생성)
├── crawl_checkpoint.json      # 체크포인트 (자동 생성)
│
├── docs/
│   ├── README.md              # 이 파일
│   ├── ARCHITECTURE.md        # v2.0 설계
│   ├── CHANGELOG.md           # 변경 이력 (NEW)
│   ├── 2nd_Audit_Report.md    # 감사 보고서 (NEW)
│   ├── CURRENT_STATUS.md      # 프로젝트 현황
│   └── ...
└── .llm/                      # LLM 협업 인프라
```

## 설치 방법

### 1. Python 환경 확인
권장: Python 3.10 이상 (3.10/3.11 권장). 가상환경 사용 권장

```bash
python --version
python -m venv .venv
source .venv/bin/activate
```

### 2. 의존성 설치

#### 프로덕션 사용
```bash
pip install -r requirements.txt
```

#### 개발/테스트 (권장)
```bash
pip install -r requirements-dev.txt
```

또는 개별 설치:
```bash
# 프로덕션
pip install requests beautifulsoup4 pandas openpyxl lxml streamlit python-dateutil

# 개발 (추가)
pip install pytest pytest-cov pytest-mock black ruff mypy pre-commit
```

### 3. 테스트 실행 (선택)

```bash
# 모든 테스트 실행
pytest

# 커버리지 포함
pytest --cov=. --cov-report=html

# 특정 테스트만
pytest tests/unit/test_crawler.py -v
```

자세한 내용은 [tests/README.md](tests/README.md) 참조

## CLI 사용 방법

### 기본 실행

```bash
cd "/home/naru/work/2025_Vibe/2025 Druid Donum/2025 Druid Full-auto Firing"
python3 main.py
```

### 실행 결과

프로그램 실행 시:

1. 산림청 입찰공고 게시판에서 최근 1년치 데이터를 수집합니다
2. 각 페이지를 순회하며 게시글 상세 정보를 추출합니다
3. 진행 상황이 콘솔에 표시됩니다
4. 완료 후 엑셀 파일이 생성됩니다

**출력 예시:**
```
============================================================
  산림청 입찰정보 크롤러
============================================================
[*] 산림청 입찰정보 크롤링 시작...
[*] 수집 기간: 최근 365일 (기준일: 2024-10-04)

[*] 페이지 1 처리 중...
  [1/10] 2024년 ○○ 산림사업 입찰공고...
  [2/10] ○○지방산림청 △△ 조달 입찰...
  ...

[✓] 크롤링 완료: 총 1,234개 항목 수집
[✓] 엑셀 파일 저장: 산림청_입찰정보_20241004_153022.xlsx
```

### 🆕 중단 및 재개 (v1.1.0)

- **Ctrl+C**로 중단 가능
- 중단 시 수집된 데이터는 자동으로 저장됩니다 (`*_중단_*.xlsx`)
- 매 10페이지마다 중간 저장 파일이 생성됩니다
- **자동 재개**: 다음 실행 시 중단된 지점부터 자동으로 계속됩니다
  - 체크포인트 파일: `crawl_checkpoint.json`
  - 재개 시 메시지 표시: `⚡ 중단된 크롤링 재개: 페이지 X부터 시작`

### 🆕 로그 확인 (v1.1.0)

로그 파일 위치: `logs/crawler_YYYYMMDD.log`

```bash
# 오늘 로그 보기
tail -f logs/crawler_20251006.log

# 에러만 필터링
grep ERROR logs/crawler_20251006.log
```

## 📊 출력 파일 형식

Excel (.xlsx) 또는 CSV (.csv) 형식으로 다음 정보를 포함합니다:

| 컬럼명 | 설명 |
|--------|------|
| 번호 | 게시글 번호 |
| 제목 | 입찰공고 제목 |
| 분류 | 공고 분류/유형 |
| 담당산림청 | 관할 지방산림청 |
| 담당부서 | 세부 담당 부서명 |
| 담당자 | 담당자 이름 |
| 연락처 | 전화번호/이메일 |
| 공고일자 | 게시 날짜 |
| 조회수 | 게시글 조회 수 |
| 첨부파일 | 첨부파일 유무 (O/공백) |
| 첨부파일링크 | 첨부파일 다운로드 링크 |
| URL | 상세 페이지 URL |

## ⚙️ 설정 변경

### 웹 앱 (app.py)
사이드바에서 실시간으로 조정 가능:
- **수집 기간**: 1~10년 (슬라이더)
- **요청 간 딜레이**: 0.5~3.0초
- **페이지 간 딜레이**: 0.5~5.0초

### CLI 버전 (main.py)
`main()` 함수에서 파라미터 조정:

```python
crawler = ForestBidCrawler(
    days=365,      # 수집 기간 (일 단위) - 웹앱에서는 years * 365
    delay=1.0,     # 요청 간 대기 시간 (초)
    page_delay=2.0 # 페이지 간 대기 시간 (초)
)
```

## ⚠️ 주의사항

### 기술적 제약
1. **서버 부하 최소화**: 기본 딜레이 설정(요청 1초, 페이지 2초) 유지 권장
   - 🆕 **최소값 강제**: 요청 0.5초, 페이지 1.0초 이하 설정 불가
2. **네트워크 안정성**: 안정적인 인터넷 연결 필수
   - 🆕 **자동 재시도**: 네트워크 오류 시 최대 3회 재시도 (지수 백오프, 최대 60초)
3. **수집 기간 제한**:
   - 🆕 **최대 10년**: 그 이상 설정 시 `ValueError` 발생
4. **장시간 실행**: 수집 기간에 따라 수 분~수십 분 소요
   - 1년: 약 5~10분
   - 5년: 약 30~60분
   - 10년: 약 1~2시간
   - 🆕 **중단 후 재개 가능**: Ctrl+C로 중단 후 재실행 시 자동 계속

### 법적 준수
5. **공개 정보만 수집**: 산림청 공개 입찰 공고만 대상
6. **연구/학술 목적**: 상업적 이용 금지
7. **파일 다운로드**: 브라우저 기본 다운로드 폴더에 저장됨 (~/Downloads)

## 🚀 배포 방법

자세한 배포 가이드는 [DEPLOY.md](DEPLOY.md)를 참고하세요.

### 빠른 배포 (Streamlit Cloud)

1. GitHub에 코드 업로드
2. https://streamlit.io/cloud 에서 배포
3. 클릭 몇 번으로 완료!

### 지원 플랫폼

- ✅ Streamlit Cloud (무료, 권장)
- ✅ Hugging Face Spaces
- ✅ Heroku
- ✅ Docker
- ✅ AWS/GCP

## 문제 해결

### requests 오류
```bash
pip install --upgrade requests
```

### 엑셀 파일 열리지 않음
```bash
pip install --upgrade openpyxl
```

### Streamlit 포트 변경
```bash
streamlit run app.py --server.port 8080
```

### 파싱 오류
- 산림청 웹사이트 구조가 변경되었을 수 있습니다
- `plan.md`를 참고하여 셀렉터를 수정하세요

### 테스트
간단한 유닛 테스트를 실행하려면(추가 필요):

```bash
python -m pytest tests/
```

## 라이센스

개인 연구용

## 작성자

산림공학 전문가 / 산림학 연구자
