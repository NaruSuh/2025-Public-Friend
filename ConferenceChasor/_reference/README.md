# 학회 참석자 만족도 조사 보고서 자동 생성기

LLM과 통계 분석을 결합하여 설문조사 데이터를 전문적인 보고서로 자동 변환해주는 시스템입니다.

## 주요 기능

- **자동 통계 분석**: CSV/Excel/Word 설문조사 데이터의 평균, 분포, 만족도 지수 등 자동 계산
- **AI 기반 텍스트 생성**: Claude AI를 활용한 자연스러운 보고서 텍스트 작성
- **다양한 입출력 형식**:
  - 입력: CSV, Excel(.xlsx), Word(.docx) 지원
  - 출력: Markdown, HTML, Word(.docx) 지원
- **완전 자동화**: 데이터 입력 → 통계 분석 → LLM 텍스트 생성 → 보고서 출력까지 원클릭

## 설치

```bash
# 1. 저장소 이동
cd ~/survey-report-generator

# 2. 필요한 패키지 설치
pip install -r requirements.txt

# 3. Anthropic API 키 설정
export ANTHROPIC_API_KEY='your-api-key-here'
```

## 빠른 시작

### 1. 샘플 데이터로 테스트

```bash
python generate_report.py --data data/sample_survey.csv --config config.json
```

생성된 보고서는 `output/survey_report_sample_survey.md`에 저장됩니다.

### 2. 자신의 데이터 사용하기

#### 데이터 준비
설문조사 데이터를 CSV 또는 Excel 형식으로 준비합니다.

예시 구조:
```csv
overall_satisfaction,content_quality,speaker_quality,positive_feedback
5,4,5,발표가 훌륭했습니다
4,4,3,네트워킹 기회가 좋았습니다
...
```

#### 설정 파일 작성
`config.json` 파일을 수정하여 보고서를 커스터마이징합니다:

```json
{
  "conference_name": "2024 AI 국제학회",
  "survey_date": "2024년 11월",
  "estimated_attendees": "350명",

  "score_columns": [
    "overall_satisfaction",
    "content_quality",
    "speaker_quality"
  ],

  "column_labels": {
    "overall_satisfaction": "전체 만족도",
    "content_quality": "발표 내용의 질",
    "speaker_quality": "발표자 수준"
  },

  "text_columns": {
    "positive_feedback": "좋았던 점",
    "improvement_suggestions": "개선 제안사항"
  }
}
```

#### 보고서 생성

```bash
# 기본 사용 (Markdown)
python generate_report.py --data your_data.csv --config config.json

# HTML 형식으로 생성
python generate_report.py --data your_data.csv --config config.json --format html

# 워드 형식으로 생성 (바로 제출 가능!)
python generate_report.py --data your_data.csv --config config.json --format docx

# 출력 경로 지정
python generate_report.py --data your_data.csv --output reports/final_report.md
```

## 사용법

### 명령행 옵션

```
python generate_report.py [옵션]

필수 옵션:
  --data PATH        설문조사 데이터 파일 (CSV, Excel, Word)

선택 옵션:
  --config PATH      설정 파일 (JSON, 기본값: config.json)
  --format FORMAT    출력 형식 (markdown, html, docx 중 선택, 기본값: markdown)
  --output PATH      출력 파일 경로 (지정 안하면 자동 생성)
```

### 예시

```bash
# 1. 최소 옵션 (설정 파일 없이)
python generate_report.py --data data/survey.csv

# 2. 워드 파일로 출력 (추천!)
python generate_report.py \
  --data data/survey.csv \
  --config config.json \
  --format docx

# 3. 전체 옵션 사용
python generate_report.py \
  --data data/survey.csv \
  --config config.json \
  --format html \
  --output output/final_report.html

# 4. Excel 파일 사용
python generate_report.py --data data/survey.xlsx --config config.json

# 5. 워드 파일에서 데이터 읽기 (먼저 CSV로 변환 필요)
python convert_docx_to_csv.py data/survey.docx data/survey.csv
python generate_report.py --data data/survey.csv --config config.json
```

## 설정 파일 상세

### score_columns
숫자형 평점 컬럼 (1-5점 척도 등)을 지정합니다.

```json
"score_columns": [
  "overall_satisfaction",
  "content_quality"
]
```

### column_labels
컬럼명을 한글 표시명으로 매핑합니다.

```json
"column_labels": {
  "overall_satisfaction": "전체 만족도",
  "content_quality": "발표 내용의 질"
}
```

### text_columns
주관식 텍스트 응답 컬럼을 지정합니다.

```json
"text_columns": {
  "positive_feedback": "좋았던 점",
  "improvement_suggestions": "개선 제안사항"
}
```

## 생성되는 보고서 구조

1. **경영진 요약** (Executive Summary)
   - AI가 전체 데이터를 분석하여 핵심 내용 요약

