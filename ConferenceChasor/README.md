# ConferenceChasor

로컬에서 구글 폼(또는 스프레드시트) 응답을 불러와 세미나 수료증 PDF를 일괄 생성하는 간단한 CLI 툴입니다.

## 빠른 시작

```bash
cd /home/naru/skyimpact/2025-Public-Friend/ConferenceChasor
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.yaml config.yaml  # 필요 시 수정
python -m certgen samples/responses.xlsx --config config.yaml --output output
```

`samples/responses.xlsx` 는 예제 데이터이며, `config.yaml` 에 필드 매핑이나 행사 정보를 맞춰 적으면 됩니다. 실행 후 `output/` 디렉터리에 PDF가 생성됩니다.

## 웹 인터페이스 사용

파일 업로드만으로 발급하려면 Flask 서버를 실행하면 됩니다.

```bash
cd /home/naru/skyimpact/2025-Public-Friend/ConferenceChasor
pip install -r requirements.txt  # 최초 1회
python app.py  # 또는 FLASK_APP=app.py flask run
```

브라우저에서 `http://localhost:8000` 에 접속한 뒤,

1. Google Form Excel/CSV 파일을 업로드합니다.
2. 필요하면 커스텀 `config.yaml` 도 함께 올립니다.
3. (선택) 시트 이름, 최대 발급 수를 입력합니다.
4. **ZIP 생성** 버튼을 누르면 참가별 PDF 가 ZIP 으로 다운로드됩니다.

## 구성 요소

- `certgen/config_loader.py`: YAML 설정을 dataclass 구조로 불러옵니다.
- `certgen/data_loader.py`: Excel/CSV 파일을 읽고 참가자 목록을 생성합니다.
- `certgen/generator.py`: ReportLab 으로 PDF 템플릿을 그립니다.
- `certgen/runner.py`: CLI 인자 파싱과 전체 파이프라인 제어.
- `config.example.yaml`: 필드명/레이아웃/필터링 등 참고용 기본 설정.
- `samples/responses.xlsx`: 테스트용 Google Form 응답 샘플.

## 설정값 설명

`config.yaml` 의 주요 항목은 다음과 같습니다.

- `event`: 행사명, 부제, 문구, 하단 서명 정보를 지정.
- `layout`: 종이 방향, 배경/테두리 색상, 폰트 이름 등 시각 요소.
- `columns`: 시트의 컬럼명과 매핑 (`Full Name`, `Affiliation`, `Completion Date` 등).
- `filters`: 특정 컬럼이 어떤 값일 때만 발급하도록 제한 (예: `Status == Attended`).
- `input`: 불러올 시트 이름, 날짜 출력 포맷, 로캘 등.
- `output`: 결과 PDF 경로 및 파일명 패턴 (`{name}`, `{event}` 플레이스홀더 사용 가능).

## 시트 준비 가이드

1. Google Form 응답을 Excel 또는 CSV 로 다운로드합니다.
2. `columns` 섹션에 실제 컬럼명을 정확히 입력합니다.
3. 참석자만 발급하려면 `filters.column` 과 `filters.equals` 를 설정합니다.
4. `Completion Date` 가 비어 있으면 실행일 기준 날짜가 들어갑니다.

## 자주 하는 커스터마이징

- **폰트 변경**: `layout.font.heading` 및 `layout.font.body` 에 ReportLab 이 인식하는 폰트명을 적거나, `reportlab.pdfbase.ttfonts.TTFont` 를 등록하는 코드를 추가해 원하는 TTF 를 사용할 수 있습니다.
- **디자인 교체**: `generator.py` 의 `_draw_*` 함수를 수정하여 배경 이미지를 깔거나 배치 좌표를 조정하면 됩니다.
- **QR 코드 삽입**: `reportlab.graphics.barcode.qr` 모듈을 가져와 `_draw_footer` 에서 `participant.raw` 데이터를 바탕으로 QR 코드를 추가하세요.

## 테스트 실행 예시

```bash
python -m certgen samples/responses.xlsx --config config.example.yaml --output demo_output --limit 2 --verbose
```

위 명령은 샘플 응답 중 `Status == Attended` 인 2명에 대해서만 PDF 를 생성하며, 작업 로그를 자세히 출력합니다.
