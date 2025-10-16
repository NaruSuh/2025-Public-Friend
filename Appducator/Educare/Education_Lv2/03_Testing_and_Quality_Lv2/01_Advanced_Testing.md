# 03 - Testing and Quality - Lv.2: Advanced Testing Strategies
# 03 - 테스트와 품질 - Lv.2: 고급 테스트 전략

You've mastered unit testing with `pytest`. Level 2 is about expanding your testing pyramid to build confidence in the *interactions* between components and the behavior of the system as a whole.
`pytest`로 단위 테스트를 익혔다면, 레벨 2에서는 테스트 피라미드를 확장하여 구성 요소 간 상호작용과 시스템 전체 행동에 대한 신뢰를 확보합니다.

## Before You Begin
## 시작하기 전에
-   Re-run the Level 1 pytest exercises so fixtures, parametrization, and coverage reports are familiar.
-   레벨 1의 pytest 실습을 다시 수행하여 픽스처, 파라미터화, 커버리지 리포트에 익숙해지세요.
-   Ensure Docker Desktop or another container runtime is running; Testcontainers and contract-testing tools rely on it.
-   Docker Desktop 등 컨테이너 런타임이 실행 중인지 확인하세요. Testcontainers나 계약 테스트 도구가 이를 필요로 합니다.
-   Identify a realistic feature (e.g., Forest crawler ingestion) that you can test end-to-end while reading this guide.
-   Forest 크롤러 수집처럼 이 가이드를 따라가며 엔드투엔드로 테스트할 현실적인 기능을 정하세요.

## Level 2 Upgrade Goals
## 레벨 2 업그레이드 목표
1.  **Test outside-in:** prove integrations with real services instead of relying purely on mocks.
1.  **바깥에서 안으로 테스트하기:** 목에만 의존하지 말고 실제 서비스를 통합하여 검증합니다.
2.  **Automate confidence:** introduce property-based and mutation testing to surface hidden cases.
2.  **신뢰 자동화:** 속성 기반 테스트와 돌연변이 테스트를 도입해 숨겨진 경우를 찾아냅니다.
3.  **Document expectations:** capture the “why” of each test so teammates (or future you) understand its role in the pyramid.
3.  **기대치 문서화:** 각 테스트가 존재하는 이유를 기록해 팀원이나 미래의 나 자신이 피라미드에서의 역할을 이해하게 합니다.

## Core Concepts
## 핵심 개념

1.  **The Testing Pyramid**: A model for balancing your test suite. Have lots of fast, cheap unit tests at the base, fewer integration tests in the middle, and a very small number of slow, expensive end-to-end tests at the top.
1.  **테스트 피라미드**: 테스트 스위트를 균형 있게 구성하는 모델로, 바닥에는 빠르고 값싼 단위 테스트를 많이 두고, 중간에는 적당한 수의 통합 테스트, 꼭대기에는 느리고 비용이 큰 E2E 테스트를 소수 배치합니다.
2.  **Integration Testing**: Testing how multiple components of your application work together (e.g., does your API endpoint correctly write to the database?).
2.  **통합 테스트**: 애플리케이션의 여러 구성 요소가 함께 제대로 작동하는지 검증합니다(예: API 엔드포인트가 데이터베이스에 올바르게 기록하는지).
3.  **Contract Testing**: A way to ensure that two separate services (e.g., your API and a frontend client, or two microservices) can communicate with each other without having to run a full integration test.
3.  **계약 테스트**: 전체 통합 테스트를 수행하지 않고도 두 서비스(API와 프런트엔드, 두 마이크로서비스 등)가 서로 통신 가능한지 확인하는 방법입니다.
4.  **Property-Based Testing**: Instead of writing examples by hand, you define the *properties* of your functions and let a library generate hundreds of test cases to try and find edge cases you missed.
4.  **속성 기반 테스트**: 수동으로 예제를 만드는 대신 함수가 만족해야 할 *속성*을 정의하고, 라이브러리가 수백 개의 테스트 케이스를 생성해 놓친 경계 조건을 찾아냅니다.

---

## 1. Integration Testing with Testcontainers
## 1. Testcontainers로 통합 테스트하기

How do you test code that talks to a real database or message queue without mocking everything? `testcontainers` lets you programmatically spin up and tear down real services in Docker containers as part of your `pytest` suite.
실제 데이터베이스나 메시지 큐를 대상으로 하는 코드를 목 없이 어떻게 테스트할까요? `testcontainers`를 사용하면 `pytest` 스위트에서 도커 컨테이너로 진짜 서비스를 띄우고 내릴 수 있습니다.

