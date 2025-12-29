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
- **Project**: naQV (naru Query Viewport)
- **Purpose**: ECOS API 및 정치경제 정보 API 데이터 분석
- **API Keys**: `.env` 파일에 저장 (ECOS_API_KEY)
- **Main APIs**: 한국은행 ECOS API
