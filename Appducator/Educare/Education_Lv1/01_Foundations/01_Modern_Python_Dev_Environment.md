# 01.01 - Modern Python Development Environment
# 01.01 - 현대적인 파이썬 개발 환경

This guide covers setting up a robust, modern, and efficient development environment for Python projects. This is the bedrock of Vibe Coding—a clean, reproducible, and automated setup frees you to focus on building.
이 가이드는 파이썬 프로젝트를 위한 강력하고 현대적이며 효율적인 개발 환경 설정에 대해 다룹니다. 이것이 바로 Vibe Coding의 기반입니다. 깨끗하고 재현 가능하며 자동화된 설정은 여러분이 개발에만 집중할 수 있도록 해줍니다.

## Core Concepts
## 핵심 개념

1.  **Virtual Environments**: Isolate project dependencies to avoid conflicts.
    **가상 환경**: 프로젝트 의존성을 격리하여 충돌을 방지합니다.
2.  **Dependency Management**: Define, install, and lock dependencies for reproducibility.
    **의존성 관리**: 재현성을 위해 의존성을 정의, 설치 및 고정합니다.
3.  **Code Formatting**: Automatically enforce a consistent code style.
    **코드 포매팅**: 일관된 코드 스타일을 자동으로 적용합니다.
4.  **Linting**: Statically analyze code to find errors, bugs, and stylistic issues.
    **린팅**: 코드를 정적으로 분석하여 오류, 버그 및 스타일 문제를 찾습니다.
5.  **Type Checking**: Use type hints to catch errors before runtime and improve code clarity.
    **타입 검사**: 타입 힌트를 사용하여 런타임 전에 오류를 잡고 코드 명확성을 향상시킵니다.
6.  **Task Running**: Automate common development tasks (e.g., running tests, formatting).
    **작업 실행**: 일반적인 개발 작업(예: 테스트 실행, 포매팅)을 자동화합니다.

## Recommended Toolchain
## 추천 도구 모음

| Category                | Tool                                                                 | Why it's essential for Vibe Coding                               |
| ----------------------- | -------------------------------------------------------------------- | ---------------------------------------------------------------- |
| **Virtual Environment** | `venv` (built-in)                                                    | Standard, reliable, and universally available. <br> 표준적이고 신뢰할 수 있으며 어디서나 사용할 수 있습니다.                   |
| **Dependency Manager**  | `pip` + `pip-tools` (for `pip-compile`)                              | `pip` is the standard. `pip-tools` adds crucial dependency locking. <br> `pip`는 표준입니다. `pip-tools`는 중요한 의존성 고정 기능을 추가합니다. <br><br>**⚡️ The Future is `uv`**: For even faster performance, `uv` (from the makers of `ruff`) is an emerging all-in-one tool that can replace `pip`, `pip-tools`, and `venv`. |
| **Code Formatter**      | `black`                                                              | Uncompromisingly enforces a single, clean style. No more debates. <br> 타협 없이 단일하고 깨끗한 스타일을 강제합니다. 더 이상의 논쟁은 없습니다. |
| **Linter**              | `ruff`                                                               | Extremely fast (written in Rust). Combines many tools (flake8, isort). <br> 매우 빠릅니다(Rust로 작성됨). 많은 도구(flake8, isort)를 결합합니다. |
| **Type Checker**        | `mypy`                                                               | The de-facto standard for static type checking in Python. <br> 파이썬의 정적 타입 검사를 위한 사실상의 표준입니다.       |
| **Task Runner**         | `Makefile` or `pyproject.toml [tool.scripts]`                        | Simple, effective automation for CLI commands. <br> CLI 명령을 위한 간단하고 효과적인 자동화입니다.                  |
| **Project Config**      | `pyproject.toml`                                                     | The modern, standardized way to configure Python projects. <br> 파이썬 프로젝트를 구성하는 현대적이고 표준화된 방법입니다.      |

---

## Step-by-Step Setup Guide
## 단계별 설정 가이드

Let's set up a new project from scratch.
처음부터 새 프로젝트를 설정해 보겠습니다.

### 1. Project Structure
### 1. 프로젝트 구조

Create a standard project layout.
표준 프로젝트 레이아웃을 만듭니다.

```bash
mkdir my-vibe-project
cd my-vibe-project
mkdir src
touch src/main.py
touch .gitignore
```

A good `.gitignore` to start with:
시작하기 좋은 `.gitignore` 파일 예시입니다.
```
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.env

# IDE / Editor
.vscode/
.idea/
*.swp
```

## 2. 가상 환경: 프로젝트별 놀이터

