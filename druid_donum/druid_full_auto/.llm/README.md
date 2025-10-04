# Multi-LLM Collaboration System

이 디렉토리는 Claude Code, Gemini CLI, Codex CLI가 충돌 없이 협업할 수 있도록 설계되었습니다.

---

## Quick Start

### For Claude Code
```bash
cat contexts/claude_context.md
cat task_assignments.yaml | yq '.tasks[] | select(.owner == "claude" and .status == "pending")'
```

### For Gemini CLI
```bash
cat contexts/gemini_context.md
cat ../CURRENT_STATUS.md | tail -20
```

### For Codex CLI
```bash
cat contexts/codex_context.md
pytest tests/ --cov
```

---

## Directory Structure

```
.llm/
├── README.md                  # This file
├── task_assignments.yaml      # Central task tracker
├── contexts/
│   ├── claude_context.md      # Claude-specific instructions
│   ├── gemini_context.md      # Gemini-specific instructions
│   └── codex_context.md       # Codex-specific instructions
└── locks/                     # File locks (auto-created)
    └── src__core__base_crawler.py  # Example lock
```

---

## Workflow

### 1. Check Your Tasks
```bash
# Claude
yq '.tasks[] | select(.owner == "claude")' task_assignments.yaml

# Gemini
yq '.tasks[] | select(.owner == "gemini")' task_assignments.yaml

# Codex
yq '.tasks[] | select(.owner == "codex")' task_assignments.yaml
```

### 2. Lock Your File
```bash
# Before editing src/core/base_crawler.py
echo "claude:$(date -Iseconds)" > locks/src__core__base_crawler.py
```

### 3. Work on Your Task
- Follow your context file (`contexts/{your_llm}_context.md`)
- Check dependencies in `task_assignments.yaml`
- Update `../CURRENT_STATUS.md` as you go

### 4. Unlock & Commit
```bash
# After done
rm locks/src__core__base_crawler.py

# Commit with prefix
git commit -m "[Claude] T002: Implement BaseCrawler"
```

---

## Communication

### Async Messages
Write to `../CURRENT_STATUS.md`:

```markdown
## [2025-10-05 18:00] Claude Code → Gemini CLI

@Gemini: BaseCrawler is ready for you!

Files:
- src/core/base_crawler.py
- src/core/parser_factory.py

Your next task: T005 (ForestKorea migration)

Questions? Reply here or check ARCHITECTURE.md
```

### Check for Messages
```bash
cat ../CURRENT_STATUS.md | grep "@Claude"
```

---

## Helper Scripts (Coming Soon)

```bash
# Check status
./scripts/llm-status.sh

# Assign task
./scripts/assign-task.sh --llm gemini --task T030

# Generate handoff
./scripts/handoff.sh --from claude --to gemini --task T002
```

---

## Rules

1. **Read before writing**: Always check `../CURRENT_STATUS.md` first
2. **Lock files**: Use `locks/` directory
3. **Commit prefixes**: `[Claude]`, `[Gemini]`, `[Codex]`
4. **Stay in your lane**: Don't edit files outside your ownership
5. **Update task_assignments.yaml**: Mark tasks completed

---

## Emergency

### Broken Build
```bash
git log --oneline -5  # Find culprit
git revert HEAD       # Revert last commit
# Update CURRENT_STATUS.md with incident report
```

### Lost Context
```bash
cat ../ARCHITECTURE.md
cat ../CURRENT_STATUS.md
cat contexts/{your_llm}_context.md
git log --oneline -20
```

---

## Metrics

Track in `../CURRENT_STATUS.md`:
- Tasks completed per LLM
- Average time per task
- Merge conflicts (goal: 0)
- Test coverage per module

---

## Tips

- Use `yq` for YAML parsing (`brew install yq` or `pip install yq`)
- Git aliases help:
  ```bash
  git config alias.llm-log "log --oneline --author='Claude\|Gemini\|Codex'"
  ```
- Set environment variable:
  ```bash
  export LLM_NAME=claude  # or gemini, codex
  ```

---

Good luck! 🚀
