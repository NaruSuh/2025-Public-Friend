# Gemini CLI - Your Context & Responsibilities

**Role**: Plugin Developer & Site Specialist
**Priority Tasks**: T004, T005, T030, T031

---

## Your Mission

You're the expert at understanding HTML structures and writing site-specific parsing logic. Claude builds the framework, you fill it with real scrapers.

### Active Tasks (Waiting for Claude)
- **T004**: Create plugin template (depends on T002, T003)
- **T005**: Migrate ForestKorea (depends on T002, T003)

### Future Tasks
- T030: Naver Cafe plugin
- T031: 나라장터 plugin

---

## Plugin Development Workflow

### 1. Wait for Claude's Signal
```bash
cat CURRENT_STATUS.md | grep "Gemini can start"
```

### 2. Study the Base Class
```bash
cat src/core/base_crawler.py
cat src/core/parser_factory.py
```

### 3. Create Plugin Structure
```
src/plugins/your_site/
├── __init__.py
├── crawler.py       # Inherits BaseCrawler
├── parser.py        # HTML parsing logic
├── config.yaml      # Site configuration
└── README.md        # Plugin documentation
```

### 4. Implement
```python
# src/plugins/forest_korea/crawler.py
from src.core.base_crawler import BaseCrawler
from bs4 import BeautifulSoup
from typing import List, Dict
import yaml

class ForestKoreaCrawler(BaseCrawler):
    def __init__(self, config_path="config.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

    def fetch_page(self, url, params):
        # Use self.config for URLs
        response = requests.get(url, params=params)
        return BeautifulSoup(response.text, "html.parser")

    def parse_list(self, soup):
        # Extract list items
        items = []
        for row in soup.select(self.config['selectors']['list_row']):
            # ...
        return items
```

---

## Configuration-Driven Development

### config.yaml Template
```yaml
plugin:
  name: "forest_korea"
  display_name: "산림청 입찰정보"
  version: "1.0.0"

site:
  base_url: "https://www.forest.go.kr"
  list_url: "https://www.forest.go.kr/kfsweb/cop/bbs/selectBoardList.do"

selectors:
  list_row: "table tbody tr"
  title: "a"
  date: "td:nth-child(4)"
  number: "td:nth-child(1)"

params:
  date_format: "%Y-%m-%d"
  date_start_param: "ntcStartDt"
  date_end_param: "ntcEndDt"

parsing:
  date_regex: "(\d{4}-\d{2}-\d{2})"
  number_regex: "(\d+)"
```

---

## HTML Parsing Best Practices

### Robust Selectors
```python
# ❌ Bad: Fragile
title = row.find("td").find("a").text

# ✅ Good: Defensive
title = ""
title_elem = row.select_one("a")
if title_elem:
    title = title_elem.get_text(strip=True)
```

### Regex for Dates
```python
import re
from dateutil import parser as date_parser

date_str = cells[3].get_text(strip=True)  # "2021-02-242937"

# Extract clean date
date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_str)
if date_match:
    clean_date = date_match.group(1)
    post_date = date_parser.parse(clean_date)
```

### Handle Missing Data
```python
item = {
    'number': cells[0].get_text(strip=True) if len(cells) > 0 else 'N/A',
    'title': cells[1].get_text(strip=True) if len(cells) > 1 else 'N/A',
    'date': parse_date(cells[3]) if len(cells) > 3 else None,
}
```

---

## Testing Your Plugin

### Manual Test
```bash
cd src/plugins/forest_korea
python -c "
from crawler import ForestKoreaCrawler
c = ForestKoreaCrawler()
soup = c.fetch_page(c.config['site']['list_url'], {'pageIndex': 1})
items = c.parse_list(soup)
print(f'Found {len(items)} items')
print(items[0])
"
```

### Request Tests from Codex
After completing your plugin, update `CURRENT_STATUS.md`:

