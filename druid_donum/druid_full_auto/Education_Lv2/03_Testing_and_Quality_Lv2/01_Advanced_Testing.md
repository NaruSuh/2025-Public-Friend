# 03 - Testing and Quality - Lv.2: Advanced Testing Strategies

You've mastered unit testing with `pytest`. Level 2 is about expanding your testing pyramid to build confidence in the *interactions* between components and the behavior of the system as a whole.

## Core Concepts

1.  **The Testing Pyramid**: A model for balancing your test suite. Have lots of fast, cheap unit tests at the base, fewer integration tests in the middle, and a very small number of slow, expensive end-to-end tests at the top.
2.  **Integration Testing**: Testing how multiple components of your application work together (e.g., does your API endpoint correctly write to the database?).
3.  **Contract Testing**: A way to ensure that two separate services (e.g., your API and a frontend client, or two microservices) can communicate with each other without having to run a full integration test.
4.  **Property-Based Testing**: Instead of writing examples by hand, you define the *properties* of your functions and let a library generate hundreds of test cases to try and find edge cases you missed.

---

## 1. Integration Testing with Testcontainers

How do you test code that talks to a real database or message queue without mocking everything? `testcontainers` lets you programmatically spin up and tear down real services in Docker containers as part of your `pytest` suite.

**Why Testcontainers?**
-   **High Fidelity**: You're testing against a real PostgreSQL or Redis, not a mock or an in-memory substitute like SQLite.
-   **Isolation**: Each test run (or even each test function) can get a fresh, clean database instance.
-   **Easy Integration**: It works seamlessly with `pytest` fixtures.

**Install**: `pip install testcontainers[postgres]`

### Example: An Integration Test for a FastAPI Endpoint

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

---

## 2. Property-Based Testing with Hypothesis

Instead of thinking of examples, you think of *rules*. Hypothesis then generates hundreds of diverse examples to try and break your rules.

**Install**: `pip install hypothesis`

Let's revisit our `parse_views` function from the first testing guide.

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
-   `0`
-   Large positive and negative numbers
-   Empty strings `""`
-   Strings with Unicode characters, emojis, null bytes `\x00`
-   Strings that look like numbers but aren't, e.g., `"1,2,3"`

If it finds a failing example, it will "shrink" it to the smallest possible failing case, making debugging much easier. Property-based testing is a powerful tool for finding edge cases you would never have thought of.

---

## 3. Other Advanced Testing Concepts

-   **Mutation Testing**: Tools like `mutmut` automatically introduce small bugs (mutations) into your code (e.g., changing a `>` to a `<`) and then run your test suite. If your tests still pass, it means they aren't strong enough to catch that bug. The goal is to "kill" as many mutants as possible.
-   **Visual Regression Testing**: For applications with a UI (like your Streamlit app), tools can take screenshots of components and compare them to a baseline. If a pixel changes, the test fails. This is great for preventing unintentional UI changes.
-   **Test Coverage is Not a Goal**: A high test coverage percentage (e.g., 95%) doesn't guarantee your code is well-tested. It just means that 95% of your lines were executed. It doesn't tell you if your *assertions* are meaningful. Focus on testing behaviors and properties, not just on hitting lines of code.

By incorporating these advanced strategies, you build a multi-layered defense against bugs. This allows you to refactor and add features with a very high degree of confidence, knowing that different parts of your test suite are validating your logic at different levels of abstraction.
