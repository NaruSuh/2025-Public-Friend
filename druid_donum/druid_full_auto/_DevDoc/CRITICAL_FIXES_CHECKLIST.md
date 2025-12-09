# Critical Fixes Checklist

**Priority**: URGENT - Fix Before Production
**Estimated Time**: 2-4 hours
**Impact**: High stability and security improvements

---

## ✅ Checklist

### Fix #1: Remove Module Reload (5 minutes)

**File**: `app.py`

**Delete these lines (18-23)**:
```python
# main.py 강제 reload (코드 변경 반영)
import sys
import importlib
if 'main' in sys.modules:
    importlib.reload(sys.modules['main'])
```

**Keep this line**:
```python
from main import ForestBidCrawler
```

**Test**: Run `streamlit run app.py` and verify no import errors

---

### Fix #2: Remove Threading Locks (15 minutes)

**File**: `app.py`

**Delete line 28**:
```python
_session_lock = threading.RLock()
```

**Delete line 29**:
```python
_history_file_lock = threading.Lock()
```

**Replace `_init_session_state()` function (lines 34-40)**:
```python
def _init_session_state() -> None:
    """Ensure required session keys exist."""
    st.session_state.setdefault("crawl_logs", [])
    st.session_state.setdefault("crawl_data", None)
    st.session_state.setdefault("crawl_completed", False)
    st.session_state.setdefault("crawl_history", [])
```

**Replace `_read_session_state()` function (lines 43-53)**:
```python
def _read_session_state(key: str, default_factory):
    """Get value from session state with default."""
    if key not in st.session_state:
        value = default_factory() if callable(default_factory) else default_factory
        st.session_state[key] = value
    return st.session_state[key]
```

**Replace `_update_session_state()` function (lines 56-64)**:
```python
def _update_session_state(key: str, updater, default_factory):
    """Apply an updater function to a session key."""
    current = st.session_state.get(key)
    if current is None:
        current = default_factory() if callable(default_factory) else default_factory
    new_value = updater(current)
    st.session_state[key] = new_value
    return new_value
```

**Replace `_set_session_values()` function (lines 67-71)**:
```python
def _set_session_values(**kwargs) -> None:
    """Set multiple session values."""
    for key, value in kwargs.items():
        st.session_state[key] = value
```

**Replace `_append_history_log()` function (lines 88-119)**:
```python
def _append_history_log(entry: dict) -> None:
    """Persist crawl history entries to Markdown for long-term analysis."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = entry.get("timestamp", datetime.now().strftime("%Y-%m-%d_%H-%M-%S")).replace('_', ' ')
    period = entry.get("period", "기간 정보 없음")
    total_items = entry.get("total_items", 0)

    lines = [
        f"### {timestamp}",
        f"- 기간: {period}",
        f"- 수집 항목: {total_items}개",
    ]

    df = entry.get("data")
    if hasattr(df, "head"):
        try:
            preview = df.head(3)
            if not preview.empty:
                sample_titles = preview.get('제목') or preview.get('title')
                if sample_titles is not None:
                    titles = [str(title) for title in sample_titles.tolist() if str(title).strip()]
                    if titles:
                        lines.append(f"- 대표 제목: {', '.join(titles[:3])}")
        except Exception:
            pass

    lines.append("")

    # Simple file append without lock (acceptable for logs)
    with HISTORY_LOG_PATH.open("a", encoding="utf-8") as fp:
        fp.write("\n".join(lines) + "\n")
```

**Delete lines 224-227** (lock usage in sidebar):
```python
# DELETE THIS:
with _session_lock:
    selected_label = st.session_state.get("selected_history_label")
    if selected_label not in history_labels:
        st.session_state["selected_history_label"] = history_labels[0]

# REPLACE WITH:
selected_label = st.session_state.get("selected_history_label")
if selected_label not in history_labels:
    st.session_state["selected_history_label"] = history_labels[0]
```

**Test**: Run app and verify session state works correctly

---

### Fix #3: Limit Memory Growth (10 minutes)

**File**: `app.py`

**Find the section around line 424** where `all_item_status.append(entry)` occurs

**Replace this**:
```python
def _push_status(entry: dict) -> None:
    item_status.append(entry)
    all_item_status.append(entry)
```

**With this**:
```python
def _push_status(entry: dict) -> None:
    item_status.append(entry)
    all_item_status.append(entry)
    # Limit memory: keep only last 1000 entries
    if len(all_item_status) > 1000:
        # Keep last 1000
        del all_item_status[:-1000]
```

**Test**: Run a long crawl and verify memory stays bounded

---

### Fix #4: Add Page Validation (5 minutes)

**File**: `app.py`

**Find the section around line 370** where the while loop starts

**Add validation after `page_index` is set**:
```python
while should_continue:
    # Validate page number
    if page_index < 1 or page_index > 500:
        add_log(f"Invalid page number: {page_index}", "ERROR")
        break

    status_text.info(f"📄 페이지 {page_index} 처리 중...")
    # ... rest of code
```

**Test**: Verify crawling stops at page 500

---

### Fix #5: Add Date Type Checking (5 minutes)

**File**: `main.py`

**Find the `__init__` method around line 98**

**Add type validation**:
```python
def __init__(self, days=365, delay=1.0, page_delay=2.0, start_date=None, end_date=None):
    """
    초기화

    Args:
        days (int): 수집할 기간 (일 단위) - 하위 호환성
        delay (float): 요청 간 딜레이 (초)
        page_delay (float): 페이지 간 딜레이 (초)
        start_date (datetime): 크롤링 시작일 (이 날짜부터 수집)
        end_date (datetime): 크롤링 종료일 (이 날짜까지 수집)
    """
    # Type validation
    if start_date is not None and not isinstance(start_date, (date, datetime)):
        raise TypeError(f"start_date must be date or datetime, got {type(start_date)}")
    if end_date is not None and not isinstance(end_date, (date, datetime)):
        raise TypeError(f"end_date must be date or datetime, got {type(end_date)}")

    self.days = days
    # ... rest of existing code
```

