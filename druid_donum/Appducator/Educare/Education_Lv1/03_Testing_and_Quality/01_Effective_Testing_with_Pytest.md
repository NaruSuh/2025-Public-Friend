# 03.01 - Effective Testing with Pytest
# 03.01 - Pytest를 사용한 효과적인 테스트

Testing is not about proving your code has no bugs. It's about building confidence that your code does what you expect it to do, and that it continues to do so as you make changes. For a Vibe Coder, testing is a design tool, not an afterthought. `pytest` is the preferred tool due to its simplicity and powerful features.
테스트는 코드에 버그가 없음을 증명하는 것이 아닙니다. 코드가 예상대로 작동하고 변경 사항이 발생해도 계속 그렇게 작동할 것이라는 확신을 구축하는 것입니다. Vibe 코더에게 테스트는 나중에 생각하는 것이 아니라 설계 도구입니다. `pytest`는 단순성과 강력한 기능으로 인해 선호되는 도구입니다.

## Core Concepts
## 핵심 개념

1.  **Test Discovery**: `pytest` automatically finds your tests (files named `test_*.py` or `*_test.py`, functions prefixed with `test_`).
    **테스트 발견**: `pytest`는 테스트를 자동으로 찾습니다 (`test_*.py` 또는 `*_test.py`라는 이름의 파일, `test_` 접두사가 붙은 함수).
2.  **Fixtures**: A powerful dependency injection system for your tests. They provide a fixed baseline of data or objects for your tests to run against.
    **픽스처**: 테스트를 위한 강력한 의존성 주입 시스템입니다. 테스트를 실행할 데이터 또는 객체의 고정된 기준선을 제공합니다.
3.  **Assertions**: Use plain `assert` statements. `pytest` rewrites them to give you detailed feedback on failures.
    **단언**: 일반 `assert` 문을 사용합니다. `pytest`는 실패에 대한 자세한 피드백을 제공하기 위해 이를 다시 작성합니다.
4.  **Parametrization**: Run the same test function with different inputs to cover multiple scenarios easily.
    **매개변수화**: 여러 시나리오를 쉽게 다루기 위해 동일한 테스트 함수를 다른 입력으로 실행합니다.
5.  **Mocking**: Isolate the code you're testing from its dependencies (like databases or external APIs) using `unittest.mock`.
    **모의(Mocking)**: `unittest.mock`을 사용하여 테스트 중인 코드를 의존성(데이터베이스 또는 외부 API와 같은)에서 격리합니다.

---

## 1. Writing a Basic Test
## 1. 기본 테스트 작성

Let's say we have a simple function to test in `src/utils.py`:
`src/utils.py`에 테스트할 간단한 함수가 있다고 가정해 보겠습니다.

```python
# src/utils.py
def parse_views(text: str) -> int:
    """Extracts the view count from a string, handling commas and errors."""
    if not isinstance(text, str):
        return 0
    try:
        # Remove commas and convert to int
        return int(text.replace(",", "").strip())
    except (ValueError, TypeError):
        return 0
```

Now, create a test file `tests/test_utils.py`:
이제 `tests/test_utils.py` 테스트 파일을 만듭니다.

```python
# tests/test_utils.py
from src.utils import parse_views

def test_parse_views_simple_number():
    """Tests a simple numeric string."""
    assert parse_views("123") == 123

def test_parse_views_with_commas():
    """Tests a string with commas."""
    assert parse_views("1,234") == 1234

def test_parse_views_with_whitespace():
    """Tests a string with leading/trailing whitespace."""
    assert parse_views("  567  ") == 567

def test_parse_views_invalid_string():
    """Tests a non-numeric string."""
    assert parse_views("abc") == 0

def test_parse_views_empty_string():
    """Tests an empty string."""
    assert parse_views("") == 0

def test_parse_views_with_none_input():
    """Tests with None as input."""
    assert parse_views(None) == 0
```
To run these tests, simply execute `pytest` in your terminal.
이 테스트를 실행하려면 터미널에서 `pytest`를 실행하기만 하면 됩니다.

## 2. Parametrization: Keep it DRY (Don't Repeat Yourself)
## 2. 매개변수화: DRY 원칙을 지키세요 (반복하지 마세요)

The tests above are a bit repetitive. We can use `pytest.mark.parametrize` to run the same test logic with different data.
위의 테스트는 약간 반복적입니다. `pytest.mark.parametrize`를 사용하여 동일한 테스트 로직을 다른 데이터로 실행할 수 있습니다.

```python
# tests/test_utils.py
import pytest
from src.utils import parse_views

@pytest.mark.parametrize(
    "input_str, expected_output",
    [
        ("123", 123),
        ("1,234", 1234),
        ("  567  ", 567),
        ("abc", 0),
        ("", 0),
        (None, 0),
        ("1,000,000", 1000000),
        ("  -42 ", -42), # Edge case: negative numbers
    ],
)
def test_parse_views_parametrized(input_str, expected_output):
    """A single, powerful test for the parse_views function."""
    assert parse_views(input_str) == expected_output
```
This is much cleaner and makes it trivial to add new test cases.
이것이 훨씬 깔끔하고 새로운 테스트 케이스를 추가하기가 매우 쉽습니다.

## 3. Fixtures: Managing State and Dependencies
## 3. 픽스처: 상태 및 의존성 관리

Fixtures are functions that provide data, objects, or setup/teardown logic for your tests. They are the cornerstone of a scalable test suite.
픽스처는 테스트를 위한 데이터, 객체 또는 설정/해체 로직을 제공하는 함수입니다. 확장 가능한 테스트 스위트의 초석입니다.