프로젝트를 진행하다 보면 각기 다른 버전의 라이브러리가 필요할 때가 많습니다. A 프로젝트는 `requests` 2.25.0 버전이, B 프로젝트는 `requests` 2.28.0 버전이 필요할 수 있습니다. 이때 시스템에 하나의 버전만 설치되어 있다면 충돌이 발생합니다.

**가상 환경(Virtual Environment)**은 프로젝트별로 독립된 파이썬 환경을 만들어 이러한 충돌을 방지합니다.

### 가상 환경 생성 및 활성화

Python 3.3 이상부터는 `venv` 모듈이 내장되어 있어 쉽게 생성할 수 있습니다.

```bash
# .venv라는 이름의 가상 환경 생성
$ python3 -m venv .venv

# 가상 환경 활성화 (Linux/macOS)
$ source .venv/bin/activate

# 활성화되면 프롬프트 앞에 (.venv)가 붙습니다.
(.venv) $ 
```

이제 이 안에서 설치하는 모든 패키지는 시스템 전체가 아닌 `.venv` 폴더 안에만 설치됩니다.

> **비활성화:** `deactivate` 명령어를 입력하면 가상 환경에서 빠져나옵니다.

## 3. 의존성 관리: `pip`와 `requirements.txt`

프로젝트를 다른 사람과 공유하거나 다른 컴퓨터에서 작업하려면, "이 프로젝트는 이러이러한 라이브러리들이 필요해"라고 알려줘야 합니다. 이를 **의존성 관리(Dependency Management)**라고 합니다.

### `pip`: 파이썬 패키지 설치 도구

`pip`는 Python의 공식 패키지 관리자로, 필요한 라이브러리를 손쉽게 설치, 업그레이드, 삭제할 수 있게 해줍니다.

```bash
# 가상 환경이 활성화된 상태에서 requests 라이브러리 설치
(.venv) $ pip install requests

# 설치된 패키지 목록 확인
(.venv) $ pip list
```

### `requirements.txt`: 의존성 목록 파일

`pip freeze` 명령어를 사용하면 현재 환경에 설치된 모든 패키지와 그 버전을 `requirements.txt` 형식으로 출력할 수 있습니다. 이 파일을 프로젝트에 포함시키면, 다른 사람들이나 미래의 내가 어떤 라이브러리를 설치해야 하는지 정확히 알 수 있습니다.

```bash
# 현재 설치된 패키지 목록을 requirements.txt 파일로 저장
(.venv) $ pip freeze > requirements.txt
```

`requirements.txt` 파일 내용은 다음과 같습니다.
```
certifi==2023.7.22
charset-normalizer==3.3.2
idna==3.6
requests==2.31.0
urllib3==2.1.0
```

### 파일로부터 의존성 설치하기

다른 사람이 만든 프로젝트를 실행하거나, 내가 만든 프로젝트를 다른 환경에 설정할 때 `requirements.txt` 파일을 사용해 모든 의존성을 한 번에 설치할 수 있습니다.

```bash
# 새로운 환경에서 가상 환경을 만들고 활성화한 후
(.venv) $ pip install -r requirements.txt
```

이 과정을 통해 모든 팀원이 동일한 버전의 라이브러리를 사용하는 동일한 개발 환경을 갖게 되어 "제 컴퓨터에서는 됐는데..." 하는 문제를 방지할 수 있습니다.

## 4. 코드 포매터와 린터: 깔끔하고 일관된 코드 유지

- **코드 포매터 (Code Formatter):** `Black`, `isort` 등. 코드를 정해진 스타일 규칙에 맞게 자동으로 정리해줍니다.
- **코드 린터 (Code Linter):** `Ruff`, `Flake8` 등. 코드 스타일 위반뿐만 아니라, 잠재적인 버그나 안티 패턴을 찾아 경고해줍니다.

### 4. Install and Manage Dependencies with `pip-tools`
### 4. `pip-tools`로 의존성 설치 및 관리하기

Instead of a simple `requirements.txt`, we'll use a two-file system for better control.
단순한 `requirements.txt` 대신, 더 나은 제어를 위해 두 개의 파일 시스템을 사용합니다.

1.  **`requirements.in`**: For your direct, high-level dependencies.
    **`requirements.in`**: 직접적인 상위 수준 의존성을 위한 파일입니다.
2.  **`requirements.txt`**: The "lock file", generated by `pip-compile`, with pinned versions of all dependencies and sub-dependencies.
    **`requirements.txt`**: `pip-compile`에 의해 생성된 "잠금 파일"로, 모든 의존성 및 하위 의존성의 고정된 버전을 포함합니다.

