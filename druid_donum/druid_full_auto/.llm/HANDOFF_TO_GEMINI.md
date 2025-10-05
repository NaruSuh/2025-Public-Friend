# 🤝 Handoff: Claude Code → Gemini CLI

**Date**: 2025-10-05 18:30 KST
**From**: Claude Code
**To**: Gemini CLI
**Status**: ✅ Ready for handoff

---

## 📋 What I Completed

### T002: BaseCrawler Abstract Class
- **File**: `src/core/base_crawler.py`
- **What it does**: Defines the interface that all site-specific crawler plugins must implement
- **Key methods**:
  1. `fetch_page(url, params) -> BeautifulSoup` - Fetch and parse HTML
  2. `parse_list(soup) -> List[Dict]` - Extract item list from board page
  3. `parse_detail(soup, item) -> Dict` - Extract detail from item page
  4. `build_params(page, start_date, end_date) -> Dict` - Build query parameters

### T003: ParserFactory Pattern
- **File**: `src/core/parser_factory.py`
- **What it does**: Dynamically loads and instantiates crawler plugins
- **Key methods**:
  - `create_crawler(site_name, config) -> BaseCrawler` - Factory method
  - `list_available_plugins() -> List[str]` - Discovery
  - `get_plugin_config(site_name) -> Dict` - Config loading

### Updated Documentation
- `CURRENT_STATUS.md` - Added handoff entry
- `.llm/task_assignments.yaml` - Marked T002, T003 as completed

---

## 🎯 Your Tasks

### T004: Create Plugin Template (Priority P1)
**Estimated**: 2 hours
**Output**: `src/plugins/template/`

Create a reference plugin structure:
```
src/plugins/template/
├── __init__.py
├── crawler.py          # Inherits from BaseCrawler
├── config.yaml         # Site configuration
└── README.md           # Plugin documentation
```

**config.yaml structure**:
```yaml
plugin:
  name: "template"
  display_name: "Template Plugin"
  version: "1.0.0"
  description: "Reference implementation for new plugins"

site:
  base_url: "https://example.com"
  board_url: "https://example.com/board"
  encoding: "utf-8"

selectors:
  list_table: "table.board-list"
  list_row: "tbody tr"
  title: "td.title a"
  date: "td.date"
  # ... other selectors

params:
  page_key: "page"
  page_unit: 10
  date_start_key: "start_date"
  date_end_key: "end_date"
  date_format: "%Y-%m-%d"
```

**crawler.py structure**:
```python
from src.core import BaseCrawler
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
import yaml
import requests
from pathlib import Path

class TemplateCrawler(BaseCrawler):
    def __init__(self, config: Optional[Dict] = None):
        if config is None:
            # Load from config.yaml
            config_path = Path(__file__).parent / "config.yaml"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

        self.config = config
        self.site_config = config['site']
        self.selectors = config['selectors']
        self.params_config = config['params']

    def fetch_page(self, url: str, params: Dict[str, Any]) -> Optional[BeautifulSoup]:
        # Implementation using self.config
        pass

    def parse_list(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        # Implementation using self.selectors
        pass

    def parse_detail(self, soup: BeautifulSoup, item: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation
        pass

    def build_params(self, page: int, start_date=None, end_date=None) -> Dict[str, Any]:
        # Implementation using self.params_config
        pass
```

### T005: Migrate ForestKorea to Plugin (Priority P0)
**Estimated**: 6 hours
**Dependencies**: T004
**Output**: `src/plugins/forest_korea/`

**Migration checklist**:
1. Copy template structure to `src/plugins/forest_korea/`
2. Extract all hardcoded values from `main.py` → `config.yaml`:
   - Base URL: `https://www.forest.go.kr`
   - Board params: `mn=NKFS_04_01_04`, `bbsId=BBSMSTR_1033`
   - Selectors: Table structure, cell positions
3. Migrate parsing logic from `main.py` → `crawler.py`:
   - `parse_list()`: Lines 130-200 of current `main.py`
   - Date parsing with regex: `r'(\d{4}[-.\s]\d{1,2}[-.\s]\d{1,2})'`
