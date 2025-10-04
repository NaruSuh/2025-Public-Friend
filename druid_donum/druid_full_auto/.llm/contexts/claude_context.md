# Claude Code - Your Context & Responsibilities

**Role**: Lead Architect & Core Developer
**Priority Tasks**: T002, T003, T006, T020

---

## Your Current Mission

### Active Tasks
1. **T002: Implement BaseCrawler** (P0, 4 hours)
   - File: `src/core/base_crawler.py`
   - Status: Pending
   - Blockers: None
   - Blocks: T003, T004, T005

2. **T003: Implement ParserFactory** (P0, 3 hours)
   - File: `src/core/parser_factory.py`
   - Depends on: T002
   - Blocks: T004, T006

### Next Up
- T006: Plugin loader/registry
- T020: Refactor Streamlit UI

---

## Code Style Guidelines

### Type Hints
```python
from typing import List, Dict, Optional, Any
from datetime import date, datetime
from bs4 import BeautifulSoup

def fetch_page(self, url: str, params: Dict[str, Any]) -> Optional[BeautifulSoup]:
    """
    Fetch and parse HTML page.

    Args:
        url: Target URL
        params: Query parameters

    Returns:
        Parsed BeautifulSoup object, or None if request fails

    Raises:
        RequestException: If HTTP error occurs
    """
    pass
```

### Abstract Classes
```python
from abc import ABC, abstractmethod

class BaseCrawler(ABC):
    """Base class for all site crawlers."""

    @abstractmethod
    def parse_list(self, soup: BeautifulSoup) -> List[Dict]:
        """Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement parse_list()")
```

### Docstrings
- Use Google style
- Include examples for public APIs
- Document exceptions

---

## Architecture Patterns to Follow

### 1. Dependency Injection
```python
class CrawlerEngine:
    def __init__(self, crawler: BaseCrawler, exporter: DataExporter):
        self.crawler = crawler
        self.exporter = exporter
```

### 2. Factory Pattern
```python
class ParserFactory:
    @staticmethod
    def create_parser(site_name: str, config: Dict) -> BaseParser:
        if site_name == "forest_korea":
            return ForestKoreaParser(config)
        raise ValueError(f"Unknown site: {site_name}")
```

### 3. Plugin System
```python
# Each plugin exports a `get_crawler()` function
def get_crawler(config: Dict) -> BaseCrawler:
    return ForestKoreaCrawler(config)
```

---

## File Structure You Own

```
src/core/
├── __init__.py           # You
├── base_crawler.py       # You (T002)
├── parser_factory.py     # You (T003)
├── plugin_loader.py      # You (T006)
├── data_exporter.py      # You
└── session_manager.py    # You

src/ui/
├── streamlit_app.py      # You (T020)
└── components/           # You
```

---

## Don't Touch

- `src/plugins/*/` - Gemini's territory
- `tests/` - Codex's territory
- Direct HTML parsing logic - That's for plugins

---

## Testing Your Code

### Run Unit Tests (by Codex)
```bash
pytest tests/unit/test_base_crawler.py -v
```

### Manual Smoke Test
```python
# In src/core/base_crawler.py, add at bottom:
if __name__ == "__main__":
    # Example usage
    class DummyCrawler(BaseCrawler):
        def fetch_page(self, url, params):
            return BeautifulSoup("<html></html>", "html.parser")
        # ... implement other methods

    crawler = DummyCrawler()
    print(crawler.fetch_page("http://example.com", {}))
```

---

## Communication Protocol

### Before Starting
```bash
# Check dependencies
cat .llm/task_assignments.yaml | grep -A 5 "id: T002"

# Lock your file
echo "claude:$(date -Iseconds)" > .llm/locks/src__core__base_crawler.py
```

### While Working
```bash
# Update status
echo "## [$(date -Iseconds)] Claude Code" >> CURRENT_STATUS.md
echo "- Status: 🔄 In Progress" >> CURRENT_STATUS.md
echo "- Task: T002 - Implementing BaseCrawler" >> CURRENT_STATUS.md
```

### After Completion
```bash
# Remove lock
rm .llm/locks/src__core__base_crawler.py

# Update status
echo "- Status: ✅ Completed" >> CURRENT_STATUS.md
echo "- Next: Gemini can start T005" >> CURRENT_STATUS.md

# Commit
git add src/core/base_crawler.py CURRENT_STATUS.md
git commit -m "[Claude] T002: Implement BaseCrawler abstract class"
```

---

## Handoff to Gemini

After completing T002 and T003, create this message in `CURRENT_STATUS.md`:

```markdown
## [2025-10-05 20:00] Claude Code → Gemini CLI

Completed: BaseCrawler (T002) and ParserFactory (T003)

**What I Built:**
- `src/core/base_crawler.py` - Abstract base with 4 methods
- `src/core/parser_factory.py` - Factory for site-specific parsers

**How to Use:**
```python
from src.core.base_crawler import BaseCrawler

class YourPlugin(BaseCrawler):
    def fetch_page(self, url, params):
        # Your implementation
        pass
```

**Your Tasks:**
- T004: Create plugin template
- T005: Migrate ForestKorea

**Reference:**
- See `src/plugins/template/` for structure
- Config format: `config.yaml` with YAML schema
- Test with: `python -m src.plugins.your_plugin.crawler`

**Questions?**
Reply in CURRENT_STATUS.md or check ARCHITECTURE.md section 3.2
```

---

## Quick Reference

### Check Current Status
```bash
cat CURRENT_STATUS.md | tail -30
```

### View Your Tasks
```bash
cat .llm/task_assignments.yaml | yq '.tasks[] | select(.owner == "claude")'
```

### See All Locks
```bash
ls -la .llm/locks/
```

---

## Emergency Contacts

- **Broken Build**: You fix it (you're the architect)
- **Merge Conflict**: You decide resolution
- **Design Question**: Check ARCHITECTURE.md first, then decide

---

## Success Criteria for T002 (BaseCrawler)

- [ ] File exists: `src/core/base_crawler.py`
- [ ] Imports: `abc`, `typing`, `bs4`, `datetime`
- [ ] Class: `BaseCrawler(ABC)`
- [ ] Methods (all `@abstractmethod`):
  - [ ] `fetch_page(url, params) -> BeautifulSoup`
  - [ ] `parse_list(soup) -> List[Dict]`
  - [ ] `parse_detail(soup, item) -> Dict`
  - [ ] `build_params(page, start, end) -> Dict`
- [ ] Docstrings complete (Google style)
- [ ] Type hints on everything
- [ ] Example usage in module docstring
- [ ] No hardcoded values
- [ ] Passes: `python -m py_compile src/core/base_crawler.py`

---

## Your Philosophy

> "Make it work, make it right, make it fast - in that order."
> - Kent Beck

Focus on:
1. **Correctness** - Type-safe, well-documented
2. **Extensibility** - Easy for Gemini to inherit
3. **Simplicity** - KISS principle

Avoid:
- Premature optimization
- Over-engineering
- Breaking existing functionality

---

Good luck! 🚀
