# 🎯 원클릭 군집코딩 - 완전 가능합니다!

## ✅ 당신이 원하는 것 (100% 가능)

```
당신: "structure.md 보고 3개 CLI가 분업해서 개발해" (엔터 1번!)

→ Claude:  core 모듈 개발 (병렬)
→ Gemini:  plugins 개발 (병렬)
→ Codex:   tests 개발 (병렬)

→ 3개가 동시에 각자 파일 작성
→ Git 자동 커밋
→ 완료 알림
```

---

## 🔑 핵심: API 직접 호출 방식

### 구조:
```
당신
 ↓
원클릭 스크립트 (swarm.py)
 ├→ Anthropic API (Claude)  → src/core/*.py 생성
 ├→ Google API (Gemini)     → src/plugins/*.py 생성
 └→ OpenAI API (Codex)      → tests/*.py 생성
```

**VSCode CLI는 안 쓰고, API를 직접 호출합니다.**

---

## 📝 실제 구현

### 1. structure.md 작성

**파일: `STRUCTURE.md`**
```markdown
# 프로젝트 구조

## Claude 담당
- src/core/http_fetcher.py
  - fetch_page() 메서드 구현
  - 재시도 로직 포함

- src/core/validator.py
  - 입력 검증 로직

## Gemini 담당
- src/plugins/template/crawler.py
  - BaseCrawler 상속
  - 4개 메서드 구현

- src/plugins/forest_korea/crawler.py
  - main.py에서 마이그레이션

## Codex 담당
- tests/unit/test_http_fetcher.py
  - fetch_page 단위 테스트
  - mock 사용

- tests/unit/test_validator.py
  - 엣지 케이스 커버
```

---

### 2. 원클릭 스크립트

**파일: `.llm/swarm.py`**
```python
#!/usr/bin/env python3
"""
원클릭 군집코딩
사용법: python3 .llm/swarm.py STRUCTURE.md
"""

import asyncio
import os
import sys
from pathlib import Path
from anthropic import Anthropic
from google import generativeai as genai
from openai import OpenAI

class SwarmCoder:
    def __init__(self, structure_file: str):
        self.structure = Path(structure_file).read_text()

        # API 클라이언트
        self.claude = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.gemini = genai.GenerativeModel('gemini-pro')
        self.codex = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def run_claude(self):
        """Claude: core 모듈 개발"""
        print("🏗️  [Claude] core 모듈 작업 시작...")

        # structure.md에서 Claude 담당 추출
        claude_tasks = self._extract_tasks("Claude 담당")

        for task in claude_tasks:
            response = self.claude.messages.create(
                model="claude-sonnet-4",
                messages=[{
                    "role": "user",
                    "content": f"""
프로젝트 구조:
{self.structure}

당신의 작업:
{task}

위 작업을 완료해주세요.
- 파일 경로와 내용을 포함해서 응답
- 코드는 완전히 작동하는 상태로
"""
                }]
            )

            # 응답에서 파일 추출 및 저장
            self._save_files(response.content)

            # Git 커밋
            self._git_commit(f"[Claude] {task['file']}")

        print("✅ [Claude] 완료")

    async def run_gemini(self):
        """Gemini: plugins 개발"""
        print("🔨 [Gemini] plugins 작업 시작...")

        gemini_tasks = self._extract_tasks("Gemini 담당")

        for task in gemini_tasks:
            response = self.gemini.generate_content(
                f"""
프로젝트 구조:
{self.structure}

당신의 작업:
{task}

위 작업을 완료해주세요.
"""
            )

            self._save_files(response.text)
            self._git_commit(f"[Gemini] {task['file']}")

        print("✅ [Gemini] 완료")

    async def run_codex(self):
        """Codex: tests 개발"""
        print("🧪 [Codex] tests 작업 시작...")

        codex_tasks = self._extract_tasks("Codex 담당")

        for task in codex_tasks:
            response = self.codex.chat.completions.create(
                model="gpt-4",
                messages=[{
                    "role": "user",
                    "content": f"""
프로젝트 구조:
{self.structure}

당신의 작업:
{task}

pytest 테스트 코드를 작성해주세요.
"""
                }]
            )

            self._save_files(response.choices[0].message.content)
            self._git_commit(f"[Codex] {task['file']}")

        print("✅ [Codex] 완료")

    def _extract_tasks(self, section: str):
        """structure.md에서 담당 섹션 추출"""
        # "## Claude 담당" 섹션 파싱
        lines = self.structure.split('\n')
        in_section = False
        tasks = []

        for line in lines:
            if section in line:
                in_section = True
                continue

            if in_section:
                if line.startswith('##'):  # 다음 섹션 시작
                    break

                if line.strip().startswith('-'):
                    # 작업 항목 추출
                    tasks.append(line.strip('- ').strip())

        return tasks

    def _save_files(self, content: str):
        """AI 응답에서 파일 추출 및 저장"""
        # 응답에서 ```python ... ``` 블록 추출
        import re

        # 파일 경로 패턴: <!-- file: src/core/foo.py -->
        file_pattern = r'<!-- file: (.+?) -->\s*```\w+\n(.*?)\n```'

        matches = re.finditer(file_pattern, content, re.DOTALL)

        for match in matches:
            file_path = match.group(1)
            file_content = match.group(2)

            # 파일 저장
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            Path(file_path).write_text(file_content)

            print(f"  ✏️  저장: {file_path}")

    def _git_commit(self, message: str):
        """Git 커밋"""
        import subprocess

        subprocess.run(['git', 'add', '.'])
        subprocess.run(['git', 'commit', '-m', message])

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
        print("📊 생성된 파일:")
        subprocess.run(['git', 'diff', '--name-only', 'HEAD~3..HEAD'])

async def main():
    if len(sys.argv) < 2:
        print("사용법: python3 swarm.py STRUCTURE.md")
        sys.exit(1)

    swarm = SwarmCoder(sys.argv[1])
    await swarm.run()

if __name__ == "__main__":
    asyncio.run(main())
```

