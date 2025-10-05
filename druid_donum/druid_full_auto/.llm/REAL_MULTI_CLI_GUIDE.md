# 🎯 실제 Multi-CLI 협업 가이드

VSCode에 Claude Code CLI, Google Gemini CLI, Codex CLI가 모두 설치되어 있다면
**진짜 군집코딩**이 가능합니다!

---

## 🎮 현재 상황

### ✅ 설치되어 있는 것:
- **Claude Code CLI** (나)
- **Google Gemini CLI**
- **Codex CLI**

### ✅ 이미 준비된 것:
- `.llm/task_assignments.yaml` - 작업 분배표
- `.llm/contexts/*.md` - 각 CLI별 가이드
- `CURRENT_STATUS.md` - 진행 상황 추적
- `.llm/HANDOFF_TO_GEMINI.md` - 인수인계 문서

---

## 🚀 실제 협업 방법 3가지

### 방법 1: 수동 릴레이 (현재 가능) ⭐

**가장 간단하고 안전한 방법**

#### 작업 흐름:
```
당신 → Claude Code CLI 호출 → 작업 → Git 커밋
       ↓
당신 → Gemini CLI 호출 → 작업 → Git 커밋
       ↓
당신 → Codex CLI 호출 → 작업 → Git 커밋
```

#### 실제 사용법:

**1단계: Claude에게 작업 지시**
```
VSCode에서:
- Cmd/Ctrl + Shift + P
- "Claude Code: Chat"
- 입력: "T002 작업해줘. .llm/task_assignments.yaml 참고해"

Claude가 작업 → 커밋
```

**2단계: Gemini에게 인계**
```
VSCode에서:
- Cmd/Ctrl + Shift + P
- "Gemini: Chat" (또는 Gemini CLI 명령어)
- 입력: ".llm/HANDOFF_TO_GEMINI.md 읽고 T004, T005 작업해줘"

Gemini가 작업 → 커밋
```

**3단계: Codex에게 인계**
```
VSCode에서:
- Codex CLI 실행
- 입력: ".llm/contexts/codex_context.md 읽고 테스트 작성해줘"

Codex가 작업 → 커밋
```

**장점:**
- ✅ Git 충돌 없음 (순차 실행)
- ✅ 각 단계 확인 가능
- ✅ 안전함

**단점:**
- ⚠️ 병렬 실행 아님
- ⚠️ 당신이 수동으로 전환

---

### 방법 2: 병렬 창 작업 (중급) ⭐⭐

**VSCode 창을 여러 개 띄워서 동시 작업**

#### 준비:
```bash
# 터미널 3개 열기
터미널 1: Claude Code CLI
터미널 2: Gemini CLI
터미널 3: Codex CLI
```

#### 작업 흐름:

**터미널 1 (Claude):**
```bash
# 독립적인 작업만 할당
> "src/core/http_fetcher.py 만들어줘"
→ 작업 → Git 커밋
```

**터미널 2 (Gemini) - 동시에:**
```bash
# 다른 파일 작업
> "src/plugins/template/ 플러그인 템플릿 만들어줘"
→ 작업 → Git 커밋
```

**터미널 3 (Codex) - 동시에:**
```bash
# 또 다른 독립적인 작업
> "tests/unit/test_parser_factory.py 단위 테스트 작성해줘"
→ 작업 → Git 커밋
```

**핵심 규칙:**
```yaml
# 각 CLI가 다른 파일을 건드리도록!
Claude:
  - src/core/http_fetcher.py
  - src/core/validator.py

Gemini:
  - src/plugins/template/*
  - src/plugins/forest_korea/*

Codex:
  - tests/unit/*
  - tests/integration/*
```

**장점:**
- ✅ 실제 병렬 작업 가능!
- ✅ 속도 2-3배 빨라짐

**단점:**
- ⚠️ Git 충돌 가능성 (파일 분리 필요)
- ⚠️ 당신이 3개 창 관리해야 함

---

### 방법 3: 스크립트 자동화 (고급) ⭐⭐⭐

**스크립트로 자동 분배**

#### 파일 생성: `.llm/run_swarm.sh`

