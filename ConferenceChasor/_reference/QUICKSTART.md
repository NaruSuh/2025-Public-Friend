# 빠른 시작 가이드

## 1분 안에 보고서 생성하기!

### Step 1: 패키지 설치

```bash
cd ~/survey-report-generator
pip install -r requirements.txt
```

### Step 2: API 키 설정

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

또는 `.bashrc` / `.zshrc`에 추가:
```bash
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### Step 3: 샘플 보고서 생성

```bash
python generate_report.py --data data/sample_survey.csv --config config.json
```

생성 완료! `output/` 폴더를 확인하세요.

---

## 자신의 데이터로 보고서 만들기

### 1. 데이터 파일 준비

`data/` 폴더에 CSV 또는 Excel 파일을 복사합니다:

```bash
cp /path/to/your/survey.csv ~/survey-report-generator/data/
```

### 2. config.json 수정

```json
{
  "conference_name": "당신의 학회명",
  "survey_date": "2024년 11월",

  "score_columns": [
    "만족도_컬럼명1",
    "만족도_컬럼명2"
  ],

  "column_labels": {
    "만족도_컬럼명1": "전체 만족도",
    "만족도_컬럼명2": "내용 품질"
  },

  "text_columns": {
    "주관식_컬럼명": "좋았던 점"
  }
}
```

**중요**: `score_columns`와 `text_columns`의 키는 실제 CSV 파일의 컬럼명과 정확히 일치해야 합니다!

### 3. 보고서 생성

```bash
python generate_report.py --data data/your_survey.csv --config config.json
```

---

## 출력 형식 변경

### Markdown (기본)
```bash
python generate_report.py --data data/survey.csv --format markdown
```

### HTML
```bash
python generate_report.py --data data/survey.csv --format html
```

### 워드 (추천! 바로 제출 가능)
```bash
python generate_report.py --data data/survey.csv --format docx
```

---

## 문제 해결

### Q: API 키 오류가 납니다
A: `export ANTHROPIC_API_KEY='your-key'` 명령을 실행했는지 확인하세요.

### Q: 컬럼을 찾을 수 없다고 합니다
A: config.json의 컬럼명이 CSV 파일의 실제 컬럼명과 정확히 일치하는지 확인하세요.
   - CSV 파일 헤더를 먼저 확인: `head -1 data/your_survey.csv`

### Q: 한글이 깨집니다
A: CSV 파일을 UTF-8 인코딩으로 저장하거나 Excel(.xlsx) 형식을 사용하세요.

---

## 고급 팁

### 여러 데이터 파일 한 번에 처리
```bash
for file in data/*.csv; do
  python generate_report.py --data "$file" --config config.json
done
```

### 특정 출력 경로 지정
```bash
python generate_report.py \
  --data data/survey.csv \
  --config config.json \
  --output ~/Desktop/final_report.md
```

---

완료! 이제 아침까지 보고서 작성 끝! 🎉
