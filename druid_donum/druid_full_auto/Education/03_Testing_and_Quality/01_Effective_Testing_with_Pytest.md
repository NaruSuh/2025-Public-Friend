# 03.01 - Effective Testing with Pytest

Testing is not about proving your code has no bugs. It's about building confidence that your code does what you expect it to do, and that it continues to do so as you make changes. For a Vibe Coder, testing is a design tool, not an afterthought. `pytest` is the preferred tool due to its simplicity and powerful features.

## Core Concepts

1.  **Test Discovery**: `pytest` automatically finds your tests (files named `test_*.py` or `*_test.py`, functions prefixed with `test_`).
2.  **Fixtures**: A powerful dependency injection system for your tests. They provide a fixed baseline of data or objects for your tests to run against.
3.  **Assertions**: Use plain `assert` statements. `pytest` rewrites them to give you detailed feedback on failures.
4.  **Parametrization**: Run the same test function with different inputs to cover multiple scenarios easily.
5.  **Mocking**: Isolate the code you're testing from its dependencies (like databases or external APIs) using `unittest.mock`.

---

## 1. Writing a Basic Test

Let's say we have a simple function to test in `src/utils.py`:

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

## 2. Parametrization: Keep it DRY (Don't Repeat Yourself)

The tests above are a bit repetitive. We can use `pytest.mark.parametrize` to run the same test logic with different data.

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

## 3. Fixtures: Managing State and Dependencies

Fixtures are functions that provide data, objects, or setup/teardown logic for your tests. They are the cornerstone of a scalable test suite.

Imagine you're testing a function that requires a database connection. You don't want to create a new connection for every single test.

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
-   **Isolation**: Each test gets a clean database state.
-   **Efficiency**: The expensive database engine is created only once.
-   **Readability**: The test function `test_create_user` focuses only on the logic, not the setup/teardown boilerplate.

## 4. Mocking: Isolating Your Code

When testing a function, you only want to test *that function's logic*, not the logic of its dependencies. This is where mocking comes in.

Let's say you're testing your crawler's `parse_list_page` function. This function takes a `BeautifulSoup` object. You don't want to actually make an HTTP request to get the HTML every time you run the test. Instead, you should save a real HTML file once and use it to create a mock `BeautifulSoup` object.

A more advanced use case is mocking an external service, like an email service.

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
-   **Speed**: Network calls are slow. Tests should be fast.
-   **Reliability**: Your tests shouldn't fail because a third-party API is down.
-   **Isolation**: You can test how your code behaves in failure scenarios (e.g., what happens if the email service raises an exception?) without actually crashing the service.

By combining fixtures for setup, parametrization for coverage, and mocking for isolation, you can build a fast, reliable, and comprehensive test suite that gives you the confidence to develop and refactor at speed—the true Vibe Coder way.