```bash
#!/bin/bash
# 실제 Multi-CLI 자동 실행 스크립트

PROJECT_DIR="/home/naru/work/2025-Public-Friend/druid_donum/druid_full_auto"
cd "$PROJECT_DIR"

echo "🐝 군집코딩 시작!"

# 파일 락 디렉토리 생성
mkdir -p .llm/locks

# 백그라운드로 각 CLI 실행
echo "🏗️  Claude 작업 시작..."
(
    # Claude CLI 실행 (VSCode API 사용)
    code --command "claude-code.executeTask" \
         --args ".llm/contexts/claude_context.md 읽고 T002 작업 시작"

    # 완료 후 락 파일 제거
    rm -f .llm/locks/claude.lock
) &

echo "🔨 Gemini 작업 시작..."
(
    # Gemini CLI 실행
    # (실제 명령어는 Gemini CLI 문서 참고)
    gemini-cli execute --context=".llm/contexts/gemini_context.md" \
                       --task="T004"

    rm -f .llm/locks/gemini.lock
) &

echo "🧪 Codex 작업 시작..."
(
    # Codex CLI 실행
    codex-cli run --context=".llm/contexts/codex_context.md" \
                  --task="T010"

    rm -f .llm/locks/codex.lock
) &

# 모든 작업 완료 대기
wait

echo "🎉 군집코딩 완료!"
```

**사용법:**
```bash
chmod +x .llm/run_swarm.sh
./.llm/run_swarm.sh
```

**장점:**
- ✅ 완전 자동화
- ✅ 진짜 병렬 실행
- ✅ 당신은 결과만 확인

**단점:**
- ⚠️ CLI별 명령어 문법 확인 필요
- ⚠️ 디버깅 어려움

---

## 📋 실전 워크플로우

### 시나리오: ForestKorea 플러그인 마이그레이션

**당신의 할 일:**
```bash
# 1. 작업 확인
cat .llm/task_assignments.yaml

# 2. 상태 업데이트
echo "작업 시작: $(date)" >> CURRENT_STATUS.md

# 3. 각 CLI에 작업 할당
```

**Claude Code CLI (당신이 지금 사용중):**
```
당신: "T006 시작해줘. Plugin loader/registry 구현"

Claude:
→ src/core/plugin_loader.py 생성
→ config validation 추가
→ Git 커밋
```

**Gemini CLI:**
```
VSCode 터미널 2에서:
> gemini-cli

당신: ".llm/HANDOFF_TO_GEMINI.md 읽고 T005 시작"

Gemini:
→ src/plugins/forest_korea/ 생성
→ main.py 로직 마이그레이션
→ Git 커밋
```

**Codex CLI:**
```
VSCode 터미널 3에서:
> codex-cli

당신: ".llm/contexts/codex_context.md 보고 pytest 환경 구축"

Codex:
→ pip install pytest
→ tests/unit/test_parser_factory.py 작성
→ Git 커밋
```

**결과:**
```
3시간 걸릴 작업을 1시간에 완료! ⚡
```

---

## 🔒 Git 충돌 방지 규칙

### 파일 소유권 명확히 하기

**`.llm/file_ownership.yaml` 생성:**
```yaml
ownership:
  claude:
    - "src/core/*.py"
    - "src/ui/*.py"
    - ".llm/ARCHITECTURE.md"

  gemini:
    - "src/plugins/*/*.py"
    - "src/plugins/*/config.yaml"

  codex:
    - "tests/**/*.py"
    - "pytest.ini"
    - ".llm/audits/*.md"

shared:
  - "CURRENT_STATUS.md"  # 모두 업데이트 가능
  - ".llm/task_assignments.yaml"
```

### 작업 전 체크:
```bash
# Claude가 작업하려는 파일
FILE="src/core/base_crawler.py"

# 소유권 확인
if grep -q "$FILE" .llm/file_ownership.yaml | grep claude; then
    echo "✅ OK to edit"
else
    echo "❌ This file belongs to another agent!"
fi
```

---

## 📊 진행 상황 모니터링

### 실시간 대시보드 (옵션)

**`.llm/monitor_dashboard.py`:**
```python
#!/usr/bin/env python3
"""실시간 협업 현황 모니터"""

import yaml
import time
from pathlib import Path

def show_status():
    with open('.llm/task_assignments.yaml') as f:
        data = yaml.safe_load(f)

    print("\n" + "="*60)
    print("🐝 Multi-CLI 협업 현황")
    print("="*60)

    for task in data['tasks']:
        status_icon = {
            'completed': '✅',
            'in_progress': '🔄',
            'pending': '⏳',
            'blocked': '🚫'
        }[task['status']]

        print(f"{status_icon} [{task['owner']}] {task['title']}")

    # Git 상태
    import subprocess
    result = subprocess.run(['git', 'status', '--short'],
                          capture_output=True, text=True)

    if result.stdout:
        print("\n📝 수정된 파일:")
        print(result.stdout)

if __name__ == "__main__":
    while True:
        show_status()
        time.sleep(5)  # 5초마다 갱신
```

