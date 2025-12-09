# ConferenceChasor 안정성 관점에서의 평가 및 개선 제안

## 1. 개요

ConferenceChasor 프로젝트는 명확한 모듈 구조와 설정 파일 기반의 유연성을 갖추고 있어 유지보수성이 좋은 기반을 가지고 있습니다. 하지만 실제 운영 환경에서 발생할 수 있는 다양한 예외 상황에 대한 고려가 부족하여, 안정성을 높이기 위한 몇 가지 개선이 필요합니다.

본 문서는 잠재적인 안정성 위험을 식별하고, 이를 해결하기 위한 구체적인 개선안을 제안합니다.

## 2. 주요 안정성 위험

1.  **예외 처리 부재**: 파일 누락, 설정 오류, 데이터 형식 불일치 등 예측 가능한 오류에 대한 처리 로직이 없어 프로그램이 예기치 않게 중단될 위험이 높습니다.
2.  **입력 유효성 검증 부족**: 설정 파일(`config.yaml`)의 값이나 입력 데이터(Excel/CSV)의 내용이 올바르다고 가정하고 있어, 잘못된 값이 들어올 경우 PDF 레이아웃이 깨지거나 오류가 발생할 수 있습니다.
3.  **자동화된 테스트의 부재**: 수동 테스트만으로는 코드 변경 시 기존 기능이 올바르게 동작하는지 보장하기 어렵습니다. 이는 기능 추가나 리팩토링 시 회귀 버그(regression bug)를 유발할 가능성을 높입니다.
4.  **리소스 관리 비효율**: 대용량 데이터 처리 시 모든 데이터를 메모리에 한 번에 로드하는 방식은 메모리 부족 문제를 일으킬 수 있습니다.
5.  **비구조적인 로깅**: `--verbose` 옵션만으로는 오류의 원인을 추적하거나 디버깅하기에 정보가 부족합니다.

## 3. 개선 제안

### 3.1. 강력한 예외 처리 (Robust Error Handling)

**문제점**: `FileNotFoundError`, `KeyError` 등 파일이나 데이터 접근 실패 시 프로그램이 그대로 중단됩니다.

**개선안**:
- **파일 접근**: `try...except FileNotFoundError` 블록을 사용하여 `config.yaml` 이나 입력 데이터 파일이 없을 때 사용자에게 명확한 에러 메시지를 출력하도록 합니다.
- **데이터 처리**: `data_loader.py`에서 Excel/CSV 파일을 읽을 때, `config.yaml`에 명시된 컬럼이 실제 파일에 없는 경우 `KeyError`를 처리하여 어떤 컬럼이 누락되었는지 알려줍니다.
- **PDF 생성**: `generator.py`에서 잘못된 폰트 이름이나 색상 코드 등으로 ReportLab 라이브러리가 오류를 발생시킬 때, 이를 감지하여 해당 설정을 수정하도록 안내하는 메시지를 출력합니다.

```python
# 예시: certgen/runner.py
try:
    config = load_config(args.config)
    participants = load_data(args.input_file, config)
    generate_all_certificates(participants, config)
except FileNotFoundError as e:
    print(f"오류: 파일을 찾을 수 없습니다 - {e.filename}")
except KeyError as e:
    print(f"오류: 설정 파일이나 데이터 파일에 필요한 키(컬럼)가 없습니다 - {e}")
except Exception as e:
    print(f"알 수 없는 오류가 발생했습니다: {e}")
```

### 3.2. 입력 유효성 검증 (Input Validation)

**문제점**: 이름이 매우 길거나, 날짜 형식이 잘못된 데이터가 들어오면 PDF 출력이 깨지거나 오류가 발생합니다.

**개선안**:
- **설정 파일 검증**: `certgen/config_loader.py`에서 YAML 파일을 로드한 후, 필수 키가 모두 존재하는지, 특정 값(e.g., 색상, 폰트)이 유효한지 검사하는 로직을 추가합니다. Pydantic 같은 라이브러리를 사용하면 dataclass 정의에 유효성 검증 규칙을 쉽게 추가할 수 있습니다.
- **데이터 정제(Sanitization)**: `data_loader.py`에서 각 참가자 데이터를 읽어올 때, 이름이나 소속과 같은 문자열 길이를 적절히 제한하거나, 날짜 형식이 올바른지 확인하고 파싱하는 단계를 추가합니다.

### 3.3. 자동화된 테스트 도입 (Automated Testing)

**문제점**: 기능 수정 후 예상치 못한 부분에서 버그가 발생해도 사전에 감지하기 어렵습니다.

**개선안**:
- **테스트 프레임워크 도입**: `pytest`를 `requirements.txt`에 추가하고, 프로젝트 루트에 `tests/` 디렉토리를 생성합니다.
- **단위 테스트(Unit Tests)**:
    - `tests/test_data_loader.py`: 정상적인 CSV, 비어있는 CSV, 특정 컬럼이 없는 CSV 등을 입력했을 때 각각 의도대로 동작하는지 테스트합니다.
    - `tests/test_config_loader.py`: 필수 키가 누락된 `config.yaml`을 로드할 때 오류가 발생하는지 테스트합니다.
- **통합 테스트(Integration Test)**: `tests/test_integration.py`에서 샘플 데이터와 설정을 이용해 `runner.py`의 메인 함수를 실행하고, 실제로 `output` 디렉터리에 예상된 PDF 파일이 생성되는지, 내용은 올바른지(간단한 텍스트 존재 여부 등)를 확인하는 테스트를 작성합니다.

### 3.4. 효율적인 데이터 처리 및 리소스 관리

**문제점**: 수만 건의 수료증 생성 시 메모리 사용량이 급증할 수 있습니다.

**개선안**:
- **스트리밍/이터레이터 방식 적용**: `data_loader.py`에서 Pandas `read_excel`/`read_csv` 사용 시 `chunksize` 옵션을 활용하거나, `openpyxl` 등의 라이브러리로 데이터를 한 줄씩 읽고 처리(yield)하도록 수정하여 메모리 사용량을 최소화합니다.
- **안전한 파일 핸들링**: 모든 파일 입출력 시 `with open(...) as f:` 구문을 사용하여, 오류 발생 시에도 파일 핸들이 자동으로 닫히도록 보장합니다.

### 3.5. 구조화된 로깅 (Structured Logging)

**문제점**: 오류 발생 시 원인 파악이 어렵고, 정상 동작 중에도 진행 상황을 체계적으로 보기 어렵습니다.

**개선안**:
- **`logging` 모듈 사용**: `print()` 함수 대신 Python 표준 라이브러리인 `logging`을 사용하도록 전면 교체합니다.
- **로그 레벨 분리**:
    - `INFO`: 참가자 몇 명을 처리 중인지 등 일반적인 진행 상황.
    - `WARNING`: 특정 참가자의 데이터가 비어있어 기본값으로 대체하는 등의 잠재적 문제 상황.
    - `ERROR`: 파일 누락, 키 오류 등 명백한 에러 상황.
- **로그 출력 제어**: `--verbose` 플래그는 `INFO` 레벨 이상을, 평상시에는 `WARNING` 레벨 이상만 콘솔에 출력하도록 설정합니다. `--log-file` 옵션을 추가하여 모든 로그를 파일로 남길 수 있게 하면 디버깅에 매우 유용합니다.

```python
# 예시: certgen/runner.py 상단에 로거 설정
import logging

# ...
if args.verbose:
    logging.basicConfig(level=logging.INFO)
else:
    logging.basicConfig(level=logging.WARNING)

logging.info(f"{len(participants)}명의 참가자 데이터를 불러왔습니다.")
```