**Why Testcontainers?**
**Testcontainers가 뛰어난 이유**
-   **High Fidelity**: You're testing against a real PostgreSQL or Redis, not a mock or an in-memory substitute like SQLite.
-   **높은 충실도**: 목이나 메모리 대체재가 아닌 실제 PostgreSQL 또는 Redis를 대상으로 테스트합니다.
-   **Isolation**: Each test run (or even each test function) can get a fresh, clean database instance.
-   **격리성**: 테스트 실행마다(심지어 테스트 함수마다) 새롭고 깨끗한 데이터베이스 인스턴스를 사용할 수 있습니다.
-   **Easy Integration**: It works seamlessly with `pytest` fixtures.
-   **쉬운 통합**: `pytest` 픽스처와 자연스럽게 연동됩니다.

**Install**: `pip install testcontainers[postgres]`
**설치**: `pip install testcontainers[postgres]`

### Example: An Integration Test for a FastAPI Endpoint
### 예시: FastAPI 엔드포인트 통합 테스트

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from testcontainers.postgres import PostgresContainer
from fastapi.testclient import TestClient

from ..src.main import app # Your FastAPI app
from ..src.database import Base # Your SQLAlchemy Base

@pytest.fixture(scope="session")
def postgres_container():
    """Spins up a PostgreSQL container for the test session."""
    with PostgresContainer("postgres:14-alpine") as postgres:
        yield postgres

@pytest.fixture(scope="session")
def db_engine(postgres_container):
    """Creates a SQLAlchemy engine connected to the test container."""
    engine = create_engine(postgres_container.get_connection_url())
    Base.metadata.create_all(bind=engine)
    yield engine

# This fixture will be used by your tests
@pytest.fixture(scope="function")
def test_client(db_engine):
    # Override the app's dependency to use the test database
    # This is a key pattern!
    app.dependency_overrides[get_db] = lambda: db_engine.connect()
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()

# tests/test_integration_users.py
def test_create_and_get_user(test_client):
    # Step 1: Create a user via the API
    response = test_client.post(
        "/api/v1/users/",
        json={"email": "integration@test.com", "password": "a_secure_password"}
    )
    assert response.status_code == 201
    user_data = response.json()
    assert user_data["email"] == "integration@test.com"
    user_id = user_data["id"]

    # Step 2: Retrieve the user via the API and verify
    response = test_client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    retrieved_user = response.json()
    assert retrieved_user["email"] == "integration@test.com"
```
This test provides very high confidence: it verifies that your HTTP layer, dependency injection, CRUD layer, and database schema all work together correctly.
이 테스트는 HTTP 계층, 의존성 주입, CRUD 계층, 데이터베이스 스키마가 올바르게 협력하는지 검증하므로 매우 높은 신뢰를 제공합니다.

**Practice:** add a fixture that seeds baseline data before each test and wipes it afterwards. Write a “sad path” test that asserts a `400` when validation fails, to ensure both success and failure paths work against the same containerized database.
**실습:** 각 테스트 전에 기본 데이터를 심고 이후 정리하는 픽스처를 추가하세요. 유효성 검사가 실패할 때 `400`을 기대하는 “슬픈 경로” 테스트를 작성해 성공/실패 경로 모두 같은 컨테이너화된 데이터베이스에서 동작하도록 하세요.

---

## 2. Property-Based Testing with Hypothesis
## 2. Hypothesis로 속성 기반 테스트 수행하기

Instead of thinking of examples, you think of *rules*. Hypothesis then generates hundreds of diverse examples to try and break your rules.
예시를 떠올리는 대신 *규칙*을 정의하면, Hypothesis가 수백 가지 다양한 입력을 생성해 그 규칙을 깨뜨리려 시도합니다.

**Install**: `pip install hypothesis`
**설치**: `pip install hypothesis`

Let's revisit our `parse_views` function from the first testing guide.
첫 번째 테스트 가이드에서 다뤘던 `parse_views` 함수를 다시 보겠습니다.

```python
# src/utils.py
def parse_views(text: str) -> int:
    if not isinstance(text, str):
        return 0
    try:
        return int(text.replace(",", "").strip())
    except (ValueError, TypeError):
        return 0
```

A property-based test would look like this:
속성 기반 테스트는 다음과 같습니다.

```python
# tests/test_property_utils.py
from hypothesis import given, strategies as st

from src.utils import parse_views

# Define a "strategy" for generating integers
integers_strategy = st.integers(min_value=-1_000_000, max_value=1_000_000)

@given(num=integers_strategy)
def test_parse_views_with_commas_property(num):
    """
    Property: For any integer, formatting it with commas and then parsing
    it should yield the original integer.
    """
    # 1. Create a test case from the generated number
    string_with_commas = f"{num:,}" # e.g., 12345 -> "12,345"
    
    # 2. Run the function and assert the property
    assert parse_views(string_with_commas) == num

@given(st.text())
def test_parse_views_does_not_crash(text):
    """
    Property: The function should never raise an unhandled exception,
    no matter what string it's given.
    """
    parse_views(text)
