# Claude Code Workflow 전역 설치 가이드

너는 지금부터 개발 워크플로우 설치 도우미야. 아래 작업을 순서대로 수행해줘.

---

## Step 1: 개발 프로젝트 폴더 탐색

먼저 사용자의 개발 프로젝트 폴더들을 찾아줘. 다음 경로들을 탐색해:

```bash
# 일반적인 개발 폴더 위치들
ls -la ~/
ls -la ~/skyimpact/ 2>/dev/null
ls -la ~/projects/ 2>/dev/null
ls -la ~/dev/ 2>/dev/null
ls -la ~/workspace/ 2>/dev/null
```

**프로젝트 폴더 판별 기준** (하나라도 있으면 개발 프로젝트):
- `pyproject.toml` 또는 `requirements.txt` → Python 프로젝트
- `package.json` → Node.js/TypeScript 프로젝트
- `go.mod` → Go 프로젝트
- `Cargo.toml` → Rust 프로젝트
- `.git/` 폴더 존재 → Git 관리되는 프로젝트
- `src/` 폴더 존재 → 소스코드 있는 프로젝트

---

## Step 2: 발견된 프로젝트 목록 출력

찾은 프로젝트들을 이 형식으로 정리해서 보여줘:

```
발견된 개발 프로젝트:

| # | 경로 | 프로젝트 타입 | 설치 상태 |
|---|------|--------------|----------|
| 1 | /home/naru/skyimpact/Labgod | Python | ❌ 미설치 |
| 2 | /home/naru/skyimpact/naQV | Python | ❌ 미설치 |
| 3 | /home/naru/skyimpact/Dolphin | Python | ❌ 미설치 |
...

설치 옵션:
- "all" 입력 → 모든 프로젝트에 설치
- 숫자 입력 (예: "1,3,5") → 선택한 프로젝트에만 설치
- "skip" 입력 → 설치 취소

어떤 프로젝트에 설치할까요?
```

**설치 상태 확인**: `.claude/` 폴더가 이미 있으면 "✅ 설치됨"으로 표시

---

## Step 3: 선택된 프로젝트에 설치 실행

사용자가 선택하면, 각 프로젝트에 대해:

```bash
# 1. 기본 파일 복사
cp -r ~/claude-code-agents-base/.claude [프로젝트경로]/
cp ~/claude-code-agents-base/CLAUDE.md [프로젝트경로]/
cp ~/claude-code-agents-base/Makefile [프로젝트경로]/
cp -r ~/claude-code-agents-base/hack [프로젝트경로]/

# 2. thoughts 디렉토리 생성
mkdir -p [프로젝트경로]/thoughts/shared/{tickets,research,plans,prs}
```

---

## Step 4: Python 프로젝트용 CLAUDE.md 수정

**Python 프로젝트로 감지된 경우**, 해당 프로젝트의 `CLAUDE.md`를 다음 내용으로 **교체**해줘:

