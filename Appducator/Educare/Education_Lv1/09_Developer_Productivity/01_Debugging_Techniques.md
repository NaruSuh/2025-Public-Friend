# 09.01 - Vibe Coding Debugging Techniques
# 09.01 - Vibe Coding 디버깅 기술

Bugs are inevitable. A Vibe Coder, however, approaches them systematically and efficiently. The goal is not just to fix the bug, but to understand its root cause and ensure it doesn't happen again. Debugging is a science, not a random walk.
버그는 피할 수 없습니다. 그러나 Vibe 코더는 체계적이고 효율적으로 접근합니다. 목표는 버그를 수정하는 것뿐만 아니라 근본 원인을 이해하고 다시 발생하지 않도록 하는 것입니다. 디버깅은 무작위적인 행보가 아니라 과학입니다.

## Core Principles
## 핵심 원칙

1.  **Reproduce the Bug**: You cannot fix what you cannot see. The first step is always to create a minimal, reliable way to reproduce the bug. This often means writing a failing test.
    **버그 재현**: 볼 수 없는 것은 고칠 수 없습니다. 첫 번째 단계는 항상 버그를 재현할 수 있는 최소한의 안정적인 방법을 만드는 것입니다. 이것은 종종 실패하는 테스트를 작성하는 것을 의미합니다.
2.  **Isolate the Problem**: Narrow down the scope. Is the bug in the frontend, the API, the database, or the interaction between them? Use logs, error messages, and the process of elimination.
    **문제 분리**: 범위를 좁힙니다. 버그가 프런트엔드, API, 데이터베이스 또는 그들 간의 상호 작용에 있습니까? 로그, 오류 메시지 및 제거 프로세스를 사용하십시오.
3.  **Question Your Assumptions**: The bug is often where you least expect it. The one line of code you think is "obviously correct" might be the culprit. Don't trust your assumptions; verify them.
    **가정 의심**: 버그는 종종 가장 예상치 못한 곳에 있습니다. "분명히 맞다"고 생각하는 코드 한 줄이 범인일 수 있습니다. 가정을 믿지 말고 확인하십시오.
4.  **Use the Right Tool**: Don't rely on `print()` statements alone. Learn to use a proper debugger, interpret logs, and use monitoring tools.
    **올바른 도구 사용**: `print()` 문에만 의존하지 마십시오. 적절한 디버거를 사용하고, 로그를 해석하고, 모니터링 도구를 사용하는 법을 배우십시오.

---

## 1. The Power of a Failing Test
## 1. 실패하는 테스트의 힘

Before you change any code, write a test that fails because of the bug. This is a core tenet of Test-Driven Development (TDD), but it's invaluable for debugging even if you don't follow TDD strictly.
코드를 변경하기 전에 버그로 인해 실패하는 테스트를 작성하십시오. 이것은 테스트 주도 개발(TDD)의 핵심 신조이지만, TDD를 엄격하게 따르지 않더라도 디버깅에 매우 중요합니다.

**Why?**
**왜?**
-   **It proves the bug exists**: It provides a concrete, repeatable demonstration of the problem.
    **버그 존재 증명**: 문제에 대한 구체적이고 반복 가능한 데모를 제공합니다.
-   **It defines "done"**: The bug is fixed when the test passes. No guesswork.
    **"완료" 정의**: 테스트가 통과하면 버그가 수정된 것입니다. 추측이 없습니다.
-   **It prevents regression**: This test becomes part of your test suite, ensuring the same bug doesn't reappear in the future.
    **회귀 방지**: 이 테스트는 테스트 스위트의 일부가 되어 향후 동일한 버그가 다시 나타나지 않도록 합니다.

```python
# tests/test_feature.py

# Assume we found a bug where negative numbers are handled incorrectly
def test_handle_negative_numbers_bug():
    # This test should fail initially
    result = my_buggy_function(-10)
    assert result == "Handled -10 correctly"
```

Now, your goal is simple: make this test pass.
이제 목표는 간단합니다. 이 테스트를 통과시키는 것입니다.

---

## 2. The Interactive Debugger (`pdb` or VSCode)
## 2. 대화형 디버거 (`pdb` 또는 VSCode)

`print()` statements are useful, but a real debugger is a superpower. It lets you pause your code mid-execution, inspect the state of all variables, and step through the logic line by line.
`print()` 문은 유용하지만 실제 디버거는 초능력입니다. 코드를 실행 중에 일시 중지하고, 모든 변수의 상태를 검사하고, 논리를 한 줄씩 단계별로 실행할 수 있습니다.

### Using the VSCode Debugger
### VSCode 디버거 사용

This is the most user-friendly way to debug.
이것이 가장 사용자 친화적인 디버깅 방법입니다.

1.  **Set a Breakpoint**: Click in the gutter to the left of a line number in your code. A red dot will appear. This is where the code will pause.
    **중단점 설정**: 코드의 줄 번호 왼쪽 여백을 클릭합니다. 빨간 점이 나타납니다. 코드가 여기서 일시 중지됩니다.
2.  **Run the Debugger**: Go to the "Run and Debug" panel in VSCode, select the appropriate configuration (e.g., "Python: Pytest"), and click the green play button.
    **디버거 실행**: VSCode의 "실행 및 디버그" 패널로 이동하여 적절한 구성(예: "Python: Pytest")을 선택하고 녹색 재생 버튼을 클릭합니다.
