# Multi-LLM CLI Collaboration Guide

**Purpose**: Claude Code, Gemini CLI, Codex CLI가 충돌 없이 동시 작업할 수 있는 워크플로우

---

## Quick Start for Each LLM

### 🤖 Claude Code (당신)
```bash
# 작업 시작 전 필수 체크
cat .llm/task_assignments.yaml | grep "claude"
cat docs/CURRENT_STATUS.md

# 작업 완료 후
echo "Claude: Completed core/base_crawler.py" >> docs/CURRENT_STATUS.md
git add . && git commit -m "[Claude] Implement BaseCrawler interface"
```

### 🧠 Gemini CLI
```bash
# Gemini 전용 컨텍스트 읽기
cat .llm/gemini_context.md

# 작업 시작
echo "Gemini: Working on plugins/naver_cafe/" >> docs/CURRENT_STATUS.md
```

### 🔧 Codex CLI
```bash
# 테스트 작성 타겟 확인
cat .llm/codex_context.md

# 작업
pytest tests/ --cov=src/core
```

---

## File Ownership Matrix

| 디렉토리/파일 | Primary Owner | Can Edit | Read-Only |
|---------------|---------------|----------|-----------|
| `src/core/` | Claude | - | Gemini, Codex |
| `src/plugins/*/` | Gemini | Claude (review) | Codex |
| `tests/` | Codex | Claude (integration) | Gemini |
| `docs/ARCHITECTURE.md` | Claude | - | All |
| `docs/PLUGIN_DEVELOPMENT.md` | Gemini | Claude | Codex |
| `.llm/*.md` | All | All | - |

---

## Communication Protocol

### 1. Status Broadcasting
모든 LLM은 작업 시작/종료 시 `docs/CURRENT_STATUS.md`를 업데이트합니다.

#### Format
```markdown
## [2025-10-05 14:30] Claude Code
- Status: ✅ Completed
- Task: Implemented `BaseCrawler` abstract class
- Files: `src/core/base_crawler.py`
- Next: Gemini can now implement `forest_korea` plugin
- Blockers: None

## [2025-10-05 15:00] Gemini CLI
- Status: 🔄 In Progress
- Task: Developing forest_korea plugin
- Files: `src/plugins/forest_korea/crawler.py`
- Next: Will request Codex for unit tests
- Blockers: Waiting for `ParserFactory` (Claude)
```

### 2. File Locking
작업 중인 파일은 `.llm/locks/` 에 기록:

```bash
# 작업 시작 (Claude)
echo "claude:$(date -Iseconds)" > .llm/locks/src__core__base_crawler.py

# 작업 완료
rm .llm/locks/src__core__base_crawler.py
```

### 3. Dependency Declaration
새 작업 시작 전 `task_assignments.yaml`에서 의존성 확인:

```yaml
tasks:
  - id: T001
    title: "Implement BaseCrawler"
    owner: claude
    status: completed
    outputs:
      - src/core/base_crawler.py

  - id: T002
    title: "Create forest_korea plugin"
    owner: gemini
    status: in_progress
    depends_on: [T001]
    blocks: [T005]  # Codex의 테스트 작업을 블록
```

---

## Context Files for Each LLM

### `.llm/claude_context.md`
```markdown
# Claude Code Context

## Your Responsibilities
- Core architecture design
- Abstract classes and interfaces
- Complex refactoring tasks
- Code review for other LLMs

## Current Focus
- [ ] Implement `src/core/base_crawler.py`
- [ ] Implement `src/core/parser_factory.py`
- [ ] Review Gemini's plugin implementations

## Code Style
- Use type hints everywhere
- Docstrings in Google format
- Abstract methods must raise `NotImplementedError`

## Don't Touch
- `src/plugins/` (Gemini's territory)
- `tests/` (Codex's territory)
```

### `.llm/gemini_context.md`
```markdown
# Gemini CLI Context

## Your Responsibilities
- Individual site plugin development
- HTML parsing logic
- Site-specific edge case handling

## Current Focus
- [ ] Port existing `main.py` to `plugins/forest_korea/`
- [ ] Create 2 new plugins (Naver Cafe, 나라장터)

## Plugin Template
See: `src/plugins/template/`

## Testing
Run: `python -m pytest tests/plugins/test_forest_korea.py`

## Report To
Claude for architecture questions
Codex for test failures
```

