# 🐝 군집코딩 (Swarm Coding) 가이드

## 문제: 순차 작업의 비효율

### 현재 상황 (수동 순차)
```
Claude 작업  ████████ (4시간)
                  ↓
Gemini 작업         ████████ (6시간)  ← Claude 놀고 있음
                         ↓
Codex 작업                  ████████ (2시간)  ← Claude, Gemini 놀고 있음
────────────────────────────────────────────────
총 시간: 12시간
활용률: 33% (3명 중 1명만 일함)
```

### 이상: 병렬 군집코딩
```
Claude ████████████████████████████  (계속 일함)
Gemini ████████████████████████████  (계속 일함)
Codex  ████████████████████████████  (계속 일함)
────────────────────────────────────────────────
총 시간: 4시간 (3배 빠름!)
활용률: 100%
```

---

## 해결 방법 3가지

### 방법 1: 작업 세분화 (Task Granularity) ⭐

**핵심 아이디어:**
큰 작업을 잘게 쪼개서 의존성을 줄인다.

#### Before (큰 덩어리)
```yaml
tasks:
  - id: T002
    title: "BaseCrawler 전체 구현"
    owner: claude
    hours: 4  # ← 이 4시간 동안 Gemini, Codex는 놀고 있음
```

#### After (작은 덩어리)
```yaml
tasks:
  - id: T002-1
    title: "BaseCrawler 인터페이스 정의"
    owner: claude
    hours: 0.5
    dependencies: []

  - id: T002-2
    title: "fetch_page 메서드 구현"
    owner: gemini  # ← 동시에 작업 가능!
    hours: 0.5
    dependencies: [T002-1]  # 인터페이스만 있으면 시작

  - id: T002-3
    title: "parse_list 메서드 구현"
    owner: codex  # ← 동시에 작업 가능!
    hours: 0.5
    dependencies: [T002-1]

  - id: T002-4
    title: "통합 및 테스트"
    owner: claude
    hours: 0.5
    dependencies: [T002-2, T002-3]
```

**타임라인:**
```
0:00  Claude: 인터페이스 정의 ████
0:30  Gemini: fetch_page ████  ← 동시!
      Codex:  parse_list ████  ← 동시!
1:00  Claude: 통합 ████
────────────────────────────────
총 시간: 1.5시간 (기존 4시간 → 62% 단축!)
```

---

### 방법 2: Orchestrator 패턴 (추천!) ⭐⭐⭐

**핵심 아이디어:**
중앙 오케스트레이터가 작업을 자동 분배.

#### 구조
```
          [Orchestrator]
               |
   ┌───────────┼───────────┐
   ↓           ↓           ↓
[Claude]    [Gemini]    [Codex]
   ↓           ↓           ↓
 [작업 큐] ← 공유 큐 → [작업 큐]
```

#### 작동 방식
1. **큐에 작업 등록**
   ```python
   queue.add_task(Task(
       id="T002",
       agent_type="gemini",
       dependencies=["T001"]
   ))
   ```

2. **에이전트들이 알아서 가져감**
   ```python
   while True:
       task = queue.get_next_task(my_type)
       if task and dependencies_met(task):
           execute(task)
   ```

3. **의존성 자동 체크**
   - T002가 T001에 의존 → T001 완료될 때까지 대기
   - T001 완료 → T002, T003 동시 시작 (의존성 없으면)

#### 실제 사용 예시

**파일: `.llm/orchestrator.py`** (이미 생성됨!)

```bash
# 사용법
python3 .llm/orchestrator.py

# 출력:
🐝 군집코딩 시작!
[claude] 🚀 에이전트 시작
[claude] 📝 작업 시작: BaseCrawler 인터페이스 정의
[gemini] 🚀 에이전트 시작
[codex] 🚀 에이전트 시작
[claude] ✅ 작업 완료: BaseCrawler 인터페이스 정의
[gemini] 📝 작업 시작: fetch_page 메서드 구현  ← 동시!
[codex] 📝 작업 시작: parse_list 메서드 구현   ← 동시!
```

---

### 방법 3: 역할 분리 (Role Separation) ⭐⭐

**핵심 아이디어:**
같은 파일을 동시에 수정하지 않도록 영역 분리.