```markdown
# CLAUDE.md - Python Project Configuration

## Language Policy
- **CRITICAL**: ALL generated documents, research notes, plans, and internal artifacts MUST be in English only
- User communication can be in Korean, but translate to English before processing
- This saves ~3x tokens compared to Korean (토큰 효율성을 위해 문서는 영어로 작성)

## Context Window Management
- Target: Keep context usage under 40% of total window (Smart Zone)
- Above 40%: Quality degrades significantly (Dumb Zone)
- Use subagents aggressively to offload research and analysis tasks
- Each subagent operates with fresh context, returning only compressed summaries

## Development Workflow
Follow the spec-driven workflow strictly:
1. **Ticket** → Create/load issue specification in `thoughts/shared/tickets/`
2. **Research** → Investigate codebase, document findings in `thoughts/shared/research/`
3. **Plan** → Create detailed implementation plan in `thoughts/shared/plans/`
4. **Implement** → Execute plan in phases, respecting context limits
5. **Validate** → Self-review against plan requirements
6. **PR** → Generate PR description in `thoughts/shared/prs/`

## Project Structure
```
.
├── .claude/
│   ├── agents/       # Subagent definitions
│   ├── commands/     # Slash commands
│   └── settings.json
├── thoughts/
│   └── shared/
│       ├── tickets/  # Issue specs (LOCAL-XXX.md)
│       ├── research/ # Investigation documents
│       ├── plans/    # Implementation plans
│       └── prs/      # PR descriptions
├── src/              # Python source code
├── tests/            # Test files
└── pyproject.toml    # Project configuration
```

## Python Development Standards
- **Python Version**: 3.11+
- **Package Manager**: pip or uv
- **Formatter**: `ruff format`
- **Linter**: `ruff check`
- **Type Checker**: `mypy --strict`
- **Test Runner**: `pytest`

## Quality Check Commands
```bash
# Run all checks
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/ --strict
pytest tests/ -v
```

## Commands Reference
| Command | Purpose |
|---------|---------|
| `/project:create-ticket` | Create new local ticket |
| `/project:research` | Research codebase for ticket |
| `/project:create-plan` | Generate implementation plan |
| `/project:implement` | Execute plan phases |
| `/project:validate` | Validate implementation |
| `/project:describe-pr` | Generate PR description |

## Critical Rules
1. **NEVER** skip the research phase - it prevents hallucination
2. **ALWAYS** use subagents for heavy analysis to preserve main context
3. **NEVER** generate code directly without a plan document
4. **ALWAYS** write plans at code-snippet level detail including file paths
5. If context feels bloated, start fresh session with plan document
6. Run `ruff check` and `pytest` after every implementation phase

## Project-Specific Notes
[Add any project-specific conventions, API keys location, or special instructions here]
```

---

## Step 5: Makefile도 Python용으로 수정

Python 프로젝트의 `Makefile`을 다음으로 **교체**:

```makefile
.PHONY: help setup check test format clean

help:
	@echo "Available commands:"
	@echo "  make setup    - Install dependencies"
	@echo "  make check    - Run linting and type checking"
	@echo "  make test     - Run tests"
	@echo "  make format   - Format code"
	@echo "  make clean    - Clean cache files"

setup:
	pip install -e ".[dev]" 2>/dev/null || pip install -r requirements.txt 2>/dev/null || echo "No dependencies file found"
	pip install ruff mypy pytest pytest-cov

check:
	ruff check src/ tests/ 2>/dev/null || ruff check . 
	mypy src/ --strict 2>/dev/null || mypy . --strict 2>/dev/null || echo "mypy check skipped"

test:
	pytest tests/ -v 2>/dev/null || pytest -v 2>/dev/null || echo "No tests found"

format:
	ruff format src/ tests/ 2>/dev/null || ruff format .
	ruff check --fix src/ tests/ 2>/dev/null || ruff check --fix .

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
```

---

## Step 6: 설치 완료 리포트

모든 설치가 끝나면 이렇게 보고해줘:

```
✅ Claude Code Workflow 설치 완료!

📦 설치된 프로젝트:
| 프로젝트 | 타입 | 상태 |
|---------|------|------|
| /home/naru/skyimpact/Labgod | Python | ✅ 설치 완료 |
| /home/naru/skyimpact/naQV | Python | ✅ 설치 완료 |
...

📁 설치된 파일:
- .claude/agents/ (4개 subagent)
- .claude/commands/ (6개 명령어)
- CLAUDE.md (Python용으로 수정됨)
- Makefile (Python용으로 수정됨)
- thoughts/shared/ (문서 저장 폴더)

🚀 사용법:
   아무 프로젝트에서 Claude Code 열고:
   /project:create-ticket <기능설명>  → 시작!

⚠️ 참고:
   - 원본 템플릿: ~/claude-code-agents-base/
   - 문서는 영어로 생성됨 (토큰 절약)
   - 대화는 한국어 OK
```

---

## 지금 바로 실행해줘!

위 Step 1부터 순서대로 진행해. 먼저 내 개발 프로젝트 폴더들을 찾아서 보여줘.