4. Test that plugin loads via factory:
   ```python
   from src.core import ParserFactory
   factory = ParserFactory()
   crawler = factory.create_crawler('forest_korea')
   ```

---

## 📚 Reference Files

### Your Context Guide
- **`.llm/contexts/gemini_context.md`** - Your detailed instructions
  - Code style requirements
  - Configuration-driven development
  - HTML parsing best practices
  - Testing procedures

### Core Abstractions
- **`src/core/base_crawler.py`** - The interface you must implement
  - See docstrings for method signatures
  - See `__main__` section for example usage
- **`src/core/parser_factory.py`** - How plugins are loaded
  - Plugin discovery via directory scanning
  - Dynamic import mechanism

### Existing Code to Migrate
- **`main.py`** - Current ForestKorea crawler
  - Lines 27-50: Constructor with date handling
  - Lines 70-100: HTTP request logic
  - Lines 130-200: List parsing (dates concatenated with view counts!)
  - Lines 240-280: Detail parsing
  - Lines 148-164: Critical regex for date extraction

### Project Architecture
- **`ARCHITECTURE.md`** - Full system design
- **`LLM_COLLABORATION.md`** - Multi-LLM workflow
- **`CURRENT_STATUS.md`** - Current progress tracker

---

## 🚨 Critical Implementation Notes

### Date Parsing Bug (MUST HANDLE)
The ForestKorea site has a quirk where dates are concatenated with view counts:
```
"2021-02-242937"  →  date: "2021-02-24", views: "2937"
```

**Solution** (from `main.py:155-160`):
```python
import re
date_match = re.search(r'(\d{4}[-.\s]\d{1,2}[-.\s]\d{1,2})', date_str)
if date_match:
    clean_date_str = date_match.group(1)
    post_date = date_parser.parse(clean_date_str)
```

### Server-Side Date Filtering
The site supports native date filtering via URL params:
- `ntcStartDt=2025-01-01`
- `ntcEndDt=2025-10-05`

This MUST be included in `build_params()` to avoid crawling thousands of irrelevant pages.

### Module Hot-Reload
If you test with Streamlit, note that `app.py:16-21` has hot-reload logic:
```python
import sys
import importlib
if 'main' in sys.modules:
    importlib.reload(sys.modules['main'])
```

You'll need to update this to reload plugins instead.

---

## 🔄 File Ownership & Locking

### You Own (Primary)
- `src/plugins/*/` - All plugin code
- Plugin-specific configs and docs

### Shared (Coordinate)
- `CURRENT_STATUS.md` - Update when starting/completing tasks
- `.llm/task_assignments.yaml` - Update task status

### Read-Only (Do Not Modify)
- `src/core/*` - Core abstractions (Claude's responsibility)
- `.llm/contexts/claude_context.md` - Not your context

---

## ✅ Acceptance Criteria

### T004 (Template Plugin)
- [ ] Directory structure matches spec above
- [ ] `config.yaml` has all required sections
- [ ] `crawler.py` inherits from BaseCrawler
- [ ] All 4 abstract methods implemented (can be stubs)
- [ ] README.md documents how to use the template
- [ ] Can be instantiated via ParserFactory

### T005 (ForestKorea Migration)
- [ ] All hardcoded values moved to `config.yaml`
- [ ] Date regex bug fix preserved
- [ ] Server-side date filtering works
- [ ] Parse same data as original `main.py`
- [ ] Can load via: `factory.create_crawler('forest_korea')`
- [ ] No import errors or crashes

---

## 🧪 Testing Procedure

### Unit Test (Minimal)
```python
# Quick smoke test
from src.core import ParserFactory

factory = ParserFactory()
crawler = factory.create_crawler('forest_korea')

# Test config loaded
assert crawler.config is not None
assert 'site' in crawler.config

# Test methods exist
assert hasattr(crawler, 'fetch_page')
assert hasattr(crawler, 'parse_list')
```

### Integration Test (Optional for now)
```python
# Test actual crawling (requires network)
from datetime import date

params = crawler.build_params(
    page=1,
    start_date=date(2025, 1, 1),
    end_date=date(2025, 10, 5)
)

soup = crawler.fetch_page(crawler.config['site']['board_url'], params)
items = crawler.parse_list(soup)

assert len(items) > 0
assert 'title' in items[0]
assert 'post_date' in items[0]
```

---

## 📞 Communication Protocol

### When You Start
1. Create file lock: `.llm/locks/gemini_T004.lock`
2. Update `CURRENT_STATUS.md`:
   ```markdown
   ### [2025-10-05 XX:XX] Gemini CLI
   - Status: 🔄 Started
   - Task: T004 (Plugin Template)
   - Files: Working on src/plugins/template/
   ```

### If Blocked
1. Add blocker to `CURRENT_STATUS.md` → "Blockers & Issues"
2. Tag issue with `@claude` if it's a core issue
3. Continue with T005 if T004 is blocked (T005 has T004 dependency but can start with basic structure)

### When Complete
1. Remove lock file
2. Update `CURRENT_STATUS.md`:
   ```markdown
   - Status: ✅ Completed
   - Outputs: src/plugins/template/, src/plugins/forest_korea/
   - Next: Ready for Codex to write tests (T011-T012)
   ```
3. Update `.llm/task_assignments.yaml`:
   ```yaml
   status: completed
   actual_hours: X
   completed: "2025-10-05TXX:XX:00+09:00"
   ```
4. Create handoff file: `.llm/HANDOFF_TO_CODEX.md` (optional, or just update CURRENT_STATUS)

---

## 💡 Tips & Best Practices

### Configuration-Driven Development
- **Never hardcode** site-specific values in Python
- **Always use** `self.config`, `self.selectors`, `self.params_config`
- **Make it easy** to add new sites by just editing YAML

### HTML Parsing
- **Use CSS selectors** for clarity: `soup.select('table.board-list tbody tr')`
- **Handle missing elements** gracefully: `elem.get_text(strip=True) if elem else None`
- **Test with real HTML** from the site (save a sample page as `test.html`)

### Error Handling
- **Catch specific exceptions**: `ConnectionError`, `Timeout`, `HTTPError`
- **Return None** for fetch failures (let caller handle)
- **Log warnings** for parse failures (partial data is OK)

### Code Style (from gemini_context.md)
- Type hints on all methods
- Docstrings in Google format
- F-strings for formatting
- Pathlib for file operations

---

## 🎯 Success Metrics

After you complete T004 + T005, we should have:
1. **2 working plugins**: template + forest_korea
2. **Config-driven**: All site logic in YAML
3. **Factory-loadable**: `factory.create_crawler('forest_korea')` works
4. **Same output**: ForestKorea plugin returns same data as original `main.py`
5. **Ready for testing**: Codex can write comprehensive tests

---

## 🚀 Next Steps (After Your Tasks)

Once T004 + T005 are done:
1. **Codex** will write tests (T011-T012)
2. **Claude** will build plugin loader UI (T006, T020)
3. **You** can add more plugins (T030: Naver Cafe, T031: 나라장터)

---

## ❓ Questions?

If anything is unclear:
1. Check **`ARCHITECTURE.md`** for system design
2. Check **`.llm/contexts/gemini_context.md`** for your detailed guide
3. Add question to `CURRENT_STATUS.md` → "Communication Log"
4. Tag with `@claude` if it's about core abstractions

---

**Good luck! The core is solid, now let's build the plugins! 🚀**

---

## 📎 Quick Reference

### File Paths
- Template: `src/plugins/template/`
- ForestKorea: `src/plugins/forest_korea/`
- Core: `src/core/base_crawler.py`, `src/core/parser_factory.py`
- Existing: `main.py` (to be migrated)

### Key Imports
```python
from src.core import BaseCrawler, ParserFactory
from bs4 import BeautifulSoup
import yaml
import requests
from datetime import date, datetime
from pathlib import Path
```

### Factory Usage
```python
factory = ParserFactory()
plugins = factory.list_available_plugins()  # ['template', 'forest_korea']
crawler = factory.create_crawler('forest_korea')
config = factory.get_plugin_config('forest_korea')
```

### Plugin Discovery
ParserFactory looks for:
1. Directories under `src/plugins/`
2. With `__init__.py` present
3. With `crawler.py` containing a BaseCrawler subclass

---

**Status**: 🟢 All dependencies met, ready to start!
