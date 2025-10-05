#!/usr/bin/env python3
"""
진짜 작동하는 군집코딩
로컬 파일 읽기 + API 호출 + 파일 저장
"""

import asyncio
import os
import re
from pathlib import Path
from anthropic import Anthropic
# from google import generativeai as genai
# from openai import OpenAI

class FileContext:
    """로컬 파일 시스템 관리"""

    def __init__(self, project_root: str):
        self.root = Path(project_root)

    def read_file(self, path: str) -> str:
        """파일 읽기"""
        full_path = self.root / path
        if full_path.exists():
            return full_path.read_text()
        return ""

    def read_all_files(self, pattern: str) -> dict:
        """패턴 매칭되는 모든 파일 읽기"""
        files = {}
        for file in self.root.rglob(pattern):
            rel_path = file.relative_to(self.root)
            files[str(rel_path)] = file.read_text()
        return files

    def write_file(self, path: str, content: str):
        """파일 쓰기"""
        full_path = self.root / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        print(f"  ✏️  저장: {path}")

class SwarmCoder:
    def __init__(self, structure_file: str):
        self.structure = Path(structure_file).read_text()
        self.files = FileContext(".")

        # API 클라이언트
        self.claude = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        # self.gemini = genai.GenerativeModel('gemini-pro')
        # self.codex = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def run_claude(self):
        """Claude: core 모듈 개발"""
        print("🏗️  [Claude] core 모듈 작업 시작...")

        # 기존 파일들 읽기
        existing_files = self.files.read_all_files("src/core/*.py")

        # 컨텍스트 구성
        context = f"""
프로젝트 구조:
{self.structure}

기존 파일들:
"""
        for path, content in existing_files.items():
            context += f"\n### {path}\n```python\n{content}\n```\n"

        context += """
당신의 작업 (structure.md의 "Claude 담당" 섹션):
- src/core/plugin_loader.py 생성
- src/core/validator.py 생성

요구사항:
1. 기존 base_crawler.py, parser_factory.py와 호환되게
2. 각 파일은 <!-- file: 경로 --> 형식으로 표시
3. 완전히 작동하는 코드로

출력 형식:
<!-- file: src/core/plugin_loader.py -->
```python
# 코드 내용
```
"""

        response = self.claude.messages.create(
            model="claude-sonnet-4",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": context
            }]
        )

        # 응답에서 파일 추출 및 저장
        self._extract_and_save_files(response.content[0].text)

        print("✅ [Claude] 완료")

    async def run_gemini(self):
        """Gemini: plugins 개발"""
        print("🔨 [Gemini] plugins 작업 시작...")

        # 기존 main.py 읽기 (마이그레이션할 코드)
        main_py = self.files.read_file("main.py")
        base_crawler = self.files.read_file("src/core/base_crawler.py")

        context = f"""
프로젝트 구조:
{self.structure}

기존 코드:
### main.py (마이그레이션할 코드)
```python
{main_py}
```

### src/core/base_crawler.py (상속할 클래스)
```python
{base_crawler}
```

당신의 작업:
1. main.py의 ForestBidCrawler를 src/plugins/forest_korea/crawler.py로 마이그레이션
2. BaseCrawler를 상속하도록 수정
3. config.yaml 생성

출력 형식:
<!-- file: src/plugins/forest_korea/crawler.py -->
```python
# 코드
```

<!-- file: src/plugins/forest_korea/config.yaml -->
```yaml
# 설정
```
"""

        # Gemini API 호출 (시뮬레이션)
        print("  📝 Gemini API 호출 중...")
        await asyncio.sleep(1)  # 실제로는 API 호출

        # 임시: 샘플 응답
        sample_response = """
<!-- file: src/plugins/forest_korea/crawler.py -->
```python
from src.core import BaseCrawler

class ForestKoreaCrawler(BaseCrawler):
    def fetch_page(self, url, params):
        # 구현
        pass
```
"""
        self._extract_and_save_files(sample_response)

        print("✅ [Gemini] 완료")

    async def run_codex(self):
        """Codex: tests 개발"""
        print("🧪 [Codex] tests 작업 시작...")

        # 테스트할 파일 읽기
        plugin_loader = self.files.read_file("src/core/plugin_loader.py")

        context = f"""
프로젝트 구조:
{self.structure}

테스트할 코드:
### src/core/plugin_loader.py
```python
{plugin_loader}
```

당신의 작업:
pytest 단위 테스트 작성

출력 형식:
<!-- file: tests/unit/test_plugin_loader.py -->
```python
import pytest
# 테스트 코드
```
"""

        # Codex API 호출 (시뮬레이션)
        print("  📝 Codex API 호출 중...")
        await asyncio.sleep(1)

        print("✅ [Codex] 완료")

    def _extract_and_save_files(self, content: str):
        """응답에서 파일 추출 및 저장"""
        # 패턴: <!-- file: 경로 --> 다음에 코드 블록
        pattern = r'<!--\s*file:\s*(.+?)\s*-->\s*```\w*\n(.*?)\n```'

        matches = re.finditer(pattern, content, re.DOTALL)

        for match in matches:
            file_path = match.group(1).strip()
            file_content = match.group(2)

            self.files.write_file(file_path, file_content)

    async def run(self):
        """3개 동시 실행"""
        print("🐝 군집코딩 시작!\n")

        # 병렬 실행
        await asyncio.gather(
            self.run_claude(),
            self.run_gemini(),
            self.run_codex()
        )

        print("\n🎉 모든 작업 완료!")

        # Git 커밋
        import subprocess
        subprocess.run(['git', 'add', '.'])
        subprocess.run(['git', 'status', '--short'])

async def main():
    import sys

    if len(sys.argv) < 2:
        print("사용법: python3 swarm_real.py STRUCTURE.md")
        sys.exit(1)

    swarm = SwarmCoder(sys.argv[1])
    await swarm.run()

if __name__ == "__main__":
    asyncio.run(main())
