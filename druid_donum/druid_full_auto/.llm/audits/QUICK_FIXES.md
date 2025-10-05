# Quick Fixes - Code Audit 2025-10-05

빠른 복사-붙여넣기 수정사항 모음

---

## 🚀 Priority 1 (Immediate)

### Fix 0: Harden plugin identifier handling (`parser_factory.py`)

**Status**: ✅ Completed by Codex (2025-10-05)

**Details**:
- Added `_validate_site_name()` guard to reject empty or unsafe plugin names.
- Reused validation in `create_crawler()`, `get_plugin_config()`, and metadata helpers to prevent module traversal or arbitrary imports.
- Wrapped non-module import errors as `CrawlerNotFoundError` for clearer diagnostics.

Relevant code: `src/core/parser_factory.py:71`, `src/core/parser_factory.py:100-111`, `src/core/parser_factory.py:175-199`, `src/core/parser_factory.py:232-241`

---

### Fix 1: Python 3.7+ Compatibility in `parser_factory.py:131`

**Status**: ✅ Completed by Codex (2025-10-05)

**Current** (Python 3.9+):
```python
def list_available_plugins(self) -> list[str]:
```

**Fixed** (Python 3.7+):
```python
from typing import List

def list_available_plugins(self) -> List[str]:
```

**Location**: `src/core/parser_factory.py:131`
**Owner**: Claude
**Estimated Time**: 1 min

---

### Fix 2: Explicit YAML Error Handling in `parser_factory.py:175`

**Status**: ✅ Completed by Codex (2025-10-05)

**Current**:
```python
with open(config_path, 'r', encoding='utf-8') as f:
    return yaml.safe_load(f)
```

**Fixed**:
```python
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
except yaml.YAMLError as e:
    raise CrawlerNotFoundError(
        f"Invalid YAML in {site_name}/config.yaml: {e}"
    )
except OSError as e:
    raise CrawlerNotFoundError(
        f"Cannot read config for {site_name}: {e}"
    )

if config is None:
    return None

if not isinstance(config, dict):
    raise CrawlerNotFoundError(
        f"Config for plugin '{site_name}' must be a mapping, got {type(config).__name__}"
    )

return config
```

**Location**: `src/core/parser_factory.py:175-176`
**Owner**: Claude
**Estimated Time**: 2 min

---

## 🔧 Priority 2 (This Week)

### Fix 3: Add Config Validation with Pydantic

**Add to `parser_factory.py`**:

```python
from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Any

class PluginConfigSchema(BaseModel):
    """Schema for plugin config.yaml validation."""

    plugin: Dict[str, Any] = Field(..., description="Plugin metadata")
    site: Dict[str, Any] = Field(..., description="Site-specific URLs and settings")
    selectors: Dict[str, Any] = Field(..., description="CSS/XPath selectors")
    params: Dict[str, Any] = Field(..., description="URL parameter configuration")

    class Config:
        extra = "allow"  # Allow additional fields

def get_plugin_config(self, site_name: str) -> Optional[Dict[str, Any]]:
    """Load and validate config.yaml for a specific plugin."""
    config_path = self.plugins_dir / site_name / "config.yaml"

    if not config_path.exists():
        return None

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            raw_config = yaml.safe_load(f)

        # Validate against schema
        validated = PluginConfigSchema(**raw_config)
        return validated.dict()

    except yaml.YAMLError as e:
        raise CrawlerNotFoundError(
            f"Invalid YAML in {site_name}/config.yaml: {e}"
        )
    except ValidationError as e:
        raise CrawlerNotFoundError(
            f"Config validation failed for {site_name}:\n{e}"
        )
    except OSError as e:
        raise CrawlerNotFoundError(
            f"Cannot read config for {site_name}: {e}"
        )
```

**Owner**: Claude
**Task**: T006
**Estimated Time**: 15 min

---

### Fix 4: Add Version Compatibility Check

**Add to `parser_factory.py`**:

```python
from packaging import version as pkg_version

CORE_VERSION = "2.0.0"  # Should come from __version__.py

def _validate_plugin_version(self, config: Dict[str, Any], site_name: str) -> None:
    """Validate plugin is compatible with current core version."""

    plugin_meta = config.get('plugin', {})
    required_version = plugin_meta.get('requires_core_version', '*')

    if required_version == '*':
        return  # No restriction

    # Parse requirement (e.g., ">=2.0.0,<3.0.0")
    try:
        # Simple version check (can be enhanced with packaging.specifiers)
        min_ver, max_ver = None, None

        if '>=' in required_version:
            min_ver = required_version.split('>=')[1].split(',')[0].strip()
        if '<' in required_version:
            max_ver = required_version.split('<')[1].strip()

        current = pkg_version.parse(CORE_VERSION)

        if min_ver and current < pkg_version.parse(min_ver):
            raise CrawlerNotFoundError(
                f"Plugin '{site_name}' requires core >={min_ver}, "
                f"but {CORE_VERSION} is installed"
            )

        if max_ver and current >= pkg_version.parse(max_ver):
            raise CrawlerNotFoundError(
                f"Plugin '{site_name}' requires core <{max_ver}, "
                f"but {CORE_VERSION} is installed"
            )

    except Exception as e:
        # Log warning but don't block
        print(f"Warning: Could not validate version for {site_name}: {e}")

# Update _load_crawler_class() to call this:
def _load_crawler_class(self, site_name: str) -> type:
    # ... existing code ...

    # After loading config, validate version
    config = self.get_plugin_config(site_name)
    if config:
        self._validate_plugin_version(config, site_name)

    # ... rest of method ...
```

**Owner**: Claude
**Task**: T006
**Estimated Time**: 20 min

---

## 📝 Priority 3 (Documentation)

### Fix 5: Add Security Best Practices to Plugin Template

**Create `src/plugins/template/SECURITY.md`**:

```markdown
# Security Guidelines for Plugin Development

## 1. Always Use HTTPS
```python
# ✅ Good
BASE_URL = "https://example.com"

# ❌ Bad
BASE_URL = "http://example.com"  # Vulnerable to MITM
```

## 2. Set Request Timeouts
```python
# ✅ Good
response = requests.get(url, timeout=10)

# ❌ Bad
response = requests.get(url)  # Can hang forever
```

## 3. Verify SSL Certificates
```python
# ✅ Good
response = requests.get(url, verify=True)

# ❌ Bad
response = requests.get(url, verify=False)  # MITM vulnerability
```

## 4. Sanitize User Inputs
```python
# ✅ Good
safe_date = date.fromisoformat(user_input)

# ❌ Bad
query = f"SELECT * FROM posts WHERE date = '{user_input}'"  # SQL injection
```

## 5. Respect robots.txt
```python
from urllib.robotparser import RobotFileParser

rp = RobotFileParser()
rp.set_url("https://example.com/robots.txt")
rp.read()

if rp.can_fetch("*", url):
    # OK to crawl
else:
    # Respect site's wishes
```

## 6. Rate Limiting
```python
import time

# Add delays between requests
time.sleep(1.0)  # Minimum 1 second between requests

# Use exponential backoff on errors
for attempt in range(max_retries):
    try:
        response = fetch_page(url)
        break
    except Exception:
        time.sleep(2 ** attempt)  # 1s, 2s, 4s, 8s...
```

## 7. Error Messages
```python
# ✅ Good
except Exception as e:
    logger.error(f"Failed to parse page: generic error")  # Don't leak details

# ❌ Bad
except Exception as e:
    logger.error(f"Failed: {e} at {url} with params {params}")  # Leaks too much
```

## 8. No Secrets in Code
```python
# ✅ Good
import os
API_KEY = os.environ.get('API_KEY')

# ❌ Bad
API_KEY = "sk_live_abc123..."  # Committed to git!
```
```

**Owner**: Gemini
**Task**: T004 (template creation)
**Estimated Time**: 10 min

---