First, install `pip-tools`:
먼저 `pip-tools`를 설치합니다.
```bash
pip install pip-tools
```

Create `requirements.in` for your main dependencies and `dev-requirements.in` for development tools.
주요 의존성을 위한 `requirements.in`과 개발 도구를 위한 `dev-requirements.in`을 만듭니다.

**`requirements.in`**:
```
# Application dependencies
fastapi
uvicorn[standard]
pydantic
```

**`dev-requirements.in`**:
```
# Development tools
-c requirements.txt  # Constrain dev tools to versions used by the app
black
ruff
mypy
pytest
```

Now, compile them:
이제 컴파일합니다.
```bash
pip-compile requirements.in -o requirements.txt
pip-compile dev-requirements.in -o dev-requirements.txt
```

You'll see `requirements.txt` and `dev-requirements.txt` are generated with pinned versions. This is **critical for reproducibility**.
`requirements.txt`와 `dev-requirements.txt`가 고정된 버전으로 생성된 것을 볼 수 있습니다. 이것은 **재현성에 매우 중요합니다**.

Install everything:
모든 것을 설치합니다.
```bash
pip install -r requirements.txt
pip install -r dev-requirements.txt
```

### 5. Automate with a `Makefile`
### 5. `Makefile`로 자동화하기

A `Makefile` simplifies running common commands. Create a file named `Makefile`.
`Makefile`은 일반적인 명령어 실행을 단순화합니다. `Makefile`이라는 이름의 파일을 만듭니다.

```makefile
.PHONY: help install format lint check test

# Colors for output
GREEN := [0;32m
RESET := [0m

help:
	@echo "Available commands:"
	@echo "  ${GREEN}install${RESET} - Install dependencies"
	@echo "  ${GREEN}format${RESET}  - Format code with black and ruff"
	@echo "  ${GREEN}lint${RESET}    - Lint code with ruff"
	@echo "  ${GREEN}check${RESET}   - Run static type checking with mypy"
	@echo "  ${GREEN}test${RESET}    - Run tests with pytest"
	@echo "  ${GREEN}all${RESET}     - Run format, lint, check, and test"

install:
	@echo "--> Installing dependencies..."
	@pip install -r requirements.txt
	@pip install -r dev-requirements.txt

format:
	@echo "--> Formatting code..."
	@ruff --fix .
	@black .

lint:
	@echo "--> Linting code..."
	@ruff .

check:
	@echo "--> Running type checks..."
	@mypy src

test:
	@echo "--> Running tests..."
	@pytest

all: format lint check test
```

Now you can simply run `make format`, `make lint`, etc.
이제 `make format`, `make lint` 등을 간단히 실행할 수 있습니다.

## Vibe Coding Workflow
## Vibe Coding 워크플로우

Your daily workflow becomes a simple, powerful loop:
여러분의 일일 워크플로우는 간단하고 강력한 루프가 됩니다.

1.  **Code**: Write your feature in `src/`.
    **코드**: `src/`에 기능을 작성합니다.
2.  **Test**: Write a corresponding test.
    **테스트**: 해당하는 테스트를 작성합니다.
3.  **Automate Checks**: Run `make all`. This command will format, lint, type-check, and run tests in one go.
    **자동화된 검사**: `make all`을 실행합니다. 이 명령어는 포매팅, 린팅, 타입 검사, 테스트 실행을 한 번에 수행합니다.
4.  **Commit**: Once all checks pass, commit your code.
    **커밋**: 모든 검사를 통과하면 코드를 커밋합니다.
5.  **Update Dependencies**:
    **의존성 업데이트**:
    -   Add a new package to `requirements.in`.
        `requirements.in`에 새 패키지를 추가합니다.
    -   Run `pip-compile requirements.in -o requirements.txt`.
        `pip-compile requirements.in -o requirements.txt`를 실행합니다.
    -   Run `pip install -r requirements.txt`.
        `pip install -r requirements.txt`를 실행합니다.
    -   Commit the updated `.in` and `.txt` files.
        업데이트된 `.in`과 `.txt` 파일을 커밋합니다.

This disciplined approach minimizes bugs, ensures consistency, and makes your project a joy to work on, whether solo or with a team. It is the foundation upon which scalable, reliable systems are built.
이러한 규칙적인 접근 방식은 버그를 최소화하고 일관성을 보장하며, 혼자 작업하든 팀과 함께 작업하든 프로젝트를 즐겁게 만듭니다. 이것이 확장 가능하고 신뢰할 수 있는 시스템이 구축되는 기반입니다.