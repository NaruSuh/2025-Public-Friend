# 🌲 산림청 입찰정보 크롤러

산림청 웹사이트의 입찰공고 정보를 자동으로 수집하여 엑셀 파일로 저장하는 프로그램입니다.

## 🎯 사용 방법

### 🖥️ Streamlit 웹 앱 (권장)

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속

### 💻 CLI 버전

```bash
python3 main.py
```

## 프로젝트 구조 (3-Files System)

```
2025 Druid Full-auto Firing/
├── prompt.md          # 프로젝트 명세 및 요구사항
├── plan.md           # 구현 계획 및 아키텍처
├── main.py           # 크롤러 엔진
├── app.py            # Streamlit 웹 앱
├── requirements.txt  # 의존성 라이브러리
├── DEPLOY.md         # 배포 가이드
└── README.md         # 사용 설명서 (본 문서)
```

## 설치 방법

### 1. Python 환경 확인
Python 3.8 이상이 필요합니다.

```bash
python --version
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

또는 개별 설치:

```bash
pip install requests beautifulsoup4 pandas openpyxl lxml streamlit
```

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

### 중단 및 재개

- **Ctrl+C**로 중단 가능
- 중단 시 수집된 데이터는 자동으로 저장됩니다
- 매 10페이지마다 중간 저장 파일이 생성됩니다

## 출력 파일 형식

엑셀 파일 (.xlsx) 형식으로 다음 정보를 포함합니다:

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

## 설정 변경

`main.py`의 `main()` 함수에서 다음 파라미터를 조정할 수 있습니다:

```python
crawler = ForestBidCrawler(
    days=365,      # 수집 기간 (일 단위)
    delay=1.0,     # 요청 간 대기 시간 (초)
    page_delay=2.0 # 페이지 간 대기 시간 (초)
)
```

## 주의사항

1. **서버 부하 최소화**: 기본 딜레이 설정을 유지하세요
2. **네트워크 안정성**: 안정적인 인터넷 연결 필요
3. **장시간 실행**: 전체 크롤링에 수 시간 소요 가능
4. **법적 준수**: 공개된 정보만 수집, 연구 목적 사용

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

## 라이센스

개인 연구용

## 작성자

산림공학 전문가 / 산림학 연구자
