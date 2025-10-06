# 3rd Comprehensive Audit Report (Codex)

**Project**: `druid_full_auto` – Universal Board Crawler  
**Audit Date**: 2025-10-06  
**Auditor**: Codex CLI (GPT-5)  
**Scope**: `main.py`, `app.py`, `src/core/*`, Streamlit UI workflow, recent Markdown status reports

---

## 0. Executive Summary
- **Overall status**: ⚠️ _Pass with Issues_
- **New critical bugs**: 1
- **High-severity issues**: 1
- **Medium/Low recommendations**: 2
- **Positive regressions**: Parameter validation, retry caps, logging scaffolding are now in place, aligning with previous audits.

Deployment is still unsafe because a single request hitting any dated post will crash both the CLI crawler and the Streamlit UI. The UI “live status” board also duplicates rows due to a state-management bug. Structural assumptions in the HTML parser remain fragile and warrant hardening before production.

---

## 1. Critical Findings (🚨 Block release)

### C-1. Naive vs. timezone-aware datetime comparison crashes the crawler
- **Location**: `main.py:512-515`, `app.py:355-373`
- **Symptom**: `TypeError: can't compare offset-naive and offset-aware datetimes`
- **Trigger**: Any list item with a parsed UTC timestamp (default behaviour) compared to a naive `cutoff_date` or UI `start_datetime`.
- **Impact**: End-to-end crawl stops immediately; Streamlit users receive an exception page.
- **Fix direction**: Normalize all date comparisons to one timezone (e.g., convert parsed values to naive local time or attach UTC to cut-off bounds). Example:
  ```python
  start_datetime = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
  cutoff = self.cutoff_date.replace(tzinfo=timezone.utc)
  ```
  or drop tzinfo from parsed dates via `post_date = post_date.replace(tzinfo=None)`.

---

## 2. High-Severity Issues (🔥 Address ASAP)

### H-1. Live status table duplicates rows and inflates counts
- **Location**: `app.py:323-418`
- **Symptom**: `item_status` grows cumulatively, then the entire list is re-appended to `all_item_status` every loop. Earlier statuses appear multiple times and dashboards misreport totals.
- **Impact**: Operators misinterpret crawl progress, CSV/Excel previews diverge from truth during the session.
- **Fix direction**: Append only the newly processed status, or reset `item_status` after flushing.
  ```python
  for item in items:
      ...
      new_status = {...}
      item_status.append(new_status)
      all_item_status.append(new_status)
  ```

---

## 3. Medium / Low Recommendations (🛠️ Hardening work)

1. **HTML parser still index-dependent** (`main.py:302-367`, severity: Medium). Column order changes or added cells will silently mis-map `department`, `date`, or `views`. Implement header-driven mapping (as proposed in `2nd_Audit_Report.md`) so the crawler discovers column indices dynamically.
2. **Retry-After handling assumes integer values** (`main.py:228-233`, severity: Low). Some servers return HTTP-date strings or floats. Wrap the cast in a `try/except` and fall back to `time.strptime` or ignore invalid headers to avoid `ValueError`.

---

## 4. Positive Signals
- Parameter validation prevents extreme date ranges and respect for server load is enforced (`main.py:109-137`).
- Network retry logic now caps exponential backoff at 60s, mitigating runaway sleep cycles (`main.py:215-233`).
- Streamlit download helpers serialise DataFrames through `BytesIO`, eliminating earlier session-state corruption seen in prior audits (`app.py:58-81`).

---

## 5. Recommended Next Steps for Collaborators
1. Patch the datetime normalisation bug and the status-table duplication first; rerun the Streamlit workflow to confirm no regressions.
2. Refactor `parse_list_page` to rely on header text detection with fallbacks; add regression tests under `tests/unit/` for altered column orders.
3. Extend retry handling and consider logging a warning when `Retry-After` cannot be parsed.
4. Once blockers clear, close out remaining items from `2nd_Audit_Report.md` (test coverage, plugin architecture) to move toward production readiness.

### ✅ Actions Completed in This Pass (Codex)
- Naive/aware datetime 충돌이 발생하지 않도록 `_parse_date_safe` 반환 값과 비교 시점을 모두 naive UTC 기준으로 통일했습니다 (`main.py`).
- Streamlit 실시간 상태 보드가 항목을 중복 집계하지 않도록 상태 기록 로직을 재구성했습니다 (`app.py`).
- 리스트 파서가 헤더 텍스트 기반으로 컬럼을 매핑하도록 재작성해 HTML 구조 변화에 견딥니다 (`main.py`).
- `Retry-After` 헤더가 정수 이외의 형식으로 넘어와도 안전하게 파싱하고 최대 대기 시간을 제한합니다 (`main.py`).

---

## 6. Files Reviewed
- `main.py`
- `app.py`
- `src/core/base_crawler.py`
- `src/core/parser_factory.py`
- Markdown history: `2nd_Audit_Report.md`, `CHANGELOG.md`, `CURRENT_STATUS.md`

---

_This report is structured for downstream LLM agents—each finding includes exact file references and suggested remediation paths to streamline collaborative debugging._