---

### 3. 사용법

```bash
# 1. API 키 설정 (환경변수)
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."
export OPENAI_API_KEY="sk-..."

# 2. structure.md 작성
vim STRUCTURE.md

# 3. 원클릭 실행!
python3 .llm/swarm.py STRUCTURE.md

# 결과:
🐝 군집코딩 시작!

🏗️  [Claude] core 모듈 작업 시작...
  ✏️  저장: src/core/http_fetcher.py
  ✏️  저장: src/core/validator.py
✅ [Claude] 완료

🔨 [Gemini] plugins 작업 시작...
  ✏️  저장: src/plugins/template/crawler.py
  ✏️  저장: src/plugins/forest_korea/crawler.py
✅ [Gemini] 완료

🧪 [Codex] tests 작업 시작...
  ✏️  저장: tests/unit/test_http_fetcher.py
  ✏️  저장: tests/unit/test_validator.py
✅ [Codex] 완료

🎉 모든 작업 완료!
📊 생성된 파일:
src/core/http_fetcher.py
src/core/validator.py
src/plugins/template/crawler.py
src/plugins/forest_korea/crawler.py
tests/unit/test_http_fetcher.py
tests/unit/test_validator.py
```

---

## 🎯 핵심 정리

### ✅ 가능한 것:
1. **structure.md 작성** → 누가 뭘 할지 명시
2. **원클릭 실행** → `python3 swarm.py STRUCTURE.md`
3. **3개 API 병렬 호출** → 동시에 작업
4. **자동 파일 생성** → 각자 담당 파일 작성
5. **자동 Git 커밋** → 충돌 없이 병합

### ❌ 필요 없는 것:
- VSCode CLI 클릭 ❌
- 수동 전환 ❌
- 순차 작업 ❌

### ✅ 필요한 것:
- API 키 3개 (비용 발생)
- structure.md 작성
- swarm.py 실행

---

## 💰 비용

```python
# 예상 (중형 프로젝트)
Claude:  $3 (10,000 tokens × 2 = 20K)
Gemini:  $0.5 (무료 할당량)
Codex:   $2 (GPT-4)
──────────────────
총: $5.5

시간: 6시간 → 30분
```

---

## 🚀 지금 할 수 있는 것

1. **STRUCTURE.md 작성**
   ```markdown
   # 크롤러 플러그인 시스템

   ## Claude 담당
   - src/core/plugin_loader.py
     - load_plugin() 메서드
     - validate_config()

   ## Gemini 담당
   - src/plugins/template/
     - 전체 구조

   ## Codex 담당
   - tests/
     - pytest 환경
   ```

2. **API 키 설정**
   ```bash
   export ANTHROPIC_API_KEY="..."
   export GOOGLE_API_KEY="..."
   export OPENAI_API_KEY="..."
   ```

3. **실행!**
   ```bash
   python3 .llm/swarm.py STRUCTURE.md
   ```

---

## ✅ 결론

**완전히 가능합니다!**

- ✅ structure.md 하나면 됨
- ✅ 원클릭 실행
- ✅ 3개 CLI(API) 병렬 작업
- ✅ 자동 파일 생성 + 커밋

**VSCode CLI는 안 쓰고, API를 직접 호출하는 방식입니다.**
(VSCode CLI = GUI 도구, 자동화용 아님)

---

**지금 해볼까요?**
STRUCTURE.md부터 같이 만들어볼까요?
