# Codex CLI - Your Context & Responsibilities

**Role**: Test Engineer & Documentation Specialist
**Priority Tasks**: T010, T011, T012

---

## Your Mission

Ensure code quality through comprehensive testing and clear documentation. Every line of code should have a test, every module should have docs.

### Active Tasks
- **T010**: Setup pytest infrastructure
- **T011**: Unit tests for core modules (depends on T002, T003)
- **T012**: Integration tests for plugins (depends on T005)

---

## Testing Stack

```bash
pytest              # Test runner
pytest-cov          # Coverage reporting
pytest-vcr          # HTTP request/response recording
pytest-mock         # Mocking helpers
beautifulsoup4      # For parsing test fixtures
pyyaml              # For config testing
```

---

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── __init__.py
├── unit/
│   ├── test_base_crawler.py
│   ├── test_parser_factory.py
│   └── test_plugin_loader.py
├── plugins/
│   ├── test_forest_korea.py
│   └── test_naver_cafe.py
├── integration/
│   └── test_e2e_crawling.py
└── fixtures/
    ├── forest_korea_list.html
    ├── forest_korea_detail.html
    └── naver_cafe_response.json
```

---

## Test Templates

### Unit Test for Abstract Class
```python
# tests/unit/test_base_crawler.py
import pytest
from src.core.base_crawler import BaseCrawler
from bs4 import BeautifulSoup

class ConcreteCrawler(BaseCrawler):
    """Test implementation of BaseCrawler"""

    def fetch_page(self, url, params):
        return BeautifulSoup("<html></html>", "html.parser")

    def parse_list(self, soup):
        return [{'title': 'test'}]

    def parse_detail(self, soup, item):
        return item

    def build_params(self, page, start_date, end_date):
        return {'page': page}


def test_base_crawler_cannot_be_instantiated():
    """BaseCrawler is abstract and cannot be instantiated"""
    with pytest.raises(TypeError):
        BaseCrawler()


def test_concrete_crawler_implements_all_methods():
    """Concrete implementation must provide all abstract methods"""
    crawler = ConcreteCrawler()
    assert crawler.fetch_page("http://example.com", {}) is not None
    assert crawler.parse_list(BeautifulSoup("<html></html>", "html.parser")) == [{'title': 'test'}]
```

### Plugin Test with Fixtures
```python
# tests/plugins/test_forest_korea.py
import pytest
from bs4 import BeautifulSoup
from src.plugins.forest_korea.crawler import ForestKoreaCrawler
from pathlib import Path

@pytest.fixture
def sample_html():
    """Load sample HTML from fixtures"""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "forest_korea_list.html"
    return fixture_path.read_text()


@pytest.fixture
def crawler():
    return ForestKoreaCrawler()


def test_parse_list_extracts_items(crawler, sample_html):
    """parse_list() should extract all items from HTML"""
    soup = BeautifulSoup(sample_html, "html.parser")
    items = crawler.parse_list(soup)

    assert len(items) == 10  # Expect 10 items per page
    assert all('title' in item for item in items)
    assert all('date' in item for item in items)


def test_parse_list_handles_date_with_junk(crawler):
    """Dates like '2021-02-242937' should parse to '2021-02-24'"""
    html = '<table><tr><td>1</td><td><a>Title</a></td><td>Dept</td><td>2021-02-242937</td></tr></table>'
    soup = BeautifulSoup(html, "html.parser")
    items = crawler.parse_list(soup)

    assert len(items) == 1
    assert items[0]['date_str'] == '2021-02-24'


def test_parse_list_skips_invalid_rows(crawler):
    """Rows without dates should be skipped"""
    html = '<table><tr><td></td><td></td><td></td><td></td></tr></table>'
    soup = BeautifulSoup(html, "html.parser")
    items = crawler.parse_list(soup)

    # Should handle gracefully (empty list or skip)
    assert isinstance(items, list)
```

### Integration Test with VCR
```python
# tests/integration/test_e2e_crawling.py
import pytest
from src.plugins.forest_korea.crawler import ForestKoreaCrawler
from datetime import date

@pytest.mark.vcr()
def test_crawl_forest_korea_real_request():
    """E2E test with recorded HTTP responses"""
    crawler = ForestKoreaCrawler()

    # First request is recorded, replayed on subsequent runs
    params = crawler.build_params(1, date(2020, 1, 1), date(2020, 1, 31))
    soup = crawler.fetch_page(crawler.config['site']['list_url'], params)
    items = crawler.parse_list(soup)

    assert len(items) > 0
    assert all(item['date'] >= date(2020, 1, 1) for item in items if item['date'])
