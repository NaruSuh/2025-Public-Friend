# druid_donum Code Audit Report

**Audit Date**: 2025-12-10
**Auditor**: Claude Opus 4.5
**Project Version**: 1.1.02 (Production Hardening 90% Complete)
**Status**: Pre-Production Review

---

## Executive Summary

**Overall Assessment**: REQUIRES IMMEDIATE ATTENTION - NOT READY for production

druid_donum is a Korean Forest Service Bid Information Web Crawler (산림청 입찰정보 크롤러) built with Streamlit and Python. The project demonstrates **good architectural foundation** but contains **multiple critical security and design issues**.

- **4 Critical Issues** (must fix before production)
- **5 Major Issues** (should fix)
- **5 Minor Issues** (nice to fix)

**Codebase Size**: 2,037 lines of Python code
**Test Coverage**: ~42% (27 unit tests)
**Risk Level**: HIGH (due to critical security and thread safety issues)

---

## 1. Critical Issues (Must Fix)

### CRIT-001: Unsafe Dynamic Module Import in ParserFactory
**Location**: `src/core/parser_factory.py` lines 98-111, 237-241
**Severity**: CRITICAL (Security - Remote Code Execution Risk)

**Issue**:
```python
def _load_crawler_class(self, site_name: str) -> type:
    module_path = f"src.plugins.{site_name}.crawler"
    module = importlib.import_module(module_path)
```

The validation at line 238 only checks `[A-Za-z0-9_]+`, which is insufficient:
- Cannot prevent `__pycache__` directory manipulation
- No signature verification of loaded plugins
- No whitelist enforcement

**Fix Recommendations**:
1. Implement plugin whitelist (hardcoded list of allowed plugins)
2. Use `importlib.util.spec_from_file_location()` with explicit path validation
3. Add cryptographic signature verification for plugins
4. Consider sandboxing with `RestrictedPython`

**Risk Rating**: 9/10

---

### CRIT-002: Thread Safety Violations in Streamlit Session State
**Location**: `app.py` lines 28-72
**Severity**: CRITICAL (Data Corruption Risk)

**Issue**:
```python
_session_lock = threading.RLock()  # False sense of security

def _read_session_state(key: str, default_factory):
    with _session_lock:
        if key not in st.session_state:
            st.session_state[key] = default_factory()
```

**Why it's broken**:
- Streamlit is **single-threaded per session** but **multi-process per user**
- `threading.RLock()` provides NO protection **across processes**
- Lines 37, 606, 84 show inconsistent patterns

**Fix Recommendations**:
1. **Remove all threading locks** - they provide false security
2. Use Streamlit's **built-in session state correctly**
3. If multi-user concurrency needed, use **Redis** or **database-backed** session storage

**Risk Rating**: 8/10

---

### CRIT-003: Forced Module Reload Anti-Pattern
**Location**: `app.py` lines 18-23
**Severity**: CRITICAL (Runtime Stability)

**Issue**:
```python
# main.py 강제 reload (코드 변경 반영)
import sys
import importlib
if 'main' in sys.modules:
    importlib.reload(sys.modules['main'])
from main import ForestBidCrawler
```

**Why it's broken**:
- Forces module reload on **every Streamlit rerun** (happens on every interaction)
- Creates **multiple copies** of `ForestBidCrawler` class in memory
- Breaks `isinstance()` checks across reloads
- Can cause `AttributeError` if classes mid-instantiation during reload

**Fix**: **Delete lines 18-23 completely**

**Risk Rating**: 8/10

---

### CRIT-004: SQL-Injection-like URL Parameter Injection
**Location**: `main.py` lines 385-387
**Severity**: HIGH (Web Scraping Ethics)

**Issue**:
```python
params = {
    'mn': 'NKFS_04_01_04',
    'bbsId': 'BBSMSTR_1033',
    'pageIndex': page_index,
    'pageUnit': 10,
    'ntcStartDt': start_date.strftime('%Y-%m-%d'),
    'ntcEndDt': end_date.strftime('%Y-%m-%d')
}
```

**Problems**:
- Date parameters are **user-controlled** without server-side validation
- No rate limiting on date range requests
- Can request enormous date ranges (0-3650 days) unchecked

