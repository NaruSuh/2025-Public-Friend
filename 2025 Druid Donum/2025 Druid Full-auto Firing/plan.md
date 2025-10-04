# 구현 계획 (Technical Design)

## 1. 아키텍처 개요

```
main.py
├── ForestBidCrawler (메인 크롤러 클래스)
│   ├── __init__() - 초기화 및 설정
│   ├── fetch_list_page() - 리스트 페이지 가져오기
│   ├── parse_list_page() - 리스트 파싱
│   ├── fetch_detail_page() - 상세 페이지 가져오기
│   ├── parse_detail_page() - 상세 정보 추출
│   ├── crawl() - 메인 크롤링 로직
│   └── save_to_excel() - 엑셀 저장
└── main() - 실행 진입점
```

## 2. 기술 스택

### 필수 라이브러리
```python
requests          # HTTP 요청
beautifulsoup4    # HTML 파싱
pandas            # 데이터 처리
openpyxl          # 엑셀 저장
lxml              # 빠른 파싱
```

### 선택적 라이브러리 (필요시)
```python
selenium          # JavaScript 동적 로딩이 requests로 불가능할 경우
webdriver-manager # Selenium 드라이버 자동 관리
tqdm              # 진행률 표시
```

## 3. 페이지 구조 분석

### 3.1 리스트 페이지 구조
```
URL 패턴:
https://www.forest.go.kr/kfsweb/cop/bbs/selectBoardList.do?
  mn=NKFS_04_01_04
  &bbsId=BBSMSTR_1033
  &pageIndex={1-421}
  &pageUnit=10
```

**추출 가능 정보 (리스트뷰)**:
- 게시글 번호
- 제목
- 상세 페이지 링크
- 부서명 (일부)
- 게시 날짜
- 조회수
- 첨부파일 유무

### 3.2 상세 페이지 구조
**추가 추출 정보**:
- 담당산림청
- 담당부서 (상세)
- 담당자 이름
- 연락처 (전화번호/이메일)
- 공고 전문
- 첨부파일 다운로드 링크

## 4. 크롤링 전략

### 4.1 페이지 수집 순서
```
1. pageIndex=1부터 시작
2. 각 페이지에서 10개 게시글 링크 수집
3. 각 게시글 상세 페이지 접근
4. 필요 정보 추출
5. 다음 페이지로 이동
6. 1년치 데이터 수집 완료시 중단
```

### 4.2 1년치 데이터 판단 기준
- 게시 날짜가 `현재 날짜 - 365일` 이전이면 중단
- 또는 사용자 지정 시작/종료 날짜 사용

### 4.3 요청 제한 (Rate Limiting)
```python
DELAY_BETWEEN_REQUESTS = 1.0  # 초 단위
DELAY_BETWEEN_PAGES = 2.0     # 페이지 간 딜레이
MAX_RETRIES = 3               # 실패 시 재시도 횟수
TIMEOUT = 10                  # 요청 타임아웃
```

## 5. 데이터 구조

### 5.1 수집 데이터 딕셔너리
```python
bid_info = {
    'number': int,              # 게시글 번호
    'title': str,               # 제목
    'category': str,            # 분류
    'forest_office': str,       # 담당산림청
    'department': str,          # 담당부서
    'manager': str,             # 담당자
    'contact': str,             # 연락처
    'post_date': str,           # 공고일자 (YYYY-MM-DD)
    'deadline': str,            # 마감일자 (YYYY-MM-DD)
    'views': int,               # 조회수
    'attachments': str,         # 첨부파일 링크 (콤마 구분)
    'url': str                  # 상세 페이지 URL
}
```

### 5.2 엑셀 출력 컬럼
```
번호 | 제목 | 분류 | 담당산림청 | 담당부서 | 담당자 | 연락처 |
공고일자 | 마감일자 | 조회수 | 첨부파일 | URL
```

## 6. 에러 처리 전략

### 6.1 네트워크 에러
```python
try:
    response = requests.get(url, timeout=TIMEOUT)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    # 재시도 로직
    # 실패 시 로그 기록 및 스킵
```

### 6.2 파싱 에러
```python
try:
    data = soup.select('selector')
    value = data[0].text.strip()
except (IndexError, AttributeError):
    value = 'N/A'  # 기본값 설정
```

### 6.3 진행상황 저장
- 매 10페이지마다 중간 저장 (임시 엑셀)
- 중단 시 재시작 가능하도록 체크포인트 저장

## 7. 성능 최적화

### 7.1 세션 재사용
```python
session = requests.Session()
# 헤더 설정으로 일반 브라우저처럼 위장
session.headers.update({
    'User-Agent': 'Mozilla/5.0 ...',
    'Accept-Language': 'ko-KR,ko;q=0.9'
})
```

### 7.2 멀티스레딩 (선택적)
- 너무 빠른 요청은 IP 차단 위험
- 기본은 순차 처리, 필요시만 적용

## 8. 구현 단계

### Phase 1: 기본 크롤러 구현
- [x] 리스트 페이지 요청 및 파싱
- [ ] 상세 페이지 요청 및 파싱
- [ ] 데이터 추출 로직

### Phase 2: 데이터 수집
- [ ] 페이지네이션 구현
- [ ] 1년치 데이터 필터링
- [ ] 에러 처리 및 재시도

### Phase 3: 저장 및 최적화
- [ ] pandas DataFrame 변환
- [ ] 엑셀 파일 저장
- [ ] 진행상황 표시
- [ ] 중간 저장 기능

## 9. 실행 방법

```bash
# 의존성 설치
pip install requests beautifulsoup4 pandas openpyxl lxml

# 실행
python main.py

# 옵션 (향후 추가 가능)
python main.py --days 365        # 최근 365일 데이터
python main.py --output custom.xlsx  # 출력 파일명 지정
python main.py --resume          # 중단된 작업 재개
```

## 10. 주의사항

1. **로봇 배제 표준 (robots.txt) 확인**
2. **과도한 요청 자제** - 딜레이 설정 필수
3. **페이지 구조 변경 대비** - 유연한 셀렉터 사용
4. **개인정보 보호** - 수집 데이터 보안 관리
5. **법적 책임** - 공개된 정보만 수집, 연구 목적 명시

## 11. 향후 개선 방향

- [ ] GUI 인터페이스 추가 (PyQt/Tkinter)
- [ ] 실시간 알림 기능 (새 공고 발생 시)
- [ ] 데이터베이스 연동 (SQLite/PostgreSQL)
- [ ] 키워드 필터링 기능
- [ ] 자동 스케줄링 (cron/Task Scheduler)