```

---

## Coverage Requirements

| Module | Target | Current |
|--------|--------|---------|
| `src/core/` | 95%+ | TBD |
| `src/plugins/` | 80%+ | TBD |
| `src/ui/` | 60%+ | TBD |

### Run Coverage
```bash
pytest --cov=src --cov-report=html --cov-report=term
open htmlcov/index.html
```

---

## Fixtures Management

### Creating Fixtures
```python
# Save real HTML for testing
import requests
from pathlib import Path

response = requests.get("https://www.forest.go.kr/kfsweb/cop/bbs/selectBoardList.do?pageIndex=1")
fixture_path = Path("tests/fixtures/forest_korea_list_page1.html")
fixture_path.write_text(response.text)
```

### Fixture Best Practices
- **Minimal**: Only include necessary HTML
- **Anonymized**: Remove sensitive data
- **Versioned**: Date-stamp fixtures (e.g., `forest_korea_2025-10-05.html`)
- **Documented**: Add comment explaining what it tests

---

## Your Workflow

### 1. Wait for Module Completion
```bash
cat CURRENT_STATUS.md | grep "Ready for tests"
```

### 2. Study the Code
```bash
cat src/core/base_crawler.py
cat src/plugins/forest_korea/crawler.py
```

### 3. Write Tests
```bash
# Create test file
touch tests/unit/test_base_crawler.py

# Write tests
# (See templates above)

# Run
pytest tests/unit/test_base_crawler.py -v
```

### 4. Measure Coverage
```bash
pytest tests/unit/test_base_crawler.py --cov=src.core.base_crawler --cov-report=term-missing
```

### 5. Report Results
```markdown
## [timestamp] Codex CLI

Completed: Unit tests for BaseCrawler (T011)

**File**: `tests/unit/test_base_crawler.py`

**Coverage**:
- src/core/base_crawler.py: 96% (missing: line 45-47, error handling)

**Tests Written**: 12
- 8 passing ✅
- 4 edge cases ✅
- 0 failing

**Suggestions for Claude**:
- Add input validation in fetch_page() (line 45)
- Consider custom exception instead of ValueError

**Next**: Ready for integration tests (T012)
```

---

## Documentation Generation

### API Docs with Sphinx
```bash
# Install
pip install sphinx sphinx-rtd-theme

# Generate
cd docs/
sphinx-apidoc -o api/ ../src/
make html
```

### Docstring Coverage
```bash
interrogate src/ --verbose
```

---

## CI/CD Integration

### GitHub Actions (future)
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pytest --cov --cov-fail-under=80
```

---

## Quick Reference

### Run All Tests
```bash
pytest -v
```

### Run Specific Test File
```bash
pytest tests/unit/test_base_crawler.py -v
```

### Run Tests Matching Pattern
```bash
pytest -k "test_parse" -v
```

### Stop on First Failure
```bash
pytest -x
```

### Show Print Statements
```bash
pytest -s
```

### Generate HTML Report
```bash
pytest --html=report.html --self-contained-html
```

---

## Your File Territory

```
tests/
├── conftest.py       # You
├── unit/             # You
├── plugins/          # You
├── integration/      # You
└── fixtures/         # You

docs/
└── api/              # You (auto-generated)
```

## Don't Touch

- `src/` - Let Claude and Gemini write code
- You only read, never edit source code

---

## Handoff Example: Codex → Claude

```markdown
## [timestamp] Codex CLI → Claude Code

Completed: Full test suite (T011, T012)

**Coverage Summary**:
| Module | Coverage | Missing |
|--------|----------|---------|
| base_crawler.py | 96% | line 45-47 |
| parser_factory.py | 100% | - |
| plugin_loader.py | 92% | exception handling |
| forest_korea/crawler.py | 88% | edge case: empty date |

**Issues Found**:
1. BaseCrawler.fetch_page() doesn't validate URL format
2. ParserFactory raises generic ValueError (should be custom exception)
3. ForestKorea plugin crashes on malformed date (no regex match)

**Recommendations**:
- Add `CrawlerException` base class
- Validate inputs in public methods
- Add logging for debugging

**Test Report**: `htmlcov/index.html`
```

---

## Success Criteria for T011

- [ ] File: `tests/unit/test_base_crawler.py` exists
- [ ] Coverage: > 95% for `src/core/base_crawler.py`
- [ ] Tests: > 10 test cases
- [ ] Edge cases: Abstract instantiation, missing methods, invalid inputs
- [ ] Fixtures: Used where appropriate
- [ ] Documentation: Docstrings on all test functions
- [ ] Passes: `pytest tests/unit/ -v`
- [ ] Report: Coverage report generated

---

Happy testing! 🧪