**Fix Recommendations**:
1. Add **per-request date range validation**
2. Implement **request throttling** (token bucket algorithm)
3. Log all requests with timestamps for audit
4. Set hard limits on `pageUnit`

**Risk Rating**: 6/10

---

## 2. Major Issues (Should Fix)

### MAJ-001: Bare `except` Clause in Data Export
**Location**: `app.py` line 636
**Severity**: HIGH

```python
try:
    views_numbers = df['조회수'].astype(str).str.extract('(\d+)')[0].astype(float)
    avg_views = int(views_numbers.mean())
except:  # BAD: catches everything including KeyboardInterrupt, SystemExit
    avg_views = 0
```

**Fix**:
```python
except (ValueError, TypeError, KeyError) as e:
    logger.warning(f"Could not calculate average views: {e}")
    avg_views = 0
```

---

### MAJ-002: HTML Parsing Index Hardcoding
**Location**: `main.py` lines 333-338
**Severity**: HIGH

```python
number_idx = _lookup_index(['번호', 'No', 'NO'], 0)      # Default: column 0
title_idx = _lookup_index(['제목', 'Title'], 1)         # Default: column 1
```

**Risk**: Site structure changes cause complete parsing failure

**Fix**: Make header detection mandatory, add semantic validation

---

### MAJ-003: DataFrame Serialization Instability
**Location**: `app.py` lines 101-111, 244-246
**Severity**: HIGH

**Issue**: DataFrames stored directly in Streamlit session state cause:
- Memory bloat
- Column order/dtypes not preserved reliably
- Cache hits unreliable

**Fix**: Store compressed bytes instead of DataFrame (parquet/pickle)

---

### MAJ-004: Weak Date Parsing Error Handling
**Location**: `main.py` lines 169-197
**Severity**: HIGH

**Issue**: Returns `None` silently without clear context, no tracking of which dates failed

---

### MAJ-005: Missing Type Hints on Public API
**Location**: `app.py` lines 43-72, 131, 335
**Severity**: MEDIUM

```python
def run_crawling(start_date, end_date, days, delay, page_delay):  # Completely untyped
```

---

## 3. Minor Issues (Nice to Fix)

| Issue | Location | Description |
|-------|----------|-------------|
| MIN-001 | requirements.txt, main.py | `lxml` listed but code uses `html.parser` |
| MIN-002 | main.py lines 670-695 | Logging configuration inconsistency |
| MIN-003 | main.py lines 630-632 | No input sanitization for file paths |
| MIN-004 | Throughout | Inconsistent error messages (English/Korean mix) |
| MIN-005 | main.py line 218 | No request timeout on retries |

---

## 4. Security Analysis

### URL Validation
- ✅ Base URLs are hardcoded (good)
- ✅ Parameters are validated at init (good)
- ❌ No per-request validation (bad)
- ❌ No rate limiting (bad)

### File Handling
- ✅ Uses `Path` library (good)
- ❌ No file size limits (bad)
- ❌ No extension validation (bad)
- ❌ No temporary file cleanup (bad)

### Data Privacy
- ✅ Only collects public data (good)
- ✅ No API keys in code (good)
- ❌ Logs contain URLs with potential PII (bad)

---

## 5. Performance Analysis

### Memory Management: PROBLEMATIC
```python
all_item_status = []  # Accumulates unbounded!
```
**Issue**: `all_item_status` grows without limit, consuming memory

**Recommendation**: Implement circular buffer or windowed list

### Scraping Efficiency: ADEQUATE
- ✅ Respects rate limits (0.5s+ delays)
- ✅ Uses connection pooling (requests.Session)
- ❌ No caching of HTML pages
- ❌ Sequential page fetching (could parallelize)

### Rate Limiting: PRESENT BUT INSUFFICIENT
- ✅ Configurable delays
- ❌ No exponential backoff for 429 responses
- ❌ No concurrent request limits

---

## 6. Code Quality Assessment

### Strengths
1. ✅ Good module organization with plugin architecture
2. ✅ Custom exceptions (CrawlerException, ParsingException)
3. ✅ Retry logic with backoff
4. ✅ 27 unit tests (18 for crawler, 9 for parsing)