3.  **Inspect and Step**: When the code pauses at your breakpoint:
    **검사 및 단계별 실행**: 코드가 중단점에서 일시 중지되면:
    -   **Variables Panel**: See the current value of all local and global variables.
        **변수 패널**: 모든 지역 및 전역 변수의 현재 값을 확인합니다.
    -   **Debug Console**: Interactively run Python code in the context of the paused function.
        **디버그 콘솔**: 일시 중지된 함수의 컨텍스트에서 대화형으로 파이썬 코드를 실행합니다.
    -   **Control Bar**:
        **제어 막대**:
        -   **Continue (F5)**: Resume execution until the next breakpoint.
            **계속(F5)**: 다음 중단점까지 실행을 재개합니다.
        -   **Step Over (F10)**: Execute the current line and move to the next, without going *into* function calls on the current line.
            **한 단계 건너뛰기(F10)**: 현재 줄의 함수 호출로 들어가지 않고 현재 줄을 실행하고 다음 줄로 이동합니다.
        -   **Step Into (F11)**: If the current line is a function call, move the debugger into that function.
            **한 단계 들어가기(F11)**: 현재 줄이 함수 호출인 경우 디버거를 해당 함수로 이동합니다.
        -   **Step Out (Shift+F11)**: Finish executing the current function and return to the line where it was called.
            **한 단계 나가기(Shift+F11)**: 현재 함수 실행을 완료하고 호출된 줄로 돌아갑니다.

### Using `pdb` (Python's built-in debugger)
### `pdb` 사용 (파이썬 내장 디버거)

For a quick debug session in the terminal, you can drop a breakpoint directly into your code.
터미널에서 빠른 디버그 세션을 위해 코드에 직접 중단점을 설정할 수 있습니다.

```python
def my_buggy_function(x):
    a = x * 2
    # I want to inspect the state here
    import pdb; pdb.set_trace()
    b = a - 5
    return b
```

When you run this code, it will pause at that line and give you a `(Pdb)` prompt. You can type commands like:
이 코드를 실행하면 해당 줄에서 일시 중지되고 `(Pdb)` 프롬프트가 표시됩니다. 다음과 같은 명령을 입력할 수 있습니다.
-   `p a` (or `print(a)`): Print the value of variable `a`.
    `p a` (또는 `print(a)`): 변수 `a`의 값을 인쇄합니다.
-   `n` (next): Step to the next line.
    `n` (다음): 다음 줄로 이동합니다.
-   `c` (continue): Continue execution until the next breakpoint.
    `c` (계속): 다음 중단점까지 실행을 계속합니다.
-   `q` (quit): Exit the debugger.
    `q` (종료): 디버거를 종료합니다.

---

## 3. `git bisect`: The Bug Time Machine
## 3. `git bisect`: 버그 타임머신

What if a bug was introduced sometime in the last 100 commits, and you have no idea where? `git bisect` is a magical tool that helps you find the exact commit that introduced the bug.
지난 100개 커밋 중 언젠가 버그가 발생했는데 어디서 발생했는지 전혀 모른다면 어떻게 될까요? `git bisect`는 버그를 유발한 정확한 커밋을 찾는 데 도움이 되는 마법 같은 도구입니다.

**How it works:**
**작동 방식:**
It performs a binary search on your commit history. You tell it a "good" commit (where the bug didn't exist) and a "bad" commit (where it does). It then checks out a commit in the middle and asks you if it's good or bad. By repeating this process, it quickly narrows down the search space.
커밋 기록에서 이진 검색을 수행합니다. "좋은" 커밋(버그가 없었던 곳)과 "나쁜" 커밋(버그가 있는 곳)을 알려줍니다. 그런 다음 중간에 있는 커밋을 체크아웃하고 좋은지 나쁜지 묻습니다. 이 과정을 반복함으로써 검색 공간을 빠르게 좁힙니다.

**The Workflow:**
**워크플로:**

```bash
# 1. Start the bisect process
# 1. 이분법 프로세스 시작
git bisect start

# 2. Tell it the current commit is bad
# 2. 현재 커밋이 나쁘다고 알립니다.
git bisect bad HEAD

# 3. Tell it a commit from a week ago was good
# 3. 일주일 전의 커밋이 좋았다고 알립니다.
git bisect good <commit_hash_from_a_week_ago>

# Git checks out a commit in the middle. Now, test your code.
# Git이 중간에 있는 커밋을 체크아웃합니다. 이제 코드를 테스트하십시오.
# Run your app or your failing test.
# 앱 또는 실패하는 테스트를 실행하십시오.

# 4. If the bug is still present, tell git:
# 4. 버그가 여전히 있으면 git에 알립니다.
git bisect bad

# 5. If the bug is gone, tell git:
# 5. 버그가 사라지면 git에 알립니다.
git bisect good

# Repeat step 4 or 5 until Git tells you:
# 4단계 또는 5단계를 Git이 알려줄 때까지 반복합니다.
# "<hash> is the first bad commit"
# "<해시>가 첫 번째 나쁜 커밋입니다"

# 6. Clean up when you're done
# 6. 완료되면 정리합니다.
git bisect reset
```

This tool is incredibly powerful for finding regressions. By combining a systematic approach with powerful tools, a Vibe Coder turns the frustrating art of debugging into an efficient, predictable science.
이 도구는 회귀를 찾는 데 매우 강력합니다. 체계적인 접근 방식과 강력한 도구를 결합함으로써 Vibe 코더는 답답한 디버깅 기술을 효율적이고 예측 가능한 과학으로 바꿉니다.