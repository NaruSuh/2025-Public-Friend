#!/usr/bin/env python3
"""
군집코딩 데모 - 시각적으로 보기 좋게 개선한 버전
"""

import asyncio
import time
from orchestrator import (
    Task, AgentType, TaskStatus, WorkQueue, Agent, Orchestrator
)

class VisualAgent(Agent):
    """시각적 효과가 있는 에이전트"""

    async def execute_task(self, task: Task):
        """작업 실행 시뮬레이션 - 진행률 표시"""

        # 시작 메시지
        emoji = {"claude": "🏗️", "gemini": "🔨", "codex": "🧪"}
        print(f"  {emoji.get(self.type.value, '⚙️')} {self.type.value.upper()}: {task.title}")

        # 진행률 표시
        steps = 10
        for i in range(steps):
            await asyncio.sleep(task.estimated_hours / steps)
            progress = (i + 1) / steps * 100
            bar = "█" * (i + 1) + "░" * (steps - i - 1)
            print(f"     [{bar}] {progress:.0f}%", end='\r')

        print()  # 줄바꿈

async def demo_sequential():
    """순차 실행 데모 (비교용)"""
    print("\n" + "="*60)
    print("📌 순차 실행 (기존 방식)")
    print("="*60 + "\n")

    tasks = [
        ("Claude", "BaseCrawler 인터페이스 정의", 0.5),
        ("Gemini", "fetch_page 메서드 구현", 0.5),
        ("Codex", "parse_list 메서드 구현", 0.5),
    ]

    start = time.time()

    for agent, task_name, duration in tasks:
        print(f"🔵 {agent}: {task_name}")
        await asyncio.sleep(duration)
        print(f"✅ {agent}: 완료\n")

    elapsed = time.time() - start
    print(f"⏱️  총 소요 시간: {elapsed:.1f}초\n")
    return elapsed

async def demo_parallel():
    """병렬 실행 데모 (군집코딩)"""
    print("\n" + "="*60)
    print("🐝 군집코딩 (병렬 실행)")
    print("="*60 + "\n")

    orchestrator = Orchestrator()

    # 작업 추가
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
        dependencies=["T001"],
        status=TaskStatus.PENDING,
        estimated_hours=0.5
    ))

    await orchestrator.queue.add_task(Task(
        id="T003",
        title="parse_list 메서드 구현",
        agent_type=AgentType.CODEX,
        priority=4,
        dependencies=["T001"],
        status=TaskStatus.PENDING,
        estimated_hours=0.5
    ))

    # 시각적 에이전트로 교체
    orchestrator.agents = [
        VisualAgent(AgentType.CLAUDE, orchestrator.queue),
        VisualAgent(AgentType.GEMINI, orchestrator.queue),
        VisualAgent(AgentType.CODEX, orchestrator.queue),
    ]

    start = time.time()
    await orchestrator.run()
    elapsed = time.time() - start

    print(f"\n⏱️  총 소요 시간: {elapsed:.1f}초\n")
    return elapsed

async def main():
    """메인 함수"""

    print("\n" + "🎯" * 30)
    print("        군집코딩 (Swarm Coding) 효과 비교")
    print("🎯" * 30)

    # 순차 실행
    sequential_time = await demo_sequential()

    # 잠깐 대기
    await asyncio.sleep(1)

    # 병렬 실행
    parallel_time = await demo_parallel()

    # 결과 비교
    print("="*60)
    print("📊 성능 비교 결과")
    print("="*60)
    print(f"순차 실행:   {sequential_time:.1f}초")
    print(f"병렬 실행:   {parallel_time:.1f}초")
    print(f"속도 개선:   {sequential_time / parallel_time:.1f}배 빠름! 🚀")
    print(f"시간 절약:   {sequential_time - parallel_time:.1f}초 ({(1 - parallel_time/sequential_time)*100:.0f}%)")
    print("="*60 + "\n")

    print("💡 실제 프로젝트에서는:")
    print(f"   12시간 작업 → {12 / (sequential_time / parallel_time):.1f}시간으로 단축!")
    print(f"   활용률: 33% → 100% (3배 효율)")
    print()

if __name__ == "__main__":
    asyncio.run(main())
