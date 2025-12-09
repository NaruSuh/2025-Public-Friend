# Comprehensive Code Audit Report - Druid Donum Project

**Project**: Korean Forest Service Bid Information Web Crawler
**Audit Date**: 2025-12-10
**Version Audited**: 1.1.02
**Auditor**: Automated Security & Code Quality Review
**Scope**: `/home/naru/skyimpact/2025-Public-Friend/druid_donum/druid_full_auto/`

---

## Executive Summary

This audit examines a Streamlit-based web crawler designed to collect bid information from the Korean Forest Service website. The application consists of two main components:
- **app.py**: Streamlit web interface (789 lines)
- **main.py**: Core crawler engine (750 lines)
- **src/core/**: Abstraction layer for future plugin architecture

**Overall Assessment**: The codebase is functional but has several security, performance, and code quality issues that should be addressed before production deployment.

**Test Coverage**: ~42% (27 unit tests)
**Primary Language**: Python 3.10+
**Framework**: Streamlit 1.28.0+

---

## Table of Contents

1. [Critical Issues (Must Fix)](#1-critical-issues-must-fix)
2. [Major Issues (Should Fix)](#2-major-issues-should-fix)
3. [Minor Issues (Nice to Fix)](#3-minor-issues-nice-to-fix)
4. [Security Analysis](#4-security-analysis)
5. [Performance Analysis](#5-performance-analysis)
6. [Code Quality Assessment](#6-code-quality-assessment)
7. [Best Practices Review](#7-best-practices-review)
8. [Dependency Analysis](#8-dependency-analysis)
9. [Recommendations](#9-recommendations)

---

## 1. Critical Issues (Must Fix)

### 1.1 Thread Safety Violations in Streamlit Session State

**Location**: `app.py` lines 28-72
**Severity**: CRITICAL
**Impact**: Race conditions, data corruption, inconsistent UI state

**Issue**:
```python
_session_lock = threading.RLock()  # Line 28

def _read_session_state(key: str, default_factory):
    with _session_lock:
        if key not in st.session_state:
            st.session_state[key] = default_factory()
        value = st.session_state[key]
        if isinstance(value, list):
            return list(value)  # Returns a copy
        # ... but then code modifies the original anyway
```

**Problem**:
- Streamlit is single-threaded per session but multi-process per user
- Using `threading.RLock()` provides NO protection across processes
- The `_session_lock` gives false sense of security
- Copying lists/dicts in `_read_session_state()` but then directly mutating `st.session_state` elsewhere

**Evidence**:
- Line 37: `st.session_state.setdefault("crawl_logs", [])`
- Line 606: `_set_session_values(crawl_data=df, crawl_completed=True)` - Direct mutation
- Line 84: `_update_session_state()` attempts atomic updates but lock is ineffective

**Recommendation**:
1. Remove threading locks (they don't work across Streamlit processes)
2. Use Streamlit's built-in session state management correctly
3. Always access `st.session_state` directly, don't try to implement your own locking
4. If multi-user concurrency is needed, use Redis or database-backed session storage

**Risk**: Medium-High (May cause data loss during concurrent crawls)

---

### 1.2 Module Reload Anti-Pattern

**Location**: `app.py` lines 18-23
**Severity**: CRITICAL
**Impact**: Unpredictable behavior, memory leaks, broken imports

**Issue**:
```python
# main.py 강제 reload (코드 변경 반영)
import sys
import importlib
if 'main' in sys.modules:
    importlib.reload(sys.modules['main'])
from main import ForestBidCrawler
```

**Problem**:
- Forces module reload on every Streamlit rerun (happens on every user interaction)
- Creates multiple copies of `ForestBidCrawler` class in memory
- Breaks `isinstance()` checks across reloads
- Can cause `AttributeError` if classes are mid-instantiation during reload
- Defeats import caching, slowing app startup

**Recommendation**:
1. **Remove this code entirely**
2. Use Streamlit's built-in hot-reload for development
3. For production, deploy with `streamlit run app.py` without file watcher
4. Update `.streamlit/config.toml` already has `runOnSave = false` - this reload is redundant

**Risk**: High (Can crash app during production use)

---

### 1.3 Unsafe Dynamic Module Import

**Location**: `src/core/parser_factory.py` lines 98-111
**Severity**: CRITICAL (Security)
**Impact**: Arbitrary code execution, module injection attacks

**Issue**:
```python
def _load_crawler_class(self, site_name: str) -> type:
    module_path = f"src.plugins.{site_name}.crawler"
    module = importlib.import_module(module_path)
```

**Problem**:
- While `_validate_site_name()` checks for `[A-Za-z0-9_]+`, this is insufficient
- Attacker could create directory `src/plugins/__pycache__/` with malicious code
- Python's import system follows `__pycache__` automatically
- No verification that loaded class is safe

**Current Validation** (line 238):
```python
if not re.fullmatch(r"[A-Za-z0-9_]+", site_name):
    raise CrawlerNotFoundError(...)
```

**Recommendation**:
1. Add whitelist of allowed plugin names
2. Verify plugin directory is owned by application
3. Add signature verification for plugins
4. Use `importlib.util.spec_from_file_location()` with explicit path checking
5. Sandbox plugin execution with `RestrictedPython` or similar

**Risk**: High (If attacker gains filesystem write access)

---

### 1.4 Unvalidated User Input in URL Construction

**Location**: `app.py` lines 376-383, `main.py` lines 548-553
**Severity**: CRITICAL (Security)
**Impact**: Server-Side Request Forgery (SSRF), information disclosure

**Issue**:
```python
params = {
    'mn': 'NKFS_04_01_04',
    'bbsId': 'BBSMSTR_1033',
    'pageIndex': page_index,  # User controlled via UI
    'pageUnit': 10,
    'ntcStartDt': start_date.strftime('%Y-%m-%d'),  # User controlled
    'ntcEndDt': end_date.strftime('%Y-%m-%d')      # User controlled
}
soup = crawler.fetch_page(crawler.LIST_URL, params)
```

**Problem**:
- `page_index` increments without bounds checking until line 577 (500 pages max)
- Date parameters from user input passed directly to URL without sanitization
- Could send malicious parameters to backend server
- No validation that dates are in reasonable range before network call

**Recommendation**:
1. Validate `page_index` range before constructing params (1-500)
2. Validate date format matches `YYYY-MM-DD` exactly
3. Add max date range check (already in constructor, but enforce in URL building)
4. Consider URL signature/checksum if API supports it

**Risk**: Medium (Server may have its own validation)

---

### 1.5 Potential SQL Injection via Unescaped Date Strings

**Location**: `main.py` lines 381-383
**Severity**: HIGH (if backend uses SQL)
**Impact**: SQL injection, data breach

**Issue**:
```python
'ntcStartDt': start_date.strftime('%Y-%m-%d'),
'ntcEndDt': end_date.strftime('%Y-%m-%d')
```

**Problem**:
- If the backend Korean Forest Service website uses these parameters directly in SQL queries
- No evidence backend sanitizes input
- Date strings could theoretically be crafted with SQL injection payloads

**Example Attack Vector**:
```python
# If start_date was somehow manipulated to:
"2024-01-01' OR '1'='1"
```

**Current Protection**:
- User selects dates from `st.date_input()` widget (produces `datetime.date` objects)
- `.strftime()` format is safe for well-formed dates
- **BUT**: No validation that dates are actually `datetime` objects before formatting

**Recommendation**:
1. Add type checking: `assert isinstance(start_date, (date, datetime))`
2. Sanitize date strings even after formatting
3. Add request signing if API supports it

**Risk**: Low-Medium (Requires compromising Streamlit's date widget)

---

## 2. Major Issues (Should Fix)

### 2.1 Fragile HTML Parsing with Hard-Coded Indices

**Location**: `main.py` lines 326-339, 363-378
**Severity**: MAJOR
**Impact**: Parsing failures, incorrect data extraction

**Issue**:
```python
def _lookup_index(labels: List[str], default: int) -> int:
    for header_text, idx in header_map.items():
        for label in labels:
            if label in header_text:
                return idx
    return default  # Falls back to hard-coded defaults

number_idx = _lookup_index(['번호', 'No', 'NO'], 0)  # Default: 0
title_idx = _lookup_index(['제목', 'Title'], 1)      # Default: 1
department_idx = _lookup_index(['부서', '담당', '기관'], 2)  # Default: 2
```

**Problem**:
- Falls back to hard-coded column indices (0, 1, 2, 3, 4, 5) if headers not found
- Website structure change will silently produce wrong data
- No validation that extracted data makes sense

**Example Failure**:
```
# If website changes table to:
# [Checkbox] [번호] [제목] [부서] [날짜] [조회]
#    0         1      2      3      4      5
# Current code expects:
# [번호] [제목] [부서] [날짜] [첨부] [조회]
#   0      1      2      3      4      5
# Result: Wrong data in wrong columns
```

**Recommendation**:
1. **Fail loudly** if header_map is empty (no headers found)
2. Make header detection mandatory, no fallback indices
3. Add schema validation to extracted data
4. Alert if column structure doesn't match expected pattern

**Code Fix**:
```python
def _lookup_index(labels: List[str]) -> int:
    for header_text, idx in header_map.items():
        for label in labels:
            if label in header_text:
                return idx
    raise ParsingException(f"Required column not found: {labels}")
```

**Risk**: High (Website changes will silently corrupt data)

---

### 2.2 Race Condition in File I/O

**Location**: `app.py` lines 88-119
**Severity**: MAJOR
**Impact**: Corrupted log files, data loss

**Issue**:
```python
_history_file_lock = threading.Lock()

def _append_history_log(entry: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)  # Not under lock!
    # ... process entry ...

    with _history_file_lock:
        with HISTORY_LOG_PATH.open("a", encoding="utf-8") as fp:
            fp.write("\n".join(lines) + "\n")
```

**Problem**:
- `LOG_DIR.mkdir()` happens **outside** the lock (line 91)
- Multiple Streamlit processes could race on directory creation
- `threading.Lock()` doesn't protect across processes (same as issue 1.1)
- File append is not atomic

**Recommendation**:
1. Use `fcntl.flock()` for inter-process file locking (Unix)
2. Use `msvcrt.locking()` for Windows
3. Or use database/Redis for persistent logging
4. Move `mkdir()` inside lock

**Risk**: Medium (File corruption under high load)

---

### 2.3 Unbounded Memory Growth in Session State

**Location**: `app.py` lines 74-85, 519-526
**Severity**: MAJOR
**Impact**: Memory exhaustion, application crash

**Issue**:
```python
def _append_history(entry: dict, max_entries: int = 5) -> None:
    def _updater(items):
        new_items = list(items)
        new_items.append(entry)
        if len(new_items) > max_entries:
            new_items = new_items[-max_entries:]  # Keep last 5
        return new_items
```

**BUT**:
```python
# Line 519-526: Keeps ALL items in all_item_status
all_item_status = []  # Never limited!
# ...
for idx, item in enumerate(items, 1):
    # ...
    all_item_status.append(entry)  # Grows unbounded!
```

**Problem**:
- `all_item_status` list grows without limit during long crawls
- Stores 100s or 1000s of status dictionaries in memory
- Each DataFrame in history also stored in memory
- Streamlit session state persists across reruns

**Size Estimate**:
```
1000 pages × 10 items/page = 10,000 status entries
Each entry ~500 bytes = 5 MB
Plus DataFrames: 10,000 rows × 10 columns × 100 bytes = 10 MB
Total per session: ~15 MB minimum
```

**Recommendation**:
1. Limit `all_item_status` to last 1000 items
2. Paginate status table display
3. Move completed crawl data to disk
4. Clear session state after download
5. Add memory monitoring

**Risk**: High (Crash after ~10,000 items crawled)

---

### 2.4 Duplicate Crawling Logic (DRY Violation)

**Location**: `app.py` lines 663-677
**Severity**: MAJOR (Maintainability)
**Impact**: Bug proliferation, inconsistent behavior

**Issue**:
```python
# Line 663
if start_crawl:
    _set_session_values(crawl_logs=[], crawl_data=None, crawl_completed=False)
    run_crawling(start_date, end_date, days, delay, page_delay)

# Line 671
if export_data:
    _set_session_values(crawl_logs=[], crawl_data=None, crawl_completed=False)
    run_crawling(start_date, end_date, days, delay, page_delay)
```

**Problem**:
- Identical code duplicated for two buttons
- Button names suggest different behavior but code is identical
- "크롤링 및 완료시 엑셀파일 작성" button name misleading (doesn't auto-download)
- Future bugs will affect only one button if not updated in both places

**Recommendation**:
```python
if start_crawl or export_data:
    _set_session_values(crawl_logs=[], crawl_data=None, crawl_completed=False)
    run_crawling(start_date, end_date, days, delay, page_delay)
```

Or make export_data button actually different:
```python
if export_data:
    # ... run crawling ...
    if crawl_completed:
        auto_download_excel()
```

**Risk**: Medium (Maintenance burden, user confusion)

---

### 2.5 Missing Type Hints in Critical Functions

**Location**: Throughout `app.py` and `main.py`
**Severity**: MAJOR
**Impact**: Reduced code maintainability, harder debugging

**Issue**:
```python
# app.py line 131
def add_log(message, log_type="INFO"):  # No type hints
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    entry = f"[{timestamp}] [{log_type}] {message}"
    # ...

# app.py line 143
def df_to_excel_bytes(df: pd.DataFrame) -> bytes:  # Good! Has types
    buffer = BytesIO()
    df.to_excel(buffer, index=False, engine='openpyxl')
    return buffer.getvalue()
```

**Coverage**:
- ~30% of functions have type hints
- `app.py` mostly missing types
- `main.py` has partial typing (lines 51, 79, 108, 169, 199, 283)
- `src/core/` has good typing

**Recommendation**:
1. Add type hints to all function signatures
2. Use `mypy` in strict mode (already in requirements-dev.txt)
3. Add to pre-commit hooks
4. Target: >90% type coverage

**Example Fix**:
```python
from typing import Dict, List, Optional

def add_log(message: str, log_type: str = "INFO") -> None:
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    entry = f"[{timestamp}] [{log_type}] {message}"
    # ...
```

**Risk**: Medium (Harder to catch bugs during development)

---

### 2.6 Inefficient DataFrame Operations

**Location**: `app.py` lines 533-558
**Severity**: MAJOR
**Impact**: Performance degradation, slow UI updates

**Issue**:
```python
if crawler.data:
    df = pd.DataFrame(crawler.data)  # Creates DataFrame every loop iteration

    preview_columns = [
        ('number', '번호'),
        ('title', '제목'),
        # ... 9 columns total
    ]

    available_preview_cols = [col for col, _ in preview_columns if col in df.columns]
    preview_df = df[available_preview_cols].copy()  # Full copy
    rename_map = {col: label for col, label in preview_columns if col in preview_df.columns}
    preview_df = preview_df.rename(columns=rename_map)  # Creates new DataFrame

    result_placeholder.dataframe(preview_df, ...)  # Renders to UI
```

**Problem**:
- Creates new DataFrame on every item processed in loop (line 370-530)
- Copies entire DataFrame (`.copy()`)
- Creates new DataFrame again (`.rename()`)
- Renders to Streamlit UI repeatedly
- For 1000 items, this runs 100+ times

**Performance Impact**:
```
DataFrame creation: O(n)
Column selection: O(n)
Copy: O(n)
Rename: O(n)
Streamlit render: O(n)
Total per iteration: O(5n)
For 1000 items / 100 pages: ~50,000 operations
```

**Recommendation**:
1. Only create DataFrame once per page, not per item
2. Use view instead of copy: `preview_df = df[cols]` (no `.copy()`)
3. Debounce UI updates (update every 10 items, not every item)
4. Use `st.empty()` placeholder more efficiently

**Risk**: High (UI freezes during large crawls)

---

## 3. Minor Issues (Nice to Fix)

### 3.1 Magic Numbers Throughout Code

**Location**: Multiple locations
**Severity**: MINOR
**Impact**: Reduced maintainability

**Examples**:
```python
# app.py line 74
def _append_history(entry: dict, max_entries: int = 5):  # Why 5?

# app.py line 519
recent_status = all_item_status[-100:]  # Why 100?

# app.py line 557
height=600  # Why 600?

# main.py line 275
backoff = min(2 ** attempt, 60)  # Why 60?

# main.py line 577
if page_index > 500:  # Why 500?
```

**Recommendation**:
Define constants at module level:
```python
MAX_HISTORY_ENTRIES = 5
STATUS_TABLE_LIMIT = 100
DATAFRAME_HEIGHT_PX = 600
MAX_BACKOFF_SECONDS = 60
MAX_PAGES_PER_CRAWL = 500
```

---

### 3.2 Inconsistent Error Handling

**Location**: Throughout both files
**Severity**: MINOR
**Impact**: Unpredictable error recovery

**Examples**:
```python
# Some places use logging
self.logger.warning(f"타임아웃 (시도 {attempt + 1}/{max_retries}): {url}")

# Some use Streamlit
st.error(f"Excel 생성 실패: {e}")

# Some use add_log()
add_log(f"오류 발생: {str(e)}", "ERROR")

# Some use bare except
except Exception as e:
    st.error(f"CSV 생성 실패: {e}")

# Some re-raise
raise CrawlerException(...) from e
```

**Recommendation**:
Standardize error handling:
1. Business logic: Use logging
2. User-facing errors: Use Streamlit messages
3. Always log full traceback to file
4. Never use bare `except Exception`

---

### 3.3 Mixed String Formatting Styles

**Location**: Throughout
**Severity**: MINOR
**Impact**: Code inconsistency

**Examples**:
```python
# f-strings (modern, preferred)
f"[{timestamp}] [{log_type}] {message}"

# %-formatting (old style)
# Not found in this code

# .format() (intermediate)
# Not found in this code

# String concatenation
'logs/crawler_' + datetime.now().strftime("%Y%m%d") + '.log'  # Should use f-string
```

**Recommendation**: Use f-strings everywhere (already mostly done)

---

### 3.4 Hardcoded Korean Strings (i18n)

**Location**: Throughout
**Severity**: MINOR
**Impact**: Limited internationalization

**Examples**:
```python
st.title("🌲 산림청 입찰정보 크롤러")
st.sidebar.header("⚙️ 크롤링 설정")
add_log("크롤링 시작", "INFO")
```

**Recommendation**:
If internationalization needed:
1. Extract strings to `locales/ko.json`, `locales/en.json`
2. Use `gettext` or simple dictionary lookup
3. Add language selector to sidebar

Current state: Acceptable for Korea-only deployment

---

### 3.5 No Input Sanitization for File Names

**Location**: `app.py` lines 255, 298, 698
**Severity**: MINOR
**Impact**: File system issues on Windows

**Issue**:
```python
file_name=f"산림청_입찰_{selected_history['timestamp']}.xlsx"
# timestamp format: '2024-10-06_14-30-45'
# Contains ':' which is invalid in Windows filenames
```

**Wait, checking the code again...**
Actually timestamp is formatted as: `datetime.now().strftime('%Y-%m-%d_%H-%M-%S')`
This produces `2024-10-06_14-30-45` which is safe (uses `-` not `:`).

**Status**: Not an issue, but document why this format is used

---

### 3.6 Incomplete Docstrings

**Location**: Multiple functions
**Severity**: MINOR
**Impact**: Reduced code readability

**Examples**:
```python
# Good docstring
def parse_list_page(self, soup):
    """
    리스트 페이지에서 게시글 정보 추출

    Args:
        soup (BeautifulSoup): 파싱된 HTML

    Returns:
        list: 게시글 정보 리스트 (번호, 링크, 날짜 등)
    """

# Missing docstrings
def _append_history(entry: dict, max_entries: int = 5) -> None:
    """Append a history item while bounding list length."""
    # No Args, Returns, or Examples

def add_log(message, log_type="INFO"):
    # No docstring at all
```

**Recommendation**:
- Add Google-style or NumPy-style docstrings to all public functions
- Include type information in docstrings
- Add usage examples for complex functions

---

### 3.7 Commented-Out Debug Code

**Location**: `app.py` line 411
**Severity**: MINOR
**Impact**: Code clutter

**Issue**:
```python
debug_table = st.empty()
```
This creates a variable named `debug_table` which suggests debugging purposes.
However, it's actively used for status display (line 521), so name is misleading.

**Recommendation**: Rename to `status_table_placeholder`

---

### 3.8 Unused Imports

**Location**: `main.py`
**Severity**: MINOR
**Impact**: Code bloat

**Checking imports...**
```python
from pathlib import Path  # Used: line 28, 691
from email.utils import parsedate_to_datetime  # Used: line 229
from typing import Optional, Dict, List, Any  # Used throughout
import json  # Used: line 36, 62, 68
import yaml  # Not found in main.py
```

**Status**: All imports in main.py are used. Clean.

---

## 4. Security Analysis

### 4.1 Authentication & Authorization
**Status**: NOT IMPLEMENTED
**Risk**: Low (runs locally, no multi-tenancy)

- No user authentication
- No access control
- No rate limiting per user
- Acceptable for single-user local deployment

**Recommendation**: Add auth if deploying to public server

---

### 4.2 Data Validation & Sanitization

#### Input Validation
**Status**: PARTIAL

**Validated**:
- Date range: Max 10 years (line 149-159 in main.py)
- Delay bounds: Min 0.5s, min 1.0s for page delay (line 162-165)
- Plugin names: Alphanumeric + underscore only (line 238 parser_factory.py)

**Not Validated**:
- Page numbers before use
- HTML content before parsing
- File paths before writing
- User-provided data in session state

#### Output Sanitization
**Status**: WEAK

- No HTML escaping in Streamlit output (Streamlit handles this)
- No validation of scraped data before display
- Excel/CSV output not sanitized (could contain formula injection)

**Excel Formula Injection Risk**:
```python
# If scraped data contains:
title = "=CMD|'/c calc'!A1"
# When opened in Excel, this could execute commands
```

**Recommendation**:
```python
def sanitize_excel_formula(value: str) -> str:
    if isinstance(value, str) and value.startswith(('=', '+', '-', '@')):
        return "'" + value  # Prefix with ' to make it text
    return value
```

---

### 4.3 Sensitive Data Handling

**Status**: GOOD

- No hardcoded credentials
- No API keys in code
- No sensitive data logged
- Session state not persisted to disk

**Minor Issue**: Checkpoint file (`crawl_checkpoint.json`) stores URLs without authentication, which is fine for public data.

---

### 4.4 Dependency Vulnerabilities

**Analysis**:
```
requests>=2.31.0          # Released 2023-05, check CVEs
beautifulsoup4>=4.12.0    # Released 2023-01, generally safe
pandas>=2.0.0             # Released 2023-04, check CVEs
openpyxl>=3.1.0           # XML parsing, check for XXE
streamlit>=1.28.0         # Released 2023-11, check CVEs
```

**Recommendation**:
1. Run `pip-audit` or `safety check` on dependencies
2. Use Dependabot or Renovate for automated updates
3. Pin exact versions in production

---

### 4.5 Logging & Monitoring

**Status**: PARTIAL

**What's Logged**:
- Crawler events (page fetches, parsing, errors)
- User actions in UI (via add_log)
- HTTP errors and retries

**What's NOT Logged**:
- Security events (failed validations)
- Performance metrics (response times)
- User sessions (who's using the app)

**Log Storage**:
- Files in `logs/` directory (readable by any local user)
- No log rotation (files grow unbounded)
- No log shipping to central server

**Recommendation**:
1. Add structured logging (JSON format)
2. Implement log rotation (`RotatingFileHandler`)
3. Log security events
4. Consider ELK stack for production

---

### 4.6 Error Information Disclosure

**Status**: VULNERABLE

**Issue**:
```python
# app.py line 648-650
except Exception as e:
    status_text.error(f"❌ 오류 발생: {e}")
    add_log(f"오류 발생: {str(e)}", "ERROR")
    st.exception(e)  # Shows full traceback to user!
```

**Problem**:
- `st.exception(e)` displays full stack trace in web UI
- Could leak file paths, internal structure, library versions
- Helps attackers fingerprint the system

**Recommendation**:
```python
except Exception as e:
    status_text.error("❌ 크롤링 중 오류가 발생했습니다. 로그를 확인해주세요.")
    logger.exception("Crawling failed")  # Log full trace to file
    # Don't use st.exception() in production
```

---

## 5. Performance Analysis

### 5.1 Network Performance

**Current Implementation**:
```python
delay=1.0,     # 1 second between requests
page_delay=2.0 # 2 seconds between pages
```

**Throughput**:
```
10 items/page × 1 second delay = 10 seconds/page (requests)
+ 2 second page delay
= ~12 seconds/page
= 5 pages/minute
= 300 pages/hour
= 3000 items/hour
```

**Bottlenecks**:
1. Sequential requests (no parallelism)
2. Fixed delays (doesn't adapt to server speed)
3. No request pipelining

**Recommendation**:
1. Implement adaptive delays (faster if server responds quickly)
2. Use `asyncio` + `aiohttp` for async requests
3. Respect `Retry-After` header (already done in line 222-246)
4. Add connection pooling

**Potential Speedup**: 3-5x with async

---

### 5.2 Memory Performance

**Current Memory Usage** (estimated):

Per crawl session:
```
Session state: ~5-10 MB (history, logs)
DataFrame: ~10 KB per item × 3000 items = 30 MB
BeautifulSoup objects: ~500 KB per page (temporary)
Streamlit overhead: ~50 MB
Total: ~100 MB per active session
```

**Memory Leaks**:
1. `all_item_status` grows unbounded (issue 2.3)
2. BeautifulSoup not explicitly closed (GC will handle, but slow)
3. Session state never cleared

**Recommendation**:
1. Add memory profiling (`memory_profiler`)
2. Clear completed data from session state
3. Use generators instead of lists where possible

---

### 5.3 I/O Performance

**File Operations**:
```python
# Inefficient: Opens file once per log entry
with HISTORY_LOG_PATH.open("a", encoding="utf-8") as fp:
    fp.write("\n".join(lines) + "\n")
```

**Recommendation**:
1. Batch writes (buffer 100 entries)
2. Use buffered I/O
3. Consider async file writes

**Excel Generation**:
```python
df.to_excel(buffer, index=False, engine='openpyxl')
```
- `openpyxl` is slow for large files (>10K rows)
- Consider `xlsxwriter` engine for better performance

---

### 5.4 CPU Performance

**Hot Spots** (profiling recommended):
1. `BeautifulSoup(response.text, 'html.parser')` - CPU intensive
2. `pd.DataFrame(crawler.data)` - CPU + memory intensive
3. Regular expression in date parsing (line 382-388)

**Recommendation**:
1. Use `lxml` parser (faster than `html.parser`)
2. Create DataFrame once, not repeatedly
3. Compile regex patterns at module level

**Example**:
```python
# Module level
DATE_PATTERN = re.compile(r'(\d{4}[-.\s]\d{1,2}[-.\s]\d{1,2})')

# In function
date_match = DATE_PATTERN.search(date_str)
```

---

### 5.5 Streamlit Performance

**Issues**:
1. Full page reruns on every interaction
2. No caching of expensive operations
3. Large DataFrames rendered repeatedly

**Recommendation**:
```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_historical_data():
    # ...

@st.cache_resource
def get_crawler_instance():
    return ForestBidCrawler(...)
```

**Current Cache Usage**:
- Excel/CSV generation (lines 143-151) - No caching decorator, but should have
- Missing decorators

---

## 6. Code Quality Assessment

### 6.1 Code Complexity

**Cyclomatic Complexity** (estimated):

High complexity functions:
```
run_crawling() (app.py:335-651)     ~50 branches
parse_list_page() (main.py:283-439) ~30 branches
crawl() (main.py:525-617)           ~20 branches
```

**Recommendation**:
- Break down `run_crawling()` into smaller functions
- Extract UI rendering logic from business logic
- Target: <15 branches per function

---

### 6.2 Code Duplication

**Duplicated Logic**:

1. **DataFrame column selection** (3 places):
   - Line 536-551 (app.py)
   - Line 589-603 (app.py)
   - Line 636-663 (main.py)

2. **Excel/CSV generation** (4 places):
   - Line 250-260 (sidebar)
   - Line 288-317 (history expander)
   - Line 690-718 (download section)

**Recommendation**: Extract to shared functions

---

### 6.3 Testing Coverage

**Current Tests** (from test_crawler.py):
- 18 unit tests for crawler
- 9 parsing tests
- 1 parser factory test

**Coverage**: ~42% (per README)

**Missing Tests**:
- Streamlit UI interactions
- Error recovery scenarios
- Edge cases in date parsing
- Concurrent access tests
- Integration tests

**Recommendation**:
1. Add integration tests with mock HTTP responses
2. Test error paths (network failures, malformed HTML)
3. Add property-based tests with Hypothesis
4. Target: >80% coverage

---

### 6.4 Code Style

**Consistency**: Generally good

**PEP 8 Compliance** (visual inspection):
- Indentation: Consistent 4 spaces ✓
- Line length: Some lines >100 chars (acceptable)
- Naming: Mixed (Korean + English, but consistent within files)
- Blank lines: Generally good

**Recommendation**:
- Run `black` formatter (already in requirements-dev.txt)
- Run `ruff` linter
- Add to pre-commit hooks

---

### 6.5 Documentation Quality

**Module Docstrings**: Present in core modules ✓
**Function Docstrings**: ~60% coverage
**Inline Comments**: Good, especially for complex logic
**External Docs**: Comprehensive README, architecture docs ✓

**Quality**: Above average for projects of this size

---

## 7. Best Practices Review

### 7.1 Python Best Practices

**Good**:
- Context managers for file I/O (`with` statements)
- Pathlib for file paths
- List comprehensions instead of loops
- Type hints in core modules

**Needs Improvement**:
- Global mutable state (`_session_lock`, `_history_file_lock`)
- Module-level side effects (line 122-128 in app.py)
- Bare `except Exception` in some places

---

### 7.2 Streamlit Best Practices

**Good**:
- Session state for data persistence
- `st.empty()` for dynamic updates
- Column layouts for UI organization

**Needs Improvement**:
- No use of `@st.cache_data` or `@st.cache_resource`
- Full page reruns not optimized
- No form submission (all interactions trigger reruns)

**Recommendation**:
```python
with st.form("crawl_settings"):
    start_date = st.date_input("시작일")
    end_date = st.date_input("종료일")
    submitted = st.form_submit_button("크롤링 시작")

if submitted:
    run_crawling(...)
```

---

### 7.3 Web Scraping Ethics

**Good**:
- Configurable delays between requests
- Respects `Retry-After` headers
- User-agent string provided
- Targets public government data

**Needs Improvement**:
- No robots.txt checking
- No rate limiting per session
- Could add "purpose" to user-agent string

**Recommendation**:
```python
headers = {
    'User-Agent': 'KoreaForestBidCrawler/1.1 (Research purposes; contact@example.com)',
}
```

---

### 7.4 Error Handling Patterns

**Current Pattern**: Try-catch at multiple levels

**Issues**:
- Some errors silently logged, others shown to user
- Inconsistent error propagation
- No error recovery in UI (must restart crawl)

**Recommendation**: Implement error hierarchy
```python
class CrawlerError(Exception): pass
class NetworkError(CrawlerError): pass
class ParsingError(CrawlerError): pass
class ValidationError(CrawlerError): pass
```

---

### 7.5 Configuration Management

**Current**: Hardcoded values in UI and code

**Recommendation**: Use config file
```yaml
# config.yaml
crawler:
  default_delay: 1.0
  default_page_delay: 2.0
  max_pages: 500
  max_date_range_years: 10

ui:
  max_history_entries: 5
  status_table_limit: 100

logging:
  level: INFO
  rotation: daily
```

---

## 8. Dependency Analysis

### 8.1 Production Dependencies

**File**: `requirements.txt`

```
requests>=2.31.0        ✓ Core HTTP library, well-maintained
beautifulsoup4>=4.12.0  ✓ HTML parsing, stable
pandas>=2.0.0           ✓ Data manipulation, large dependency
openpyxl>=3.1.0         ✓ Excel support, required
lxml>=4.9.0             ⚠️ Listed but not used (uses html.parser)
streamlit>=1.28.0       ✓ UI framework, core dependency
python-dateutil>=2.8.2  ✓ Date parsing, used
PyYAML>=6.0             ⚠️ Listed but only used in parser_factory
```

**Issues**:
1. `lxml` listed but `html.parser` used in code
2. `PyYAML` only needed for future plugin system
3. No version upper bounds (could break on major updates)

**Recommendation**:
```
# requirements.txt
requests>=2.31.0,<3.0.0
beautifulsoup4>=4.12.0,<5.0.0
pandas>=2.0.0,<3.0.0
openpyxl>=3.1.0,<4.0.0
lxml>=4.9.0,<5.0.0  # Or remove if not needed
streamlit>=1.28.0,<2.0.0
python-dateutil>=2.8.2,<3.0.0
PyYAML>=6.0,<7.0.0
```

---

### 8.2 Development Dependencies

**File**: `requirements-dev.txt`

```
pytest>=7.4.0           ✓ Testing framework
pytest-cov>=4.1.0       ✓ Coverage reporting
pytest-mock>=3.11.0     ✓ Mocking support
black>=23.0.0           ✓ Code formatter
ruff>=0.1.0             ✓ Fast linter
mypy>=1.5.0             ✓ Type checker
pre-commit>=3.4.0       ✓ Git hooks
```

**Status**: Excellent selection, modern tooling ✓

---

### 8.3 Missing Dependencies

**Potential Additions**:

1. **Security**:
   - `pip-audit` - Vulnerability scanning
   - `bandit` - Security linter

2. **Performance**:
   - `memory-profiler` - Memory analysis
   - `py-spy` - CPU profiling

3. **Production**:
   - `gunicorn` - If deploying as production server
   - `python-dotenv` - Environment variable management

4. **Async** (for future):
   - `aiohttp` - Async HTTP
   - `asyncio` - Built-in, but document usage

---

### 8.4 Dependency Security Scan

**Recommendation**: Run security audit

```bash
pip install pip-audit
pip-audit

# Or use safety
pip install safety
safety check
```

**Known CVEs** (as of Dec 2025):
- Check each dependency against CVE database
- Set up automated scanning in CI/CD

---

## 9. Recommendations

### 9.1 Immediate Actions (Critical)

**Priority 1 - Security & Stability**:

1. **Remove module reload** (Issue 1.2)
   ```python
   # DELETE lines 18-22 in app.py
   ```

2. **Remove threading locks** (Issue 1.1)
   ```python
   # DELETE _session_lock and _history_file_lock
   # Use Streamlit's session state directly
   ```

3. **Fix unbounded memory growth** (Issue 2.3)
   ```python
   # Limit all_item_status to 1000 entries
   if len(all_item_status) > 1000:
       all_item_status = all_item_status[-1000:]
   ```

4. **Add page validation** (Issue 1.4)
   ```python
   if not 1 <= page_index <= 500:
       raise ValueError(f"Invalid page: {page_index}")
   ```

---

### 9.2 Short-term Improvements (1-2 weeks)

**Priority 2 - Code Quality**:

1. **Add type hints** to all functions
2. **Run black formatter** on entire codebase
3. **Add docstrings** to remaining functions
4. **Implement proper error hierarchy**
5. **Add schema validation** to parsed data
6. **Remove code duplication** (DRY violations)

---

### 9.3 Medium-term Enhancements (1 month)

**Priority 3 - Performance & Features**:

1. **Implement caching** with `@st.cache_data`
2. **Add async HTTP** with aiohttp
3. **Optimize DataFrame operations**
4. **Add configuration file** (YAML)
5. **Implement log rotation**
6. **Add structured logging** (JSON)
7. **Increase test coverage** to >80%

---

### 9.4 Long-term Roadmap (3-6 months)

**Priority 4 - Architecture**:

1. **Complete plugin architecture** (src/core/)
2. **Add authentication** if deploying publicly
3. **Implement database backend** for results
4. **Add API layer** for headless operation
5. **Create monitoring dashboard**
6. **Add alerting** for crawl failures

---

### 9.5 Code Refactoring Plan

**Phase 1: Critical Fixes** (1 week)
```
1. Remove module reload
2. Fix threading issues
3. Add memory limits
4. Add input validation
```

**Phase 2: Quality Improvements** (2 weeks)
```
1. Add type hints everywhere
2. Extract duplicate code
3. Simplify complex functions
4. Add comprehensive tests
```

**Phase 3: Performance** (2 weeks)
```
1. Implement caching
2. Optimize DataFrame ops
3. Add async support
4. Profile and optimize hot paths
```

**Phase 4: Production Readiness** (3 weeks)
```
1. Add monitoring
2. Implement proper logging
3. Add deployment automation
4. Security hardening
```

---

## 10. Conclusion

### Overall Assessment

**Strengths**:
- Functional core crawler logic
- Good UI/UX with Streamlit
- Comprehensive documentation
- Unit tests for critical paths
- Active development and iteration

**Weaknesses**:
- Threading misuse creates false sense of security
- Memory management issues
- Limited error recovery
- Performance not optimized for large crawls

**Production Readiness**: 60%

**Recommendation**: Address critical issues before production deployment. The codebase is well-structured but needs hardening for production use.

---

### Risk Assessment

| Category | Risk Level | Mitigation Priority |
|----------|-----------|---------------------|
| Security | Medium | High |
| Stability | Medium-High | High |
| Performance | Medium | Medium |
| Maintainability | Low-Medium | Medium |
| Scalability | Medium | Low |

---

### Next Steps

1. **Immediate** (This Week):
   - Fix issues 1.1, 1.2, 2.3
   - Add input validation
   - Run security audit on dependencies

2. **Short-term** (This Month):
   - Add type hints
   - Increase test coverage
   - Optimize performance

3. **Long-term** (Next Quarter):
   - Complete plugin architecture
   - Add monitoring
   - Production deployment

---

## Appendix A: File Inventory

**Core Application Files**:
- `app.py` - 789 lines - Streamlit UI
- `main.py` - 750 lines - Crawler engine

**Core Library**:
- `src/core/base_crawler.py` - 222 lines - Abstract base
- `src/core/parser_factory.py` - 269 lines - Plugin loader
- `src/core/__init__.py` - 12 lines - Module exports

**Tests** (3 files, 27 tests):
- `tests/unit/test_crawler.py` - 121 lines - 18 tests
- `tests/unit/test_parsing.py` - ~200 lines - 9 tests (estimate)
- `tests/unit/test_parser_factory.py` - ~70 lines - 1 test (estimate)

**Configuration**:
- `requirements.txt` - 9 lines - Production deps
- `requirements-dev.txt` - 16 lines - Dev deps
- `.streamlit/config.toml` - 7 lines - Streamlit config

**Total LOC**: ~2,500 lines (excluding docs)

---

## Appendix B: Security Checklist

- [ ] Input validation on all user inputs
- [ ] SQL injection prevention (N/A - no database)
- [ ] XSS prevention (handled by Streamlit)
- [ ] CSRF protection (N/A - no forms with state changes)
- [ ] Authentication & authorization (N/A - local deployment)
- [ ] Secure session management (partial - no encryption)
- [ ] File upload validation (N/A - no uploads)
- [ ] Dependency vulnerability scanning
- [ ] Error message sanitization
- [ ] Logging without sensitive data
- [ ] HTTPS enforcement (deployment concern)
- [ ] Rate limiting (partial - delays only)

---

## Appendix C: Performance Benchmarks

**Recommended Benchmarking**:

```python
# Add to tests/benchmark/
import time
import pytest

def test_parsing_performance():
    # Parse 1000 sample HTML snippets
    # Target: <10ms per parse

def test_dataframe_creation():
    # Create DataFrame from 10k items
    # Target: <500ms

def test_excel_generation():
    # Generate Excel from 10k rows
    # Target: <5 seconds
```

**Current Performance** (estimated):
- Parse rate: ~100 items/minute
- Memory usage: ~100 MB per session
- Excel generation: ~10 seconds for 3000 rows

---

**End of Audit Report**

Generated: 2025-12-10
Auditor: Automated Code Review System
Classification: Internal Use - Development Documentation