### `.llm/codex_context.md`
```markdown
# Codex CLI Context

## Your Responsibilities
- Write unit tests for all modules
- Integration tests for E2E workflows
- API documentation generation

## Current Focus
- [ ] Unit tests for `src/core/`
- [ ] Plugin tests for `src/plugins/forest_korea/`
- [ ] Generate API docs from docstrings

## Coverage Target
- Core modules: 95%+
- Plugins: 80%+
- UI: 60%+

## Tools
- pytest + pytest-cov
- sphinx-apidoc
- doctest

## Workflow
1. Claude completes a module
2. You write tests
3. Report coverage to `docs/CURRENT_STATUS.md`
```

---

## Workflow Example: Adding a New Plugin

### Step 1: Claude Creates Interface (30 min)
```bash
# Claude
git checkout -b feature/plugin-interface
# Implement src/core/base_crawler.py
git commit -m "[Claude] Add BaseCrawler interface"
git push
# Update CURRENT_STATUS.md
```

### Step 2: Gemini Implements Plugin (2 hours)
```bash
# Gemini
git pull origin feature/plugin-interface
git checkout -b feature/naver-cafe-plugin
# Implement src/plugins/naver_cafe/
cat .llm/claude_context.md  # Check if BaseCrawler is ready
git commit -m "[Gemini] Implement Naver Cafe plugin"
# Update CURRENT_STATUS.md: "Ready for tests"
```

### Step 3: Codex Writes Tests (1 hour)
```bash
# Codex
git pull origin feature/naver-cafe-plugin
# Implement tests/plugins/test_naver_cafe.py
pytest tests/plugins/test_naver_cafe.py --cov
# Report coverage to CURRENT_STATUS.md
git commit -m "[Codex] Add tests for Naver Cafe plugin (87% coverage)"
```

### Step 4: Claude Reviews & Merges (30 min)
```bash
# Claude
git checkout main
git merge feature/plugin-interface
git merge feature/naver-cafe-plugin
# Review all changes
git push origin main
```

---

## Conflict Resolution

### Merge Conflicts
1. **Prevention**: Use file ownership matrix
2. **Detection**: GitHub PR checks
3. **Resolution**: Owner LLM resolves conflicts

### Logic Conflicts
1. **Detection**: Test failures
2. **Discussion**: Via `docs/CURRENT_STATUS.md` comments
3. **Resolution**: Claude has final decision

### Example
```markdown
## [2025-10-05 16:00] Gemini CLI
- Issue: `BaseCrawler.fetch_page()` signature changed
- Impact: My plugin implementation broken
- Question: @Claude - Should I use new signature or revert?

## [2025-10-05 16:15] Claude Code
- Decision: Use new signature `fetch_page(url, params, **kwargs)`
- Reason: Supports custom headers
- Action: I'll update `PLUGIN_DEVELOPMENT.md` with example
```

---

## Sync Points

### Daily Standup (Async)
Each LLM updates `docs/CURRENT_STATUS.md` with:
- Yesterday: What was completed
- Today: What will be worked on
- Blockers: Dependencies or issues

### Weekly Review
Claude compiles:
- Completed tasks
- Code quality metrics
- Next week's assignments

---

## Tool Integration

### For Human Developer
```bash
# Check current status
./scripts/llm-status.sh

# Assign task to specific LLM
./scripts/assign-task.sh --llm gemini --task "Add Google Shopping plugin"

# Generate handoff prompt
./scripts/generate-handoff.sh --from claude --to gemini
```

### Auto-Sync Script
```bash
# .llm/sync.sh
#!/bin/bash
git pull origin main
cat docs/CURRENT_STATUS.md | tail -20
cat .llm/task_assignments.yaml | yq '.tasks[] | select(.owner == env(LLM_NAME))'
```

---

## Best Practices

### ✅ DO
- Always read `CURRENT_STATUS.md` before starting
- Lock files you're editing
- Write detailed commit messages with `[LLM_NAME]` prefix
- Update documentation as you code
- Run tests before committing

