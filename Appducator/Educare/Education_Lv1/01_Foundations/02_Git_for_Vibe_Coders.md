# 01.02 - Git for Vibe Coders: Beyond the Basics
# 01.02 - Vibe 코더를 위한 Git: 기본을 넘어서

Git is more than just a tool for saving code. It's a system for structuring your development process, collaborating safely, and maintaining a clean, understandable project history. A Vibe Coder uses Git with intention.
Git은 단순히 코드를 저장하는 도구 그 이상입니다. 개발 프로세스를 구조화하고, 안전하게 협업하며, 깨끗하고 이해하기 쉬운 프로젝트 히스토리를 유지하기 위한 시스템입니다. Vibe 코더는 의도를 가지고 Git을 사용합니다.

## Core Concepts
## 핵심 개념

1.  **Atomic Commits**: Each commit should represent a single, complete, logical change.
    **원자적 커밋**: 각 커밋은 단일하고 완전하며 논리적인 변경 사항을 나타내야 합니다.
2.  **Meaningful History**: Your commit history should read like a story of the project's development.
    **의미 있는 히스토리**: 커밋 히스토리는 프로젝트 개발 과정에 대한 이야기처럼 읽혀야 합니다.
3.  **Branching Strategy**: A clear strategy for managing features, releases, and hotfixes.
    **브랜칭 전략**: 기능, 릴리스, 핫픽스를 관리하기 위한 명확한 전략.
4.  **Code Review**: Using Pull/Merge Requests as a quality gate.
    **코드 리뷰**: Pull/Merge Request를 품질 게이트로 사용.

---

## 1. Crafting Atomic Commits
## 1. 원자적 커밋 만들기

A commit should be the smallest change that leaves the codebase in a consistent state.
커밋은 코드베이스를 일관된 상태로 남기는 가장 작은 변경 단위여야 합니다.

-   **Good**: "Add user authentication endpoint" (includes model, service, route, and tests).
    **좋은 예**: "사용자 인증 엔드포인트 추가" (모델, 서비스, 라우트, 테스트 포함).
-   **Bad**: "Fix typo" followed by "Add login route" followed by "Add user model". These should be one commit.
    **나쁜 예**: "오타 수정" 다음에 "로그인 라우트 추가" 다음에 "사용자 모델 추가". 이것들은 하나의 커밋이어야 합니다.
-   **Bad**: "Implement user profile and payment processing". This is too large; it should be at least two separate commits.
    **나쁜 예**: "사용자 프로필 및 결제 처리 구현". 이것은 너무 큽니다. 최소 두 개의 별도 커밋으로 나눠야 합니다.

### The `git add -p` (Patch) Command
### `git add -p` (패치) 명령어

This is a Vibe Coder's secret weapon. Instead of `git add .`, use `git add -p` to review and stage changes hunk by hunk.
이것은 Vibe 코더의 비밀 무기입니다. `git add .` 대신 `git add -p`를 사용하여 변경 사항을 덩어리(hunk)별로 검토하고 스테이징하세요.

```bash
git add -p src/main.py
```

Git will show you a block of changes and ask what to do:
Git은 변경된 블록을 보여주고 무엇을 할지 묻습니다:
-   `y`: Stage this hunk.
    `y`: 이 덩어리를 스테이징합니다.
-   `n`: Do not stage this hunk.
    `n`: 이 덩어리를 스테이징하지 않습니다.
-   `s`: Split this hunk into smaller hunks (if possible).
    `s`: 이 덩어리를 더 작은 덩어리로 나눕니다 (가능한 경우).
-   `e`: Edit the hunk manually (for advanced users).
    `e`: 덩어리를 수동으로 편집합니다 (고급 사용자용).
-   `q`: Quit.
    `q`: 종료합니다.

This practice forces you to review your own code and helps you build atomic commits by staging only related changes.
이 관행은 자신의 코드를 검토하게 만들고, 관련된 변경 사항만 스테이징하여 원자적 커밋을 만드는 데 도움을 줍니다.

### Writing Great Commit Messages
### 훌륭한 커밋 메시지 작성하기

A well-written commit message is crucial for a readable history. Follow the "50/72" rule.
잘 작성된 커밋 메시지는 읽기 쉬운 히스토리에 매우 중요합니다. "50/72" 규칙을 따르세요.

-   **Subject Line (max 50 chars)**:
    **제목 (최대 50자)**:
    -   Use the imperative mood (e.g., "Add," "Fix," "Refactor," not "Added," "Fixes").
        명령형을 사용하세요 (예: "Added", "Fixes"가 아닌 "Add", "Fix", "Refactor").
    -   Capitalize the first letter.
        첫 글자를 대문자로 작성하세요.
    -   Do not end with a period.
        마침표로 끝내지 마세요.
    -   Example: `feat: Add user login endpoint`
        예시: `feat: 사용자 로그인 엔드포인트 추가`