## 🔍 Code Review Checklist for LLMs

Use this checklist when reviewing plugin code:

```markdown
## Security Review
- [ ] All URLs use HTTPS
- [ ] All requests have timeouts
- [ ] SSL verification enabled
- [ ] No hardcoded secrets
- [ ] User inputs are validated
- [ ] Error messages don't leak sensitive data

## Quality Review
- [ ] Type hints on all methods
- [ ] Docstrings in Google format
- [ ] No hardcoded values (use config.yaml)
- [ ] Proper error handling (specific exceptions)
- [ ] Logging at appropriate levels
- [ ] No code duplication

## Performance Review
- [ ] Rate limiting implemented
- [ ] No infinite loops
- [ ] Memory usage bounded
- [ ] Large datasets handled incrementally

## Testing Review
- [ ] Unit tests for all methods
- [ ] Edge cases covered
- [ ] Mock HTTP requests (use VCR.py)
- [ ] Test with malformed inputs
```

---

## 📋 Gemini-Specific Fixes for T005

### Fix 6: Preserve Date Regex from `main.py`

**Critical**: When migrating ForestKorea, preserve this regex fix:

**From `main.py:155-160`**:
```python
import re

# Date strings like "2021-02-242937" (date + view count)
date_match = re.search(r'(\d{4}[-.\s]\d{1,2}[-.\s]\d{1,2})', date_str)
if date_match:
    clean_date_str = date_match.group(1)
    post_date = date_parser.parse(clean_date_str)
else:
    # Fallback to direct parsing
    post_date = date_parser.parse(date_str)
```

**Location in Plugin**: `src/plugins/forest_korea/crawler.py` in `parse_list()` method

---

### Fix 7: Server-Side Date Filtering

**Critical**: Include date parameters in `build_params()`:

```python
def build_params(
    self,
    page: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict[str, Any]:
    params = {
        'mn': 'NKFS_04_01_04',
        'bbsId': 'BBSMSTR_1033',
        'pageIndex': page,
        'pageUnit': 10
    }

    # CRITICAL: Add server-side date filtering
    if start_date:
        params['ntcStartDt'] = start_date.strftime('%Y-%m-%d')
    if end_date:
        params['ntcEndDt'] = end_date.strftime('%Y-%m-%d')

    return params
```

**Impact**: Without this, crawler will fetch thousands of irrelevant pages.

---

## 🎯 Copy-Paste Templates

### Template: Add New Issue to Audit Log

```markdown
### [SEVERITY] Issue Title

**File**: `path/to/file.py:LINE`
**Category**: Security / Performance / Quality / Documentation
**Severity**: Critical / High / Medium / Low
**Found By**: [LLM Name]
**Date**: YYYY-MM-DD

**Description**:
[What is wrong?]

**Impact**:
[What could happen?]

**Recommendation**:
```python
# Before
bad_code()

# After
good_code()
```

**Assigned To**: [Owner]
**Priority**: P0/P1/P2/P3
**Estimated Time**: Xmin/hrs
```

---

### Template: Quick Fix Commit Message

```bash
git commit -m "[Fix] Issue #X: Short description

- Changed: specific file and function
- Why: reason for change
- Impact: none / minor / major
- Tested: how you verified

Refs: .llm/audits/AUDIT_2025-10-05.md#finding-X

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 📞 Usage Instructions

### For Claude
1. Apply Fix 1, 2 immediately (total: 3 min)
2. Implement Fix 3, 4 during T006 (total: 35 min)
3. Update this file if new fixes identified

### For Gemini
1. **MUST** apply Fix 6, 7 during T005 (critical for data quality)
2. Reference Fix 5 when creating T004 template
3. Use Code Review Checklist for self-review

### For Codex
1. Use Code Review Checklist when writing tests
2. Ensure tests cover edge cases from fixes
3. Add regression tests for Fixed bugs

---

**Last Updated**: 2025-10-05 18:50 KST
**Maintainer**: Claude Code
**Next Review**: After T005 completion
