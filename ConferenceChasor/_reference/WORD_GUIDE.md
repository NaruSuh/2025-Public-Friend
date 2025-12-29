# 워드 파일 사용 가이드

## 워드 파일로 보고서 출력하기 (강력 추천!)

워드 형식으로 출력하면 바로 제출 가능한 전문적인 보고서가 생성됩니다.

### 기본 사용법

```bash
python generate_report.py --data data/survey.csv --config config.json --format docx
```

### 생성되는 내용

워드 보고서에는 다음이 모두 포함됩니다:

✅ **전문적인 서식**
- 제목과 부제목 스타일
- 한글 폰트 (맑은 고딕)
- 적절한 여백과 간격

✅ **구조화된 표**
- 메타데이터 표 (조사 기간, 응답자 수 등)
- 통계 데이터 표
- 항목별 점수 표

✅ **강조 박스**
- 경영진 요약 하이라이트
- 주요 인사이트 강조

✅ **불릿 포인트**
- 응답 분포
- 주관식 응답 샘플
- 개선 권장사항

✅ **바로 편집 가능**
- 모든 텍스트 수정 가능
- 서식 변경 가능
- 추가 내용 삽입 가능

---

## 워드 파일에서 데이터 읽기

워드 파일의 표로 정리된 설문 데이터를 CSV로 변환할 수 있습니다.

### 1단계: 워드 파일 확인

```bash
# 워드 파일에 어떤 표들이 있는지 확인
python convert_docx_to_csv.py data/survey.docx --list
```

출력 예시:
```
'data/survey.docx' 파일의 표 목록:
============================================================
총 표 개수: 2개

표 0:
  - 행 수: 21
  - 열 수: 8
  - 헤더: ['응답자ID', '전체만족도', '내용품질', ...]

표 1:
  - 행 수: 5
  - 열 수: 3
  - 헤더: ['항목', '평균', '표준편차']
============================================================
```

### 2단계: CSV로 변환

```bash
# 첫 번째 표 (인덱스 0) 변환
python convert_docx_to_csv.py data/survey.docx data/survey.csv

# 두 번째 표 (인덱스 1) 변환
python convert_docx_to_csv.py data/survey.docx data/survey.csv --table 1
```

### 3단계: 보고서 생성

```bash
python generate_report.py --data data/survey.csv --config config.json --format docx
```

---

## 실제 사용 예시

### 시나리오 1: CSV 데이터 → 워드 보고서

```bash
# 가장 간단한 방법
python generate_report.py \
  --data data/my_survey.csv \
  --config config.json \
  --format docx
```

결과: `output/survey_report_my_survey.docx` 생성됨

### 시나리오 2: 워드 데이터 → 워드 보고서

```bash
# 1. 워드 표를 CSV로 변환
python convert_docx_to_csv.py data/raw_data.docx data/converted.csv

# 2. 워드 보고서 생성
python generate_report.py --data data/converted.csv --config config.json --format docx
```

결과: `output/survey_report_converted.docx` 생성됨

### 시나리오 3: 출력 파일명 지정

```bash
python generate_report.py \
  --data data/survey.csv \
  --config config.json \
  --format docx \
  --output ~/Desktop/최종보고서.docx
```

결과: `~/Desktop/최종보고서.docx` 생성됨

---

## 워드 보고서 편집하기

생성된 워드 파일을 MS Word나 LibreOffice에서 열어서:

1. **내용 수정**
   - 텍스트 직접 편집 가능
   - 추가 설명 삽입 가능

2. **서식 변경**
   - 폰트, 색상 변경
   - 표 스타일 수정

3. **내용 추가**
   - 이미지, 차트 삽입
   - 페이지 번호 추가
   - 헤더/푸터 설정

4. **바로 제출**
   - PDF로 변환
   - 이메일로 전송
   - 인쇄

---

## 팁과 트릭

### 팁 1: 여러 형식으로 동시 생성

```bash
# 마크다운 버전
python generate_report.py --data data/survey.csv --config config.json --format markdown

# 워드 버전 (제출용)
python generate_report.py --data data/survey.csv --config config.json --format docx

# HTML 버전 (웹 게시용)
python generate_report.py --data data/survey.csv --config config.json --format html
```

### 팁 2: 워드 파일의 특정 표만 추출

여러 표가 있는 워드 파일에서 원하는 표만 선택:

```bash
# 먼저 모든 표 확인
python convert_docx_to_csv.py data/report.docx --list

# 원하는 표 번호 확인 후 추출
python convert_docx_to_csv.py data/report.docx data/extracted.csv --table 2
```

### 팁 3: 배치 처리

여러 설문 파일을 한 번에 처리:

```bash
# Bash 스크립트
for file in data/*.csv; do
    python generate_report.py \
        --data "$file" \
        --config config.json \
        --format docx \
        --output "output/$(basename $file .csv).docx"
done
```

---

## 문제 해결

### Q: 워드 파일이 깨져 보입니다
A: `python-docx` 패키지가 설치되었는지 확인하세요
```bash
pip install python-docx
```

### Q: 한글이 제대로 표시되지 않습니다
A: 시스템에 맑은 고딕 폰트가 설치되어 있는지 확인하세요

### Q: 표가 너무 작아요
A: 생성된 워드 파일을 열어서 표를 선택하고 크기를 조절할 수 있습니다

### Q: 워드에서 "질문: 답변" 형식의 데이터는요?
A: `convert_docx_to_csv.py`는 표 형식만 지원합니다.
   텍스트 형식 데이터는 수동으로 CSV로 정리해주세요.

---

## 다음 단계

1. ✅ 샘플 데이터로 테스트
2. ✅ 자신의 데이터로 워드 보고서 생성
3. ✅ 생성된 보고서 확인 및 편집
4. ✅ 제출!

**축하합니다! 아침까지 보고서 완성!** 🎉