-   **Body (optional, wrapped at 72 chars)**:
    **본문 (선택 사항, 72자에서 줄 바꿈)**:
    -   Separated from the subject by a blank line.
        제목과 한 줄 띄워서 구분합니다.
    -   Explain the "what" and "why," not the "how." The code shows the "how."
        "어떻게"가 아닌 "무엇을"과 "왜"를 설명하세요. "어떻게"는 코드가 보여줍니다.
    -   Reference issue numbers (e.g., "Resolves #42").
        이슈 번호를 참조하세요 (예: "Resolves #42").

**Good Commit Message Template:**
**좋은 커밋 메시지 템플릿:**

```
feat: Implement password reset functionality

Adds the /request-reset and /reset-password endpoints.
This allows users who have forgotten their password to securely
reset it via a token sent to their email address.

Resolves: #23
```

**Conventional Commits**: For extra structure, use prefixes like `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`. This is highly recommended for automated versioning and changelog generation.
**Conventional Commits**: 추가적인 구조를 위해 `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`와 같은 접두사를 사용하세요. 이는 자동화된 버전 관리 및 변경 로그 생성에 강력히 권장됩니다.

---

## 2. A Simple and Effective Branching Strategy: `main` + Feature Branches
## 2. 간단하고 효과적인 브랜칭 전략: `main` + 기능 브랜치

For solo developers or small teams, a complex GitFlow is often overkill. A simpler approach is more effective.
개인 개발자나 소규모 팀에게 복잡한 GitFlow는 종종 과합니다. 더 간단한 접근 방식이 더 효과적입니다.

1.  **`main` Branch**:
    **`main` 브랜치**:
    -   Always represents the stable, production-ready state of the code.
        항상 안정적이고 프로덕션 준비가 된 코드 상태를 나타냅니다.
    -   You should be able to deploy from `main` at any time.
        언제든지 `main`에서 배포할 수 있어야 합니다.
    -   Direct commits to `main` are forbidden. Changes are only merged via Pull Requests.
        `main`에 직접 커밋하는 것은 금지됩니다. 변경 사항은 Pull Request를 통해서만 병합됩니다.

2.  **Feature Branches**:
    **기능 브랜치**:
    -   Create a new branch for every new feature, bugfix, or chore.
        모든 새로운 기능, 버그 수정 또는 잡다한 작업에 대해 새 브랜치를 만듭니다.
    -   Branch off from the latest `main`.
        최신 `main`에서 브랜치를 나눕니다.
    -   Name them descriptively, e.g., `feat/user-auth`, `fix/parsing-error`, `chore/update-deps`.
        설명적으로 이름을 지정하세요 (예: `feat/user-auth`, `fix/parsing-error`, `chore/update-deps`).

### The Workflow
### 워크플로우

```bash
# 1. Start a new feature, making sure your main is up-to-date
# 1. 새 기능 작업을 시작하기 전에 main 브랜치를 최신 상태로 유지합니다.
git checkout main
git pull origin main

# 2. Create a new feature branch
# 2. 새 기능 브랜치를 생성합니다.
git checkout -b feat/new-cool-feature

# 3. Work on your feature, making atomic commits
# 3. 기능 작업을 하며 원자적 커밋을 만듭니다.
# ... write code, run tests ...
# ... 코드 작성, 테스트 실행 ...
git add -p
git commit -m "feat: Add core logic for cool feature"
# ... write more code, run tests ...
# ... 추가 코드 작성, 테스트 실행 ...
git add -p
git commit -m "feat: Add tests for cool feature"

# 4. Push your branch to the remote repository
# 4. 원격 저장소에 브랜치를 푸시합니다.
git push origin feat/new-cool-feature

# 5. Open a Pull Request (PR) on GitHub/GitLab
# 5. GitHub/GitLab에서 Pull Request(PR)를 엽니다.
#    - The PR compares your feature branch to `main`.
#    - PR은 기능 브랜치와 `main` 브랜치를 비교합니다.
#    - Your CI pipeline (tests, linting) should run automatically.
#    - CI 파이프라인(테스트, 린팅)이 자동으로 실행되어야 합니다.
#    - Review your own code one last time. If you have a team, assign a reviewer.
#    - 마지막으로 자신의 코드를 검토합니다. 팀이 있다면 리뷰어를 지정합니다.

# 6. After review and all checks pass, merge the PR
# 6. 검토와 모든 검사가 통과된 후 PR을 병합합니다.
#    - Use a "Squash and Merge" or "Rebase and Merge" strategy if possible.
#    - 가능하다면 "Squash and Merge" 또는 "Rebase and Merge" 전략을 사용합니다.
#      - **Squash and Merge**: Combines all of your feature branch's commits into a single, clean commit on `main`. This keeps the `main` branch history very tidy. Highly recommended for Vibe Coders.
#      - **Squash and Merge**: 기능 브랜치의 모든 커밋을 `main` 브랜치에 하나의 깨끗한 커밋으로 합칩니다. 이는 `main` 브랜치 히스토리를 매우 깔끔하게 유지합니다. Vibe 코더에게 강력히 추천됩니다.
#      - **Rebase and Merge**: Replays your feature branch's commits on top of the latest `main`, creating a linear history. Cleaner than a standard merge, but can be more complex.
#      - **Rebase and Merge**: 기능 브랜치의 커밋들을 최신 `main` 위에 다시 적용하여 선형 히스토리를 만듭니다. 일반적인 병합보다 깨끗하지만 더 복잡할 수 있습니다.

# 7. Clean up
# 7. 정리
git checkout main
git pull origin main # Update your local main
git branch -d feat/new-cool-feature # Delete the local feature branch
```