Imagine you're testing a function that requires a database connection. You don't want to create a new connection for every single test.
데이터베이스 연결이 필요한 함수를 테스트한다고 상상해보십시오. 모든 단일 테스트에 대해 새 연결을 만들고 싶지 않을 것입니다.

```python
# tests/conftest.py
# This file is special: fixtures defined here are available to all tests.
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

@pytest.fixture(scope="session")
def db_engine():
    """
    A fixture that creates a database engine once per test session.
    'scope="session"' is the key here.
    """
    print("\n--> Creating DB engine")
    # Use an in-memory SQLite database for tests
    engine = create_engine("sqlite:///:memory:")
    # You would create your tables here
    # models.Base.metadata.create_all(bind=engine)
    yield engine
    print("\n--> Tearing down DB engine")
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    A fixture that provides a clean database session for each test function.
    'scope="function"' is the default and runs for every test.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

# --- Now, in your test file ---
# tests/test_crud.py

# The 'db_session' argument tells pytest to inject the fixture.
def test_create_user(db_session):
    from src import crud, schemas
    user_in = schemas.UserCreate(email="test@example.com", password="password")
    created_user = crud.create_user(db=db_session, user=user_in)
    
    assert created_user.id is not None
    assert created_user.email == "test@example.com"

    # The transaction is rolled back automatically by the fixture,
    # so this user won't exist in the next test.
```
**Why this is powerful:**
**이것이 강력한 이유:**
-   **Isolation**: Each test gets a clean database state.
    **격리**: 각 테스트는 깨끗한 데이터베이스 상태를 얻습니다.
-   **Efficiency**: The expensive database engine is created only once.
    **효율성**: 비용이 많이 드는 데이터베이스 엔진은 한 번만 생성됩니다.
-   **Readability**: The test function `test_create_user` focuses only on the logic, not the setup/teardown boilerplate.
    **가독성**: `test_create_user` 테스트 함수는 설정/해체 상용구 코드가 아닌 로직에만 집중합니다.

## 4. Mocking: Isolating Your Code
## 4. 모의(Mocking): 코드 격리

When testing a function, you only want to test *that function's logic*, not the logic of its dependencies. This is where mocking comes in.
함수를 테스트할 때 의존성의 로직이 아닌 *해당 함수의 로직*만 테스트하고 싶을 것입니다. 여기서 모의가 사용됩니다.

Let's say you're testing your crawler's `parse_list_page` function. This function takes a `BeautifulSoup` object. You don't want to actually make an HTTP request to get the HTML every time you run the test. Instead, you should save a real HTML file once and use it to create a mock `BeautifulSoup` object.
크롤러의 `parse_list_page` 함수를 테스트한다고 가정해 보겠습니다. 이 함수는 `BeautifulSoup` 객체를 받습니다. 테스트를 실행할 때마다 HTML을 얻기 위해 실제로 HTTP 요청을 하고 싶지는 않을 것입니다. 대신 실제 HTML 파일을 한 번 저장하고 이를 사용하여 모의 `BeautifulSoup` 객체를 만들어야 합니다.

A more advanced use case is mocking an external service, like an email service.
더 고급 사용 사례는 이메일 서비스와 같은 외부 서비스를 모의하는 것입니다.

```python
# src/logic.py
from .services import email_service

def register_user_and_send_email(email: str, name: str):
    # ... user registration logic ...
    print("User registered.")
    
    # This is an external call we want to mock
    email_service.send_welcome_email(email_to=email, name=name)
    
    return True

# tests/test_logic.py
from unittest.mock import patch
from src.logic import register_user_and_send_email

# The @patch decorator intercepts calls to the specified object.
@patch("src.services.email_service.send_welcome_email")
def test_register_user_and_send_email(mock_send_email):
    """
    Tests that the registration logic calls the email service correctly.
    """
    # The 'mock_send_email' argument is the mocked function provided by @patch.
    result = register_user_and_send_email("test@example.com", "tester")

    assert result is True
    
    # Assert that our mock was called exactly once.
    mock_send_email.assert_called_once()
    
    # Assert it was called with the correct arguments.
    mock_send_email.assert_called_once_with(
        email_to="test@example.com", 
        name="tester"
    )
```
**Why mock?**
**왜 모의를 사용해야 할까요?**
-   **Speed**: Network calls are slow. Tests should be fast.
    **속도**: 네트워크 호출은 느립니다. 테스트는 빨라야 합니다.
-   **Reliability**: Your tests shouldn't fail because a third-party API is down.
    **신뢰성**: 타사 API가 다운되었다고 해서 테스트가 실패해서는 안 됩니다.
-   **Isolation**: You can test how your code behaves in failure scenarios (e.g., what happens if the email service raises an exception?) without actually crashing the service.
    **격리**: 실제로 서비스를 중단시키지 않고도 실패 시나리오에서 코드가 어떻게 작동하는지 테스트할 수 있습니다(예: 이메일 서비스에서 예외가 발생하면 어떻게 될까요?).

By combining fixtures for setup, parametrization for coverage, and mocking for isolation, you can build a fast, reliable, and comprehensive test suite that gives you the confidence to develop and refactor at speed—the true Vibe Coder way.
설정을 위한 픽스처, 커버리지를 위한 매개변수화, 격리를 위한 모의를 결합하여 빠르고 안정적이며 포괄적인 테스트 스위트를 구축하여 Vibe Coder의 진정한 방식인 빠른 속도로 개발하고 리팩토링할 수 있다는 자신감을 얻을 수 있습니다.