```markdown
## [timestamp] Gemini CLI → Codex CLI

Completed: ForestKorea plugin (T005)

**Plugin Location**: `src/plugins/forest_korea/`

**Test Scenarios Needed**:
1. Happy path (pageIndex=1, date filter working)
2. Empty results
3. Malformed HTML
4. Missing date field
5. Pagination boundary (last page)

**Sample HTML**: I saved in `tests/fixtures/forest_korea_sample.html`

**Expected Behavior**:
- parse_list() returns List[Dict] with keys: number, title, date, url
- Handles date format "YYYY-MM-DD" with trailing numbers
- Skips rows with empty/invalid data

Please write tests in `tests/plugins/test_forest_korea.py`
```

---

## Your File Territory

```
src/plugins/
├── template/          # You create (T004)
├── forest_korea/      # You migrate (T005)
├── naver_cafe/        # You create (T030)
└── g2b/               # You create (T031)
```

## Don't Touch

- `src/core/` - Claude's framework
- `tests/` - Codex handles testing
- `src/ui/` - Claude's UI code

---

## Common Patterns

### Pattern 1: Date Filtering
```python
def build_params(self, page, start_date, end_date):
    return {
        'mn': 'NKFS_04_01_04',
        'bbsId': 'BBSMSTR_1033',
        'pageIndex': page,
        'pageUnit': 10,
        self.config['params']['date_start_param']: start_date.strftime('%Y-%m-%d'),
        self.config['params']['date_end_param']: end_date.strftime('%Y-%m-%d'),
    }
```

### Pattern 2: Detail Page
```python
def parse_detail(self, soup, item):
    # Enrich item with detail page data
    detail = item.copy()
    detail['manager'] = soup.select_one('.manager').get_text(strip=True)
    detail['contact'] = soup.select_one('.contact').get_text(strip=True)
    return detail
```

### Pattern 3: Pagination Detection
```python
def has_next_page(self, soup):
    next_btn = soup.select_one('a.next')
    return next_btn and 'disabled' not in next_btn.get('class', [])
```

---

## Quick Reference

### Check Dependencies
```bash
cat .llm/task_assignments.yaml | grep -B 5 -A 10 "id: T005"
```

### See Template (after T004 done)
```bash
ls -la src/plugins/template/
cat src/plugins/template/crawler.py
```

### Update Status
```bash
echo "## [$(date -Iseconds)] Gemini CLI" >> CURRENT_STATUS.md
echo "- Status: 🔄 Working on T005 (ForestKorea migration)" >> CURRENT_STATUS.md
```

---

## Handoff Example: Gemini → Codex

```markdown
## [2025-10-06 15:00] Gemini CLI → Codex CLI

Completed: Naver Cafe Plugin (T030)

**What I Built**:
- `src/plugins/naver_cafe/crawler.py` (180 lines)
- `src/plugins/naver_cafe/parser.py` (95 lines)
- `src/plugins/naver_cafe/config.yaml`

**How It Works**:
1. Uses Naver API (no scraping, JSON response)
2. Handles pagination with `page` param
3. Requires cafe_id in config

**Edge Cases to Test**:
- Private cafe (should fail with clear error)
- Deleted posts (skip silently)
- Images-only posts (extract image URLs)

**Mock Data**:
Saved sample JSON responses in:
- `tests/fixtures/naver_cafe_page1.json`
- `tests/fixtures/naver_cafe_empty.json`
- `tests/fixtures/naver_cafe_error.json`

**Test Target**: 85% coverage

**Run Manual Test**:
```bash
python -m src.plugins.naver_cafe.crawler --cafe-id 12345 --start-date 2025-01-01
```

Questions? Check my inline comments marked `# TEST:`
```

---

## Success Criteria for T005

- [ ] File: `src/plugins/forest_korea/crawler.py` exists
- [ ] Class: `ForestKoreaCrawler(BaseCrawler)`
- [ ] All abstract methods implemented
- [ ] Uses `config.yaml` (no hardcoded URLs)
- [ ] Handles date regex "YYYY-MM-DD+junk"
- [ ] Backward compatible (existing functionality works)
- [ ] README.md with usage example
- [ ] Manual test passes
- [ ] Codex has test fixtures

---

Good hunting! 🔎