#### Before (충돌 발생)
```python
# src/core/base_crawler.py
class BaseCrawler:
    def fetch_page(self):  # ← Claude 작업중
        pass

    def parse_list(self):  # ← Gemini도 동시에 수정? 충돌!
        pass
```

#### After (영역 분리)
```
src/core/
  ├── base_crawler.py      # ← Claude 전담
  ├── http_fetcher.py      # ← Gemini 전담 (fetch_page 로직)
  └── html_parser.py       # ← Codex 전담 (parse 로직)
```

**각자 작업 후 통합:**
```python
# base_crawler.py (Claude)
from .http_fetcher import HttpFetcher  # Gemini가 만든 것
from .html_parser import HtmlParser    # Codex가 만든 것

class BaseCrawler:
    def __init__(self):
        self.fetcher = HttpFetcher()
        self.parser = HtmlParser()
```

---

## 실전 구현: 3단계

### 1단계: 작업 YAML 수정

**파일: `.llm/task_assignments.yaml`**

```yaml
tasks:
  # 작업을 잘게 쪼갠다
  - id: T002-1
    title: "BaseCrawler 인터페이스 스켈레톤"
    owner: claude
    priority: P0
    hours: 0.5
    dependencies: []

  - id: T002-2
    title: "HttpFetcher 유틸리티 구현"
    owner: gemini
    priority: P0
    hours: 1.0
    dependencies: [T002-1]

  - id: T002-3
    title: "HtmlParser 유틸리티 구현"
    owner: codex
    priority: P0
    hours: 1.0
    dependencies: [T002-1]

  - id: T002-4
    title: "통합 및 단위 테스트"
    owner: claude
    priority: P0
    hours: 0.5
    dependencies: [T002-2, T002-3]
```

### 2단계: Orchestrator 실행

```bash
# orchestrator.py 수정해서 실제 LLM API 호출하도록
cd .llm
python3 orchestrator.py
```

**orchestrator.py에 추가해야 할 부분:**

```python
async def _call_claude_api(self, task: Task):
    """실제 Claude API 호출"""
    import anthropic

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # 작업 컨텍스트 로드
    context = self._load_task_context(task)

    # Claude에게 요청
    response = client.messages.create(
        model="claude-sonnet-4",
        messages=[{
            "role": "user",
            "content": f"{context}\n\n작업: {task.title}"
        }]
    )

    # 결과를 Git에 커밋
    self._commit_changes(task, response.content)
```

### 3단계: 모니터링

**파일: `.llm/swarm_monitor.py`**

```python
import time
from orchestrator import Orchestrator

def monitor():
    """실시간 모니터링"""
    orchestrator = Orchestrator()

    while True:
        print("\n=== 군집 상태 ===")
        for agent in orchestrator.agents:
            if agent.current_task:
                print(f"{agent.type}: {agent.current_task.title}")
            else:
                print(f"{agent.type}: 대기중")

        print(f"완료: {len([t for t in orchestrator.queue.tasks if t.status == 'completed'])}")
        print(f"진행중: {len([t for t in orchestrator.queue.tasks if t.status == 'in_progress'])}")

        time.sleep(5)

if __name__ == "__main__":
    monitor()
```

---

## 실제 비용 계산

### 현재 (순차)
```
Claude:  4시간 × $10/hr = $40
Gemini:  6시간 × $5/hr  = $30
Codex:   2시간 × $8/hr  = $16
────────────────────────────
총 시간: 12시간
총 비용: $86
```

### 군집코딩 (병렬)
```
Claude:  4시간 × $10/hr = $40  ← 동시 실행
Gemini:  4시간 × $5/hr  = $20  ← 동시 실행 (놀지 않음)
Codex:   4시간 × $8/hr  = $32  ← 동시 실행 (놀지 않음)
────────────────────────────
총 시간: 4시간 (3배 빠름!)
총 비용: $92 (+$6, 7% 증가)
```

**결론:**
- ⏱️ 시간: 12시간 → 4시간 (67% 단축)
- 💰 비용: $86 → $92 (7% 증가)
- 🎯 시간당 효율: **3배 향상**

---

## 주의사항 & 한계