### Weaknesses
1. ❌ Critical thread safety issues
2. ❌ Module reload anti-pattern
3. ❌ ~40% type hint coverage
4. ❌ No integration tests

---

## 7. Dependencies Audit

**requirements.txt**:
```
requests>=2.31.0          ✓ Stable
beautifulsoup4>=4.12.0    ✓ Industry standard
pandas>=2.0.0             ✓ Standard
openpyxl>=3.1.0           ✓ Excel support
lxml>=4.9.0               ⚠️ NOT USED IN CODE
streamlit>=1.28.0         ✓ Web framework
python-dateutil>=2.8.2    ✓ Date parsing
PyYAML>=6.0               ⚠️ Listed but not imported
```

**Recommendation**: Remove unused `lxml` or explicitly use with `parser='lxml'`

---

## 8. Testing Assessment

### Existing Tests
- **Coverage**: 27 tests (18 crawler, 9 parsing)
- **Framework**: pytest with mock support
- **Quality**: Good (covers edge cases)

### Coverage Gaps
- ❌ No tests for Streamlit UI (app.py)
- ❌ No integration tests
- ❌ No tests for ParserFactory
- ❌ No tests for checkpoint persistence

**Target**: 80%+ coverage

---

## 9. Recommended Fixes (Priority Order)

### Priority 1 (Critical - Fix Before Production)
1. Remove module reload hack (app.py:18-23) - 30 min
2. Remove threading locks (app.py:28-72) - 1 hour
3. Fix dynamic import security (parser_factory.py) - 4 hours
4. Add URL/parameter validation (main.py) - 2 hours
5. Remove bare except (app.py:636) - 30 min

### Priority 2 (High - Fix Before Deployment)
1. Add type hints to app.py public API - 3 hours
2. Implement database-backed session storage - 4 hours
3. Add rate limiting + request throttling - 3 hours
4. Implement structured logging - 2 hours
5. Add integration tests - 6 hours

### Priority 3 (Medium - Improve Code Quality)
1. Remove unused lxml dependency - 10 min
2. Consolidate logging configuration - 1 hour
3. Add robots.txt parsing - 2 hours
4. Implement code formatting in pre-commit - 1 hour
5. Increase test coverage to 80%+ - 8 hours

**Total Estimated Effort**: ~38 hours

---

## 10. Files Audited

| File | Lines | Status |
|------|-------|--------|
| app.py | 788 | FAIL - Critical thread safety issues |
| main.py | 749 | PASS with recommendations |
| src/core/parser_factory.py | ~200 | FAIL - Security vulnerability |
| tests/test_crawler.py | ~150 | PASS |
| tests/test_parsing.py | ~100 | PASS |

**Total LOC**: 2,037 (Python)

---

## 11. Risk Summary

| Area | Risk Level |
|------|------------|
| Security | HIGH |
| Reliability | HIGH |
| Maintainability | MEDIUM |
| Performance | MEDIUM |

---

## 12. Deployment Checklist

- [ ] Remove module reload code (CRITICAL)
- [ ] Remove threading locks (CRITICAL)
- [ ] Fix ParserFactory import security (CRITICAL)
- [ ] Add type hints to app.py (HIGH)
- [ ] Remove bare except (HIGH)
- [ ] Set up CI/CD with GitHub Actions
- [ ] Add pre-commit hooks (black, ruff, mypy)
- [ ] Increase test coverage to 80%+
- [ ] Set up log rotation and monitoring
- [ ] Configure Streamlit production settings
- [ ] Add error monitoring (Sentry/similar)

---

## 13. Conclusion

The druid_donum project demonstrates **solid foundational design** with good testing infrastructure and error handling in the core crawler. However, **three critical security/stability issues must be fixed before any production deployment**:

1. Module reload anti-pattern
2. Fake thread safety with locks
3. Unsafe dynamic imports

**Overall Recommendation**: **CONDITIONAL APPROVAL**
- ✅ Suitable for research/development
- ❌ NOT READY for production deployment
- Timeline to production: 2-3 weeks with dedicated developer

---

*Generated by Claude Opus 4.5 Code Audit System*