---

## 3. Interactive Rebase: Your Time Machine
## 3. 대화형 리베이스: 당신의 타임머신

`git rebase -i` is one of Git's most powerful features. It allows you to rewrite the history of your *local, unpushed* commits. This is perfect for cleaning up your work *before* you open a Pull Request.
`git rebase -i`는 Git의 가장 강력한 기능 중 하나입니다. *푸시하지 않은 로컬* 커밋의 히스토리를 다시 작성할 수 있게 해줍니다. Pull Request를 열기 *전에* 작업을 정리하기에 완벽합니다.

Imagine your local history looks messy:
로컬 히스토리가 지저분하다고 상상해보세요:
-   `commit 1`: "feat: Start user model"
-   `commit 2`: "oops, fix typo"
-   `commit 3`: "refactor: Clean up user model"
-   `commit 4`: "WIP"

You can clean this up before pushing.
푸시하기 전에 이것을 정리할 수 있습니다.

```bash
# Rebase the last 4 commits
# 마지막 4개의 커밋을 리베이스합니다.
git rebase -i HEAD~4
```

This opens an editor with a list of your commits:
그러면 다음과 같이 커밋 목록이 있는 편집기가 열립니다:

```
pick <hash1> feat: Start user model
pick <hash2> oops, fix typo
pick <hash3> refactor: Clean up user model
pick <hash4> WIP
```

You can change `pick` to other commands:
`pick`을 다른 명령어로 변경할 수 있습니다:
-   `r` or `reword`: Keep the commit, but change the message.
    `r` 또는 `reword`: 커밋은 유지하되 메시지를 변경합니다.
-   `s` or `squash`: Combine this commit with the one above it.
    `s` 또는 `squash`: 이 커밋을 바로 위의 커밋과 합칩니다.
-   `f` or `fixup`: Like `squash`, but discard this commit's message.
    `f` 또는 `fixup`: `squash`와 같지만 이 커밋의 메시지는 버립니다.
-   `d` or `drop`: Delete the commit entirely.
    `d` 또는 `drop`: 커밋을 완전히 삭제합니다.

To clean up our example, you could change it to:
예제를 정리하기 위해 다음과 같이 변경할 수 있습니다:

```
pick <hash1> feat: Start user model
f <hash2> oops, fix typo
f <hash3> refactor: Clean up user model
d <hash4> WIP
```

Then, you'll be prompted to write a new, single commit message for the combined commits. You can reword the first one to be "feat: Add user model".
그러면 합쳐진 커밋들에 대한 새로운 단일 커밋 메시지를 작성하라는 메시지가 표시됩니다. 첫 번째 커밋 메시지를 "feat: Add user model"로 수정할 수 있습니다.

**Golden Rule of Rebasing**: Never rebase commits that have already been pushed and are being used by others. It rewrites history, which can cause major problems for collaborators. It's safe to rebase your own local feature branch before you've shared it.
**리베이스의 황금률**: 이미 푸시되어 다른 사람들이 사용하고 있는 커밋은 절대 리베이스하지 마세요. 히스토리를 다시 작성하여 협업자들에게 큰 문제를 일으킬 수 있습니다. 공유하기 전의 자신의 로컬 기능 브랜치를 리베이스하는 것은 안전합니다.

By mastering this workflow, you treat your project's history as a first-class citizen. This discipline pays huge dividends in maintainability and makes it easier to find bugs (`git bisect`), understand features, and onboard new developers (even if that's just your future self).
이 워크플로우를 마스터함으로써 프로젝트의 히스토리를 일급 시민으로 취급하게 됩니다. 이러한 원칙은 유지보수성에 큰 이점을 제공하며, 버그를 찾고(`git bisect`), 기능을 이해하고, 새로운 개발자를 온보딩하는 것(미래의 자신 포함)을 더 쉽게 만듭니다.