**사용:**
```bash
python3 .llm/monitor_dashboard.py
```

---

## 🎯 권장 작업 흐름 (Best Practice)

### Phase 1: 순차 작업 (안전)
```
1. Claude: 핵심 구조 완성 (T002, T003)
2. Gemini: 플러그인 작성 (T004, T005)
3. Codex: 테스트 작성 (T010, T011)
```

### Phase 2: 병렬 작업 (효율)
```
동시에:
- Claude: UI 개선
- Gemini: 새 플러그인 추가 (Naver Cafe)
- Codex: 통합 테스트
```

### Phase 3: 통합
```
Claude: 모두 통합, 충돌 해결, 최종 리뷰
```

---

## 🚨 주의사항

### 1. API 비용
```
Claude Sonnet:  $3/M tokens input, $15/M tokens output
Gemini Pro:     $0.125/M tokens (둘 다)
Codex:          $0.002/token

→ 동시 실행하면 비용 3배!
→ 작업 분배 잘 해야 함
```

### 2. Rate Limit
```
각 API마다 분당 요청 수 제한 있음
3개 동시 실행 시 제한 걸릴 수 있음
```

### 3. Git 충돌
```
같은 파일 동시 수정 → 충돌!
→ 파일 소유권 명확히 하기
```

---

## ✅ 체크리스트: 시작 전 확인

- [ ] Claude Code CLI 설치 확인
- [ ] Gemini CLI 설치 확인
- [ ] Codex CLI 설치 확인
- [ ] API 키 설정 완료
- [ ] `.llm/file_ownership.yaml` 생성
- [ ] `CURRENT_STATUS.md` 최신 상태 확인
- [ ] Git 작업 브랜치 생성 (선택)

---

## 🎬 Quick Start

**지금 바로 시작:**

```bash
# 1. 현재 상태 확인
cat .llm/task_assignments.yaml

# 2. Claude (당신이 지금 사용중)
"다음 작업 시작: T006 plugin loader"

# 3. 새 터미널 열어서 Gemini
# (Gemini CLI 명령어로 실행)

# 4. 또 다른 터미널에서 Codex
# (Codex CLI 명령어로 실행)

# 5. 완료 후 통합
git pull --rebase
# 충돌 해결
git push
```

---

## 💡 팁

### Tip 1: 작업 크기
```
큰 작업 (4시간) → 잘게 쪼개기 (30분씩)
→ 충돌 가능성 ↓
→ 병렬 효율 ↑
```

### Tip 2: 커밋 자주
```
작은 단위로 자주 커밋
→ 충돌 시 롤백 쉬움
```

### Tip 3: 브랜치 전략
```
main
 ├── claude-core (Claude 작업)
 ├── gemini-plugins (Gemini 작업)
 └── codex-tests (Codex 작업)

→ 나중에 main에 merge
```

---

## 📞 문제 해결

### Q: Gemini CLI 명령어를 모르겠어요
A: VSCode에서 `Cmd+Shift+P` → "Gemini" 검색 → 사용 가능한 명령어 확인

### Q: Git 충돌이 났어요
A:
```bash
git status
git diff
# 수동으로 충돌 해결
git add .
git commit
```

### Q: 어떤 CLI가 어떤 작업을 해야 하나요?
A: `.llm/task_assignments.yaml`의 `owner` 필드 참고

---

## 🎉 결론

**3개 CLI를 모두 설치했다면:**
- ✅ 순차 작업 (방법 1) - 지금 바로 가능!
- ✅ 병렬 작업 (방법 2) - 파일 분리만 하면 가능!
- ⏳ 자동화 (방법 3) - 스크립트 작성 필요

**추천:**
먼저 **방법 1 (수동 릴레이)**로 시작해서
감을 익힌 후 **방법 2 (병렬 창)**으로 발전!

---

**시작해볼까요? 어떤 방법으로 해보고 싶으세요?**