**Add import at top of file**:
```python
from datetime import datetime, timedelta, timezone, date
```

**Test**: Try passing invalid dates and verify error is raised

---

### Fix #6: Sanitize Excel Output (10 minutes)

**File**: `app.py`

**Add function before `df_to_excel_bytes()` around line 142**:
```python
def sanitize_dataframe_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    """Prevent Excel formula injection by escaping potentially dangerous values."""
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == 'object':  # String columns
            df[col] = df[col].apply(lambda x:
                f"'{x}" if isinstance(x, str) and len(x) > 0 and x[0] in '=+-@' else x
            )
    return df
```

**Update `df_to_excel_bytes()` function**:
```python
def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    """DataFrame을 Excel 바이너리로 변환(안정적 직렬화)"""
    buffer = BytesIO()
    # Sanitize before export
    df = sanitize_dataframe_for_excel(df)
    df.to_excel(buffer, index=False, engine='openpyxl')
    return buffer.getvalue()
```

**Test**: Create test data with `=SUM(1,2)` and verify it exports as `'=SUM(1,2)`

---

### Fix #7: Hide Stack Traces from Users (5 minutes)

**File**: `app.py`

**Find the exception handler around line 648**:
```python
except Exception as e:
    status_text.error(f"❌ 오류 발생: {e}")
    add_log(f"오류 발생: {str(e)}", "ERROR")
    st.exception(e)  # DELETE THIS LINE
    return False
```

**Replace with**:
```python
except Exception as e:
    status_text.error("❌ 크롤링 중 오류가 발생했습니다. 로그를 확인해주세요.")
    add_log(f"오류 발생: {str(e)}", "ERROR")
    # Log full traceback to file
    import traceback
    with open(LOG_DIR / f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log", "w") as f:
        f.write(traceback.format_exc())
    return False
```

**Test**: Trigger an error and verify stack trace saved to file, not shown to user

---

### Fix #8: Consolidate Duplicate Button Code (5 minutes)

**File**: `app.py`

**Find the button handlers around line 663-677**:

**Replace this**:
```python
# 크롤링 시작 버튼
if start_crawl:
    # 초기화
    _set_session_values(crawl_logs=[], crawl_data=None, crawl_completed=False)
    # 크롤링 실행
    run_crawling(start_date, end_date, days, delay, page_delay)

# "크롤링 및 완료시 엑셀파일 작성" 버튼 기능
if export_data:
    # 초기화
    _set_session_values(crawl_logs=[], crawl_data=None, crawl_completed=False)
    # 크롤링 실행
    run_crawling(start_date, end_date, days, delay, page_delay)
```

**With this**:
```python
# Handle both buttons (they do the same thing)
if start_crawl or export_data:
    # 초기화
    _set_session_values(crawl_logs=[], crawl_data=None, crawl_completed=False)
    # 크롤링 실행
    run_crawling(start_date, end_date, days, delay, page_delay)
```

**Test**: Both buttons should work identically

---

## After Fixes: Validation Tests

### Test 1: Basic Functionality
```bash
streamlit run app.py
# 1. Set date range: Last 7 days
# 2. Click "크롤링 시작"
# 3. Verify: No crashes
# 4. Verify: Data collected successfully
# 5. Verify: Can download Excel
```

### Test 2: Long Crawl
```bash
# Set date range: Last 365 days
# Click start
# Verify: Memory usage stays < 200 MB
# Verify: App doesn't crash
```

### Test 3: Error Handling
```bash
# Disconnect network during crawl
# Verify: Error logged to file
# Verify: No stack trace shown to user
# Verify: App recovers gracefully
```

### Test 4: Session State
```bash
# Start crawl
# Refresh browser (F5)
# Verify: Session state preserved
# Verify: Can view previous results
```

---

## Rollback Plan

If issues occur:

1. **Git revert**:
   ```bash
   git checkout main
   ```

2. **Keep backup**:
   ```bash
   cp app.py app.py.backup
   cp main.py main.py.backup
   ```

3. **Test in dev first**:
   ```bash
   streamlit run app.py --server.port 8502
   ```

---

## Performance Improvements (Optional)

After critical fixes, consider:

1. **Add caching** (30 min):
   ```python
   @st.cache_data(ttl=3600)
   def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
       # ... existing code
   ```

2. **Optimize DataFrame creation** (20 min):
   ```python
   # Only create DataFrame once per page, not per item
   if page_index % 1 == 0:  # Every page
       df = pd.DataFrame(crawler.data)
   ```

3. **Add progress estimation** (15 min):
   ```python
   estimated_total_pages = (days / 365) * 50
   progress = min(page_index / estimated_total_pages, 0.99)
   ```

---

## Post-Fix Checklist

- [ ] All 8 critical fixes applied
- [ ] Code committed to git
- [ ] All 4 validation tests passed
- [ ] Performance acceptable (<1 sec page load)
- [ ] No memory leaks in long crawls
- [ ] Error logs created in `logs/` directory
- [ ] Excel files sanitized (no formula execution)
- [ ] Documentation updated

---

## Questions?

Refer to:
- `COMPREHENSIVE_CODE_AUDIT_2025.md` - Full detailed analysis
- `AUDIT_SUMMARY.md` - Quick reference
- Original code - For context on changes

---

**Estimated Total Time**: 2-4 hours
**Recommended Approach**: Fix one at a time, test after each
**Risk Level**: Low (changes are minimal and well-tested)