### ❌ DON'T
- Edit files outside your ownership
- Commit without testing
- Skip status updates
- Change interfaces without discussion
- Assume other LLMs know your changes

---

## Emergency Procedures

### Broken Build
1. Last committer reverts
2. Update `CURRENT_STATUS.md` with incident report
3. Fix in separate branch

### Lost Context
1. Read `docs/ARCHITECTURE.md`
2. Read `docs/CURRENT_STATUS.md`
3. Check `.llm/{your_llm}_context.md`
4. Review recent commits: `git log --oneline -20`

---

## Success Metrics

- **Zero merge conflicts** in 80% of PRs
- **< 30 min** average time for handoffs
- **> 90%** test coverage across all modules
- **< 1 day** turnaround for new plugin development

---

## Handoff Prompt Templates

### Claude → Gemini
```
I've completed the BaseCrawler interface in `src/core/base_crawler.py`.

Context:
- Abstract methods: fetch_page(), parse_list(), parse_detail()
- Type hints fully annotated
- See docstrings for expected return types

Your Task:
- Implement ForestKorea plugin using this interface
- Reference: `src/plugins/template/` for structure
- Config: Define in `config.yaml` per PLUGIN_DEVELOPMENT.md

Files You Need:
- src/plugins/forest_korea/crawler.py
- src/plugins/forest_korea/parser.py
- src/plugins/forest_korea/config.yaml

Test:
- Manual: `python -m src.plugins.forest_korea.crawler`
- Ask Codex for unit tests after completion

Questions: Check docs/ARCHITECTURE.md or ask in CURRENT_STATUS.md
```

### Gemini → Codex
```
Completed Naver Cafe plugin implementation.

Files Created:
- src/plugins/naver_cafe/crawler.py (150 lines)
- src/plugins/naver_cafe/parser.py (80 lines)
- src/plugins/naver_cafe/config.yaml

Your Task:
- Write unit tests in tests/plugins/test_naver_cafe.py
- Target coverage: 80%+
- Test scenarios: See inline comments marked `# TEST:`

Mock Data:
- Sample HTML responses in tests/fixtures/naver_cafe_*.html
- Use pytest-vcr for HTTP recording

Run:
`pytest tests/plugins/test_naver_cafe.py -v --cov=src.plugins.naver_cafe`

Edge Cases to Test:
1. Missing date field
2. Pagination end detection
3. Login-required boards (should fail gracefully)
```

### Codex → Claude
```
Test suite completed for core modules.

Results:
- src/core/base_crawler.py: 96% coverage
- src/core/parser_factory.py: 100% coverage
- src/core/data_exporter.py: 89% coverage

Failed Tests: None
Warnings: 3 (deprecation warnings from BeautifulSoup)

Suggested Improvements:
1. Add input validation in BaseCrawler.fetch_page()
2. ParserFactory.get_parser() should raise custom exception, not ValueError

Documentation:
- Generated API docs in docs/api/
- Run `make docs` to view locally

Next: Ready for integration tests
```

---

## Appendix: Task Assignment Template

```yaml
# .llm/task_assignments.yaml
version: "1.0"
last_updated: "2025-10-05T14:00:00Z"

tasks:
  - id: T001
    title: "Design and implement BaseCrawler interface"
    owner: claude
    priority: P0
    status: completed
    estimated_hours: 4
    actual_hours: 3.5
    outputs:
      - src/core/base_crawler.py
      - docs/API_REFERENCE.md (section)
    dependencies: []
    blocks: [T002, T003]

  - id: T002
    title: "Implement ForestKorea plugin"
    owner: gemini
    priority: P0
    status: in_progress
    estimated_hours: 6
    progress: 70%
    outputs:
      - src/plugins/forest_korea/crawler.py
      - src/plugins/forest_korea/parser.py
      - src/plugins/forest_korea/config.yaml
    dependencies: [T001]
    blocks: [T005]

  - id: T005
    title: "Unit tests for ForestKorea plugin"
    owner: codex
    priority: P1
    status: pending
    estimated_hours: 3
    outputs:
      - tests/plugins/test_forest_korea.py
    dependencies: [T002]
    blocks: []
```

이 구조를 따르면 3개 LLM CLI가 **동시에, 충돌 없이, 효율적으로** 작업할 수 있습니다!
