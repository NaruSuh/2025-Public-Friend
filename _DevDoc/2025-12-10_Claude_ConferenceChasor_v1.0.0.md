# ConferenceChasor Code Audit Report

**Audit Date**: 2025-12-10
**Auditor**: Claude Opus 4.5
**Project Version**: 1.0.0
**Status**: Pre-Production Review

---

## Executive Summary

**Overall Assessment**: REQUIRES IMMEDIATE ATTENTION for security issues before production deployment.

ConferenceChasor is a Flask-based certificate generator for conferences and seminars with approximately 420 lines of Python code. The project demonstrates good code organization with clear module separation but has several critical security vulnerabilities and areas for improvement.

- **5 Critical Issues** (security vulnerabilities)
- **5 Major Issues** (should fix)
- **6 Minor Issues** (nice to fix)

**Total LOC**: ~420 lines (Python)
**Test Coverage**: 0%

---

## 1. Critical Issues (Must Fix)

### CRIT-001: File Upload Security Vulnerabilities
**Location**: `app.py` lines 36-57
**Severity**: CRITICAL

**Issues**:
1. **No file size limits**: Missing `MAX_CONTENT_LENGTH` configuration allows potential DoS attacks
2. **Insufficient file validation**: Only validates via HTML accept attribute (client-side)
3. **No MIME type validation**: Does not verify actual file content type
4. **Unsafe filename handling**: Uses `sheet_file.filename` directly without sanitization

**Current Code**:
```python
sheet_file = request.files.get("sheet")
if not sheet_file or not sheet_file.filename:
    raise ValueError("Google Form 응답 파일을 업로드하세요.")
sheet_path = tmpdir_path / sheet_file.filename  # UNSAFE
sheet_file.save(sheet_path)
```

**Fix**:
```python
from werkzeug.utils import secure_filename
import magic  # python-magic

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'.xlsx', '.xls', '.xlsm', '.csv'}
ALLOWED_MIME_TYPES = {
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel',
    'text/csv'
}

def validate_upload(file):
    if not file or not file.filename:
        raise ValueError("파일을 선택하세요.")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"허용되지 않는 파일 형식입니다: {ext}")

    file.seek(0)
    mime = magic.from_buffer(file.read(2048), mime=True)
    file.seek(0)
    if mime not in ALLOWED_MIME_TYPES:
        raise ValueError(f"잘못된 파일 형식입니다.")

    return secure_filename(file.filename)
```

---

### CRIT-002: CSRF Protection Missing
**Location**: `app.py`
**Severity**: CRITICAL

**Issue**: Flask application has no CSRF protection enabled. POST endpoint accepts form submissions without CSRF tokens.

**Risk**: Attackers could trick authenticated users into generating certificates with malicious data.

**Fix**:
```python
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(32))
csrf = CSRFProtect(app)
```

---

### CRIT-003: Path Traversal Vulnerability
**Location**: `certgen/generator.py` lines 118-125
**Severity**: HIGH

**Issue**: Filename generation uses user-controlled data without proper sanitization.

**Current Code**:
```python
def _build_filename(self, participant: Participant) -> str:
    pattern = self.config.output.filename_pattern
    safe_name = participant.name.replace(" ", "_")  # Only replaces spaces!
    event_name = self.config.event.title.replace(" ", "_")
    filename = pattern.format(name=safe_name, event=event_name)
```

**Risk**: Participant names containing `../` could cause files to be written outside intended directories.

**Fix**:
```python
import re
from pathlib import Path

def _build_filename(self, participant: Participant) -> str:
    def sanitize(text: str) -> str:
        text = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', text)
        text = re.sub(r'[_\s]+', '_', text)
        return text.strip('_. ')[:100]

    safe_name = sanitize(participant.name)
    event_name = sanitize(self.config.event.title)
    filename = pattern.format(name=safe_name, event=event_name)

    if not filename.lower().endswith('.pdf'):
        filename += '.pdf'

    return Path(filename).name
```

---

### CRIT-004: No Input Validation on Config Files
**Location**: `certgen/config_loader.py` lines 85-113
**Severity**: HIGH

**Issue**: YAML config files are loaded and merged without validation of types or values.

**Fix**: Use Pydantic for schema validation
```python
from pydantic import BaseModel, validator, Field

class LayoutConfig(BaseModel):
    page_orientation: str = "landscape"
    border_color: str = "#1f4b99"

    @validator('page_orientation')
    def validate_orientation(cls, v):
        if v.lower() not in ['landscape', 'portrait']:
            raise ValueError("page_orientation must be 'landscape' or 'portrait'")
        return v.lower()

    @validator('border_color')
    def validate_color(cls, v):
        if not re.match(r'^#[0-9a-fA-F]{6}$', v):
            raise ValueError(f"Invalid hex color: {v}")
        return v
```

---

### CRIT-005: Missing Flask Security Headers
**Location**: `app.py`
**Severity**: HIGH

**Issue**: No security headers configured (CSP, X-Frame-Options, X-Content-Type-Options, etc.)

**Fix**:
```python
from flask_talisman import Talisman

Talisman(app,
    content_security_policy={
        'default-src': "'self'",
        'style-src': "'self' 'unsafe-inline'"
    }
)
```

---

## 2. Major Issues (Should Fix)

### MAJ-001: Inadequate Error Handling
**Location**: Multiple files
**Issue**: Generic exception handling loses error context.

```python
# app.py line 28 - Too broad
except Exception as exc:
    LOGGER.exception("Unexpected failure while generating certificates")
    error = f"서버 처리 중 오류가 발생했습니다: {exc}"
```

**Recommendation**: Catch specific exceptions (pandas.errors.*, openpyxl.*, yaml.YAMLError)