```
Hypothesis is incredibly smart. It will automatically generate inputs like:
Hypothesis는 매우 영리하여 다음과 같은 입력을 자동으로 생성합니다.
-   `0`
-   `0`
-   Large positive and negative numbers
-   매우 큰 양수와 음수
-   Empty strings `""`
-   빈 문자열 `""`
-   Strings with Unicode characters, emojis, null bytes `\x00`
-   유니코드 문자, 이모지, 널 바이트 `\x00`가 포함된 문자열
-   Strings that look like numbers but aren't, e.g., `"1,2,3"`
-   숫자처럼 보이지만 실제로는 아닌 문자열(예: `"1,2,3"`)

If it finds a failing example, it will "shrink" it to the smallest possible failing case, making debugging much easier. Property-based testing is a powerful tool for finding edge cases you would never have thought of.
실패 사례를 발견하면 가장 단순한 형태로 “축소”해 디버깅을 쉽게 만듭니다. 속성 기반 테스트는 미처 생각하지 못한 극단적 상황을 찾는 강력한 도구입니다.

**Practice:** pair each property-based test with an accompanying docstring explaining the business rule it protects. Share the failing examples Hypothesis discovers in your project journal so you remember to update requirements and docs.
**실습:** 속성 기반 테스트마다 보호하려는 비즈니스 규칙을 독스트링으로 설명하고, Hypothesis가 찾아낸 실패 사례를 프로젝트 저널에 기록해 요구사항과 문서를 업데이트할 수 있게 하세요.

---

## 3. Other Advanced Testing Concepts
## 3. 기타 고급 테스트 개념

-   **Mutation Testing**: Tools like `mutmut` automatically introduce small bugs (mutations) into your code (e.g., changing a `>` to a `<`) and then run your test suite. If your tests still pass, it means they aren't strong enough to catch that bug. The goal is to "kill" as many mutants as possible.
-   **돌연변이 테스트**: `mutmut` 같은 도구는 코드에 작은 버그(예: `>`를 `<`로 변경)를 자동으로 주입하고 테스트 스위트를 실행합니다. 테스트가 통과하면 결함을 잡지 못한 것이므로 더 강력한 테스트가 필요합니다.
-   **Visual Regression Testing**: For applications with a UI (like your Streamlit app), tools can take screenshots of components and compare them to a baseline. If a pixel changes, the test fails. This is great for preventing unintentional UI changes.
-   **시각적 회귀 테스트**: UI가 있는 애플리케이션(예: Streamlit 앱)의 경우, 도구가 컴포넌트를 스크린샷으로 찍어 기준과 비교합니다. 픽셀이 바뀌면 테스트가 실패하므로 의도치 않은 UI 변화를 막습니다.
-   **Test Coverage is Not a Goal**: A high test coverage percentage (e.g., 95%) doesn't guarantee your code is well-tested. It just means that 95% of your lines were executed. It doesn't tell you if your *assertions* are meaningful. Focus on testing behaviors and properties, not just on hitting lines of code.
-   **테스트 커버리지가 목표가 아님**: 높은 커버리지(예: 95%)는 코드가 잘 테스트되었다는 뜻이 아니라 단순히 그만큼 실행됐다는 의미입니다. 주장문(assertion)의 의미를 확인하고, 코드 줄수를 채우는 것이 아니라 동작과 속성을 점검하세요.

By incorporating these advanced strategies, you build a multi-layered defense against bugs. This allows you to refactor and add features with a very high degree of confidence, knowing that different parts of your test suite are validating your logic at different levels of abstraction.
이러한 고급 전략을 도입하면 버그에 맞서는 다층 방어막을 구축할 수 있습니다. 테스트 스위트의 각 부분이 다양한 추상화 단계에서 로직을 검증하므로, 리팩터링과 기능 추가를 훨씬 더 자신 있게 진행할 수 있습니다.

## Going Further
## 더 나아가기
-   Spin up a nightly GitHub Actions workflow that runs property tests, contract tests, and mutation tests separately from the fast unit-test workflow.
-   빠른 단위 테스트 파이프라인과 분리된 속성 테스트, 계약 테스트, 돌연변이 테스트를 야간 GitHub Actions 워크플로로 실행하세요.
-   Evaluate Pact or Schemathesis for contract testing across your internal services; document the “provider states” you need in a shared README.
-   내부 서비스 간 계약 테스트를 위해 Pact나 Schemathesis를 평가하고, 필요한 “provider state”를 공유 README에 정리하세요.
-   Teach the testing pyramid to a teammate or friend—explaining the concept out loud will expose any fuzzy parts you still need to solidify.
-   테스트 피라미드를 동료나 친구에게 설명해 보세요. 소리 내어 설명하면서 아직 명확하지 않은 부분을 발견하게 됩니다.
