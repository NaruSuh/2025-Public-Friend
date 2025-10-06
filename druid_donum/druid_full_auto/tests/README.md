# Tests

## Running Tests

### Install test dependencies
```bash
pip install -r requirements-dev.txt
```

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=. --cov-report=html
```

### Run specific test file
```bash
pytest tests/unit/test_crawler.py -v
```

### Run specific test
```bash
pytest tests/unit/test_crawler.py::TestCrawlerValidation::test_valid_params -v
```

## Test Structure

```
tests/
├── unit/               # Unit tests
│   ├── test_crawler.py    # Crawler validation & checkpoint tests
│   └── test_parsing.py    # HTML parsing tests
└── integration/        # Integration tests (TODO)
```

## Writing Tests

All test files should:
- Start with `test_`
- Use descriptive class names (e.g., `TestCrawlerValidation`)
- Have clear docstrings
- Test both success and failure cases