### 1. Git 충돌 관리
**문제:**
```bash
Claude: base_crawler.py 수정 중
Gemini: base_crawler.py 수정 중
→ Git 충돌!
```

**해결:**
- 파일 단위로 소유권 분리 (방법 3)
- 또는 오케스트레이터가 파일 락 관리

```python
# orchestrator.py에 추가
class FileLock:
    def __init__(self):
        self.locks = {}

    async def acquire(self, file_path: str, agent_type: str):
        if file_path in self.locks:
            raise Exception(f"{file_path}는 {self.locks[file_path]}가 사용중")
        self.locks[file_path] = agent_type

    async def release(self, file_path: str):
        del self.locks[file_path]
```

### 2. API Rate Limit
**문제:**
```
Claude API: 최대 10 req/min
Gemini API: 최대 60 req/min
Codex API: 최대 20 req/min

→ 동시에 요청하면 Rate Limit 걸림
```

**해결:**
```python
import asyncio
from aiolimiter import AsyncLimiter

# API별로 Rate Limiter 설정
claude_limiter = AsyncLimiter(10, 60)  # 10 req/min
gemini_limiter = AsyncLimiter(60, 60)  # 60 req/min

async def _call_claude_api(self, task):
    async with claude_limiter:
        # API 호출
        pass
```

### 3. 의존성 데드락
**문제:**
```yaml
T001: depends on [T002]
T002: depends on [T001]
→ 무한 대기!
```

**해결:**
```python
def detect_circular_dependency(tasks):
    """순환 의존성 탐지"""
    visited = set()

    def dfs(task_id, path):
        if task_id in path:
            raise Exception(f"순환 의존성 발견: {path}")
        if task_id in visited:
            return

        visited.add(task_id)
        task = find_task(task_id)

        for dep_id in task.dependencies:
            dfs(dep_id, path + [task_id])

    for task in tasks:
        dfs(task.id, [])
```

---

## 기존 도구와 비교

### CrewAI
```python
from crewai import Crew, Agent, Task

# 비슷한 개념!
architect = Agent(role="Architect", goal="Design system")
developer = Agent(role="Developer", goal="Write code")

crew = Crew(agents=[architect, developer])
crew.kickoff()
```

### 우리 Orchestrator
```python
# 우리가 만든 것도 거의 동일!
orchestrator = Orchestrator()
orchestrator.add_agent(AgentType.CLAUDE)
orchestrator.add_agent(AgentType.GEMINI)
await orchestrator.run()
```

**차이점:**
- CrewAI: 범용 프레임워크, 학습 곡선 있음
- 우리 것: 우리 프로젝트 특화, 간단함

---

## 다음 단계

### 즉시 가능:
1. ✅ **orchestrator.py 사용** (이미 만들어짐!)
2. ✅ **작업 세분화** (task_assignments.yaml 수정)

### 추가 개발 필요:
3. ⏳ **실제 LLM API 연동**
   - Claude SDK
   - Gemini SDK
   - OpenAI SDK

4. ⏳ **Git 통합**
   - 자동 커밋
   - 충돌 감지
   - 자동 PR 생성

5. ⏳ **모니터링 대시보드**
   - Streamlit으로 실시간 현황 표시
   - 각 에이전트 진행률 시각화

---

## 실행 명령어 요약

```bash
# 1. 시뮬레이션 테스트
python3 .llm/orchestrator.py

# 2. 실제 군집코딩 (TODO: LLM API 연동 후)
# python3 .llm/orchestrator.py --production

# 3. 모니터링 (TODO: 구현 후)
# python3 .llm/swarm_monitor.py
```

---

## 결론

**군집코딩은 가능합니다!**

핵심은:
1. **작업 세분화** - 큰 덩어리를 작게
2. **의존성 명시** - 누가 누굴 기다리는지 명확히
3. **영역 분리** - 같은 파일 동시 수정 방지
4. **자동 조율** - Orchestrator가 알아서 분배

**시작하기:**
- ✅ orchestrator.py는 이미 작동함 (시뮬레이션)
- ⏳ 실제 LLM API 연동만 하면 바로 사용 가능!

---

**질문이나 개선 아이디어:**
`.llm/CURRENT_STATUS.md`의 "Communication Log"에 남겨주세요!