---

### MAJ-002: Memory Management Issues
**Location**: `certgen/data_loader.py` lines 25-37
**Issue**: Entire Excel/CSV file loaded into memory at once. No streaming or chunking.

**Recommendation**: Implement chunked processing with `pd.read_excel(chunksize=...)`

---

### MAJ-003: No Rate Limiting
**Location**: `app.py`
**Issue**: Web interface has no rate limiting on certificate generation endpoint.

**Fix**:
```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=get_remote_address)

@app.route('/generate', methods=['POST'])
@limiter.limit("5 per minute")
def generate():
    ...
```

---

### MAJ-004: Insufficient Logging
**Location**: All modules
**Issues**:
1. Inconsistent logging levels
2. No request ID tracking
3. Missing security event logging

---

### MAJ-005: No Resource Cleanup Guarantees
**Location**: `web_runner.py` lines 63-77
**Issue**: File handles in zip creation aren't explicitly managed.

---

## 3. Minor Issues (Nice to Fix)

| Issue | Location | Description |
|-------|----------|-------------|
| MIN-001 | Multiple | Missing type hints on functions |
| MIN-002 | generator.py | Magic numbers and hardcoded values |
| MIN-003 | Multiple | Inconsistent string formatting |
| MIN-004 | config_loader.py | Dead/unused code (`InputConfig.locale`) |
| MIN-005 | Most files | No docstrings on classes/functions |
| MIN-006 | Various | Inconsistent naming conventions (mixed Korean/English) |

---

## 4. Code Quality Assessment

### Strengths
1. ✅ Good Module Separation: Clear separation between data loading, config, generation, and runners
2. ✅ Modern Python: Uses dataclasses, type hints (partial), and modern syntax
3. ✅ Configuration-Driven: Flexible YAML-based configuration
4. ✅ Temporary File Handling: Uses `tempfile.TemporaryDirectory()` for secure file handling

### Weaknesses
1. ❌ No Tests: Zero automated tests found
2. ❌ Mixed Concerns: Business logic mixed with presentation
3. ❌ Limited Extensibility: Hard to add new certificate layouts
4. ❌ No Validation Layer: Input validation scattered across modules

---

## 5. Security Checklist

| Security Aspect | Status | Priority |
|----------------|--------|----------|
| CSRF Protection | ❌ Missing | Critical |
| File Upload Validation | ⚠️ Partial | Critical |
| File Size Limits | ❌ Missing | Critical |
| Path Traversal Protection | ⚠️ Partial | High |
| Input Validation | ⚠️ Partial | High |
| SQL Injection | ✅ N/A | - |
| XSS Protection | ✅ Good | - |
| Security Headers | ❌ Missing | High |
| Rate Limiting | ❌ Missing | Medium |
| Secrets Management | ✅ Good | - |

---

## 6. Dependencies Audit

**Current `requirements.txt`**:
```
pandas==2.2.2
openpyxl==3.1.5
PyYAML==6.0.1
reportlab==4.1.0
Flask==3.0.3
```

**Missing Dependencies**:
| Package | Purpose |
|---------|---------|
| flask-wtf | CSRF protection |
| flask-limiter | Rate limiting |
| werkzeug | Filename sanitization (explicit) |
| python-magic | MIME type detection |
| pydantic | Data validation |
| pytest | Testing framework |
| gunicorn | Production WSGI server |

---

## 7. Recommended Fixes (Priority Order)

### Week 1 (Critical)
1. Add file upload security (size limits, MIME validation, filename sanitization) - 4 hours
2. Implement CSRF protection using Flask-WTF - 2 hours
3. Fix path traversal vulnerabilities in filename generation - 2 hours
4. Add config validation using Pydantic - 3 hours
5. Set up security headers using Flask-Talisman - 1 hour

### Week 2 (Major)
1. Add comprehensive test suite - 6 hours
2. Implement rate limiting - 2 hours
3. Standardize error handling - 4 hours
4. Add structured logging - 2 hours
5. Update requirements.txt with all dependencies - 1 hour

### Week 3-4 (Minor)
1. Add type hints to all functions - 3 hours
2. Extract magic numbers to configuration - 2 hours
3. Write documentation - 3 hours
4. Clean up dead code - 1 hour

**Total Estimated Effort**: ~36 hours

---

## 8. Files Audited

| File | Lines | Status |
|------|-------|--------|
| app.py | ~100 | FAIL - Critical security issues |
| web_runner.py | ~80 | PASS with recommendations |
| certgen/__init__.py | ~10 | PASS |
| certgen/__main__.py | ~20 | PASS |
| certgen/config_loader.py | ~115 | FAIL - Needs validation |
| certgen/data_loader.py | ~45 | PASS with recommendations |
| certgen/generator.py | ~130 | FAIL - Path traversal |
| certgen/runner.py | ~40 | PASS |

---

## 9. Risk Summary

| Area | Risk Level |
|------|------------|
| Security | HIGH |
| Reliability | MEDIUM |
| Maintainability | MEDIUM |
| Performance | LOW |

---

## 10. Conclusion

ConferenceChasor demonstrates good foundational code structure and modern Python practices. However, **it is not production-ready** in its current state due to critical security vulnerabilities in file upload handling, missing CSRF protection, and inadequate input validation.

**Risk Level**: HIGH if deployed as-is, MEDIUM-LOW after critical fixes.

The codebase is manageable at ~420 lines and well-structured for incremental improvements. With focused effort on security and testing, this can become a robust, production-grade application.

**Estimated Effort to Production-Ready**: 2-3 weeks

---

*Generated by Claude Opus 4.5 Code Audit System*
