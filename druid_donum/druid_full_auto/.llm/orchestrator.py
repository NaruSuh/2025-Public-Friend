#!/usr/bin/env python3
"""
Multi-Agent Orchestrator for Swarm Coding
실제 군집코딩을 위한 오케스트레이터 예시
"""

import asyncio
import yaml
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum

class AgentType(Enum):
    CLAUDE = "claude"
    GEMINI = "gemini"
    CODEX = "codex"

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"

@dataclass
class Task:
    id: str
    title: str
    agent_type: AgentType
    priority: int
    dependencies: List[str]
    status: TaskStatus
    estimated_hours: float

class WorkQueue:
    """작업 큐 - 모든 에이전트가 공유"""
    def __init__(self):
        self.tasks: List[Task] = []
        self.lock = asyncio.Lock()

    async def add_task(self, task: Task):
        async with self.lock:
            self.tasks.append(task)
            self.tasks.sort(key=lambda t: t.priority, reverse=True)

    async def get_next_task(self, agent_type: AgentType) -> Task | None:
        """에이전트 타입에 맞는 다음 작업 가져오기"""
        async with self.lock:
            for task in self.tasks:
                # 조건: 1) 내 타입, 2) 대기중, 3) 의존성 완료
                if (task.agent_type == agent_type and
                    task.status == TaskStatus.PENDING and
                    self._dependencies_met(task)):
                    task.status = TaskStatus.IN_PROGRESS
                    return task
        return None

    def _dependencies_met(self, task: Task) -> bool:
        """의존성 체크"""
        for dep_id in task.dependencies:
            dep_task = next((t for t in self.tasks if t.id == dep_id), None)
            if dep_task and dep_task.status != TaskStatus.COMPLETED:
                return False
        return True

class Agent:
    """개별 AI 에이전트"""
    def __init__(self, agent_type: AgentType, work_queue: WorkQueue):
        self.type = agent_type
        self.queue = work_queue
        self.current_task: Task | None = None

    async def run(self):
        """에이전트 메인 루프 - 계속 작업 찾아서 실행"""
        print(f"[{self.type.value}] 🚀 에이전트 시작")

        while True:
            # 다음 작업 가져오기
            task = await self.queue.get_next_task(self.type)

            if task is None:
                # 할 일 없으면 1초 대기 후 재확인
                await asyncio.sleep(1)

                # 모든 작업 완료됐으면 종료
                if self._all_tasks_done():
                    print(f"[{self.type.value}] ✅ 모든 작업 완료")
                    break
                continue

            # 작업 수행
            print(f"[{self.type.value}] 📝 작업 시작: {task.title}")
            await self.execute_task(task)

            # 작업 완료 표시
            task.status = TaskStatus.COMPLETED
            print(f"[{self.type.value}] ✅ 작업 완료: {task.title}")

    async def execute_task(self, task: Task):
        """실제 작업 실행 (여기서 LLM API 호출)"""

        if self.type == AgentType.CLAUDE:
            # Claude API 호출
            await self._call_claude_api(task)

        elif self.type == AgentType.GEMINI:
            # Gemini API 호출
            await self._call_gemini_api(task)

        elif self.type == AgentType.CODEX:
            # Codex API 호출
            await self._call_codex_api(task)

    async def _call_claude_api(self, task: Task):
        """Claude API 실제 호출"""
        # 실제론 anthropic SDK 사용
        print(f"  → Claude에게 요청: {task.title}")
        await asyncio.sleep(task.estimated_hours)  # 시뮬레이션

    async def _call_gemini_api(self, task: Task):
        """Gemini API 실제 호출"""
        # 실제론 google.generativeai SDK 사용
        print(f"  → Gemini에게 요청: {task.title}")
        await asyncio.sleep(task.estimated_hours)

    async def _call_codex_api(self, task: Task):
        """Codex API 실제 호출"""
        # 실제론 openai SDK 사용
        print(f"  → Codex에게 요청: {task.title}")
        await asyncio.sleep(task.estimated_hours)

    def _all_tasks_done(self) -> bool:
        """모든 작업이 완료됐는지 확인"""
        return all(
            t.status == TaskStatus.COMPLETED
            for t in self.queue.tasks
        )

class Orchestrator:
    """오케스트레이터 - 에이전트들을 조율"""
    def __init__(self):
        self.queue = WorkQueue()
        self.agents: List[Agent] = []

    def load_tasks_from_yaml(self, yaml_path: str):
        """YAML에서 작업 로드"""
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)

        for task_data in data['tasks']:
            task = Task(
                id=task_data['id'],
                title=task_data['title'],
                agent_type=AgentType(task_data['owner']),
                priority=self._priority_to_int(task_data['priority']),
                dependencies=task_data.get('dependencies', []),
                status=TaskStatus.PENDING,
                estimated_hours=task_data['estimated_hours']
            )
            asyncio.run(self.queue.add_task(task))

    def _priority_to_int(self, priority: str) -> int:
        """P0, P1, P2 → 숫자로 변환"""
        return {'P0': 4, 'P1': 3, 'P2': 2, 'P3': 1}.get(priority, 0)

    def add_agent(self, agent_type: AgentType):
        """에이전트 추가"""
        agent = Agent(agent_type, self.queue)
        self.agents.append(agent)

    async def run(self):
        """모든 에이전트 동시 실행"""
        print("🐝 군집코딩 시작!\n")

        # 모든 에이전트를 비동기로 동시 실행
        tasks = [agent.run() for agent in self.agents]
        await asyncio.gather(*tasks)

        print("\n🎉 군집코딩 완료!")

# 사용 예시
async def main():
    """실제 사용 방법"""

    # 1. 오케스트레이터 생성
    orchestrator = Orchestrator()

    # 2. YAML에서 작업 로드
    # orchestrator.load_tasks_from_yaml('.llm/task_assignments.yaml')

    # 3. 또는 수동으로 작업 추가
    await orchestrator.queue.add_task(Task(
        id="T001",
        title="BaseCrawler 인터페이스 정의",
        agent_type=AgentType.CLAUDE,
        priority=4,
        dependencies=[],
        status=TaskStatus.PENDING,
        estimated_hours=0.5
    ))

    await orchestrator.queue.add_task(Task(
        id="T002",
        title="fetch_page 메서드 구현",
        agent_type=AgentType.GEMINI,
        priority=4,
        dependencies=["T001"],  # T001 완료 후 시작
        status=TaskStatus.PENDING,
        estimated_hours=0.5
    ))

    await orchestrator.queue.add_task(Task(
        id="T003",
        title="parse_list 메서드 구현",
        agent_type=AgentType.CODEX,
        priority=4,
        dependencies=["T001"],  # T001 완료 후 시작
        status=TaskStatus.PENDING,
        estimated_hours=0.5
    ))

    # 4. 에이전트 추가 (3개 동시 실행)
    orchestrator.add_agent(AgentType.CLAUDE)
    orchestrator.add_agent(AgentType.GEMINI)
    orchestrator.add_agent(AgentType.CODEX)

    # 5. 실행!
    await orchestrator.run()

if __name__ == "__main__":
    # 실행
    asyncio.run(main())