2. **주요 지표**
   - 전체 만족도 지수 (0-100)
   - 만족도 등급 (매우 우수 / 우수 / 양호 / 보통 / 개선 필요)

3. **세부 항목별 분석**
   - 각 항목의 평균, 중앙값, 표준편차
   - 응답 분포 시각화
   - AI 생성 분석 텍스트

4. **주관식 응답 분석**
   - AI가 텍스트 응답에서 주요 테마 추출
   - 긍정/부정 피드백 분류
   - 주요 응답 샘플

5. **개선 권장사항**
   - 데이터 기반 구체적 제안

6. **결론**
   - 전체 평가 및 향후 전망

7. **부록**
   - 상세 통계 데이터 (JSON)

## 프로젝트 구조

```
survey-report-generator/
├── generate_report.py          # 메인 실행 스크립트
├── convert_docx_to_csv.py      # 워드 → CSV 변환 유틸리티
├── config.json                 # 설정 파일 (예시)
├── requirements.txt            # 패키지 의존성
├── README.md                   # 이 파일
├── QUICKSTART.md               # 빠른 시작 가이드
├── HOW_TO_USE.txt              # 간단 사용법
├── data/                       # 데이터 폴더
│   └── sample_survey.csv       # 샘플 데이터
├── output/                     # 생성된 보고서 저장
├── src/                        # 소스 코드
│   ├── data_processor.py       # 데이터 처리 및 통계 분석
│   ├── llm_generator.py        # LLM 텍스트 생성
│   ├── report_generator.py     # 보고서 통합 생성
│   └── docx_processor.py       # 워드 파일 입출력
└── templates/                  # (선택) 사용자 정의 템플릿
```

## 워드 파일 사용하기

### 워드 파일에서 데이터 읽기

워드 파일의 표 형태로 작성된 설문조사 데이터를 CSV로 변환할 수 있습니다.

```bash
# 워드 파일의 모든 표 목록 보기
python convert_docx_to_csv.py data/survey.docx --list

# 첫 번째 표를 CSV로 변환
python convert_docx_to_csv.py data/survey.docx data/survey.csv

# 특정 표 인덱스 지정 (예: 두 번째 표)
python convert_docx_to_csv.py data/survey.docx data/survey.csv --table 1

# 변환 후 보고서 생성
python generate_report.py --data data/survey.csv --config config.json
```

### 워드 파일로 보고서 출력

가장 추천하는 방법입니다! 워드 파일로 출력하면 바로 제출 가능합니다.

```bash
# 워드 파일로 보고서 생성
python generate_report.py --data data/survey.csv --config config.json --format docx

# 출력 파일명 지정
python generate_report.py \
  --data data/survey.csv \
  --config config.json \
  --format docx \
  --output reports/final_report.docx
```

생성된 워드 파일에는 다음이 포함됩니다:
- 전문적인 서식과 레이아웃
- 표와 차트
- 헤더와 섹션 구분
- 바로 편집 가능한 형식

## 고급 사용법

### Python 코드로 직접 사용

```python
from src.report_generator import SurveyReportGenerator

# 설정
config = {
    'conference_name': '2024 AI 학회',
    'score_columns': ['satisfaction', 'quality'],
    'column_labels': {
        'satisfaction': '만족도',
        'quality': '품질'
    }
}

# 보고서 생성
generator = SurveyReportGenerator('data/survey.csv', config)
generator.save_report('output/report.md', output_format='markdown')
```

### 데이터 분석만 수행

```python
from src.data_processor import SurveyDataProcessor

processor = SurveyDataProcessor('data/survey.csv')
processor.load_data()

# 기본 통계
stats = processor.get_basic_stats()
print(stats)

# 만족도 분석
satisfaction = processor.analyze_satisfaction_scores(['q1', 'q2'])
print(satisfaction)

# 만족도 지수
index = processor.calculate_satisfaction_index(['q1', 'q2'])
print(f"만족도 지수: {index}/100")
```

## 문제 해결

### API 키 오류
```
ValueError: ANTHROPIC_API_KEY가 설정되지 않았습니다
```

해결: 환경변수 설정
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

### 파일 인코딩 오류
CSV 파일이 UTF-8이 아닌 경우 발생할 수 있습니다.

해결: CSV를 UTF-8로 저장하거나, Excel 형식(.xlsx) 사용

### 컬럼명 찾을 수 없음
```
ValueError: 컬럼 'satisfaction'을 찾을 수 없습니다
```

해결: config.json의 score_columns 값이 실제 CSV 컬럼명과 일치하는지 확인

## 라이선스

이 프로젝트는 학술 및 개인 사용을 위해 자유롭게 사용 가능합니다.

## 기여

개선 사항이나 버그 리포트는 이슈로 등록해주세요.

---

**만든이**: AI 기반 자동화 도구
**생성일**: 2024년
**버전**: 1.0
