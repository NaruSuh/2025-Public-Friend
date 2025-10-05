# 01 - Foundations - Lv.2: Advanced Python and Tooling
# 01 - 파운데이션 - Lv.2: 고급 파이썬과 도구 활용

You've mastered the basics of a modern development environment. Now, it's time to deepen your understanding of Python itself and adopt more powerful tooling to manage complexity.
현대적인 개발 환경의 기초를 이미 익혔다면, 이제는 파이썬 언어 자체에 대한 이해를 더 깊게 하고 복잡도를 관리할 수 있는 더 강력한 도구들을 도입할 차례입니다.

## Before You Begin
## 시작하기 전에
-   Revisit Level 1 modules `01_Modern_Python_Dev_Environment` and `02_Git_for_Vibe_Coders` to make sure virtual environments, pip-tools, and Git workflows feel automatic.
-   레벨 1의 `01_Modern_Python_Dev_Environment`와 `02_Git_for_Vibe_Coders` 모듈을 다시 살펴보면서 가상 환경, pip-tools, Git 워크플로가 몸에 익었는지 확인하세요.
-   Skim `Education/02_Backend_Development/01_FastAPI_Robust_APIs.md` so the examples here can build directly on API routing concepts without re-explaining them.
-   `Education/02_Backend_Development/01_FastAPI_Robust_APIs.md`를 훑어보아 API 라우팅 개념을 다시 복기하면, 여기의 예시를 바로 적용할 수 있습니다.
-   Set up a scratch repo or branch where you can experiment freely; each section below includes a lightweight hands-on exercise.
-   자유롭게 실험할 수 있는 스크래치 저장소나 브랜치를 마련하세요. 아래 각 섹션에는 가볍게 따라 할 수 있는 실습 과제가 포함되어 있습니다.

## Level 2 Upgrade Goals
## 레벨 2 업그레이드 목표
1.  **Work fluently with Python’s data model** so language features like decorators and context managers feel approachable, not “magic.”
1.  **파이썬 데이터 모델을 자연스럽게 다루기** – 데코레이터나 컨텍스트 매니저 같은 언어 기능을 “마법”이 아닌 친숙한 도구로 느끼게 합니다.
2.  **Adopt tooling that scales with multi-service projects** (Poetry, monorepos) without re-learning dependency basics from Level 1.
2.  **멀티 서비스 프로젝트에도 확장되는 도구 체계 구축** – 레벨 1에서 배운 의존성 관리 기초를 반복하지 않고도 Poetry나 모노레포 전략을 활용합니다.
3.  **Practice micro-projects** that force you to apply the new ideas immediately, reinforcing them for a future Vibe product.
3.  **마이크로 프로젝트로 즉시 실습하기** – 새로운 개념을 바로 적용해보고 향후 Vibe 제품에 녹여낼 수 있도록 다집니다.

## Core Concepts
## 핵심 개념

1.  **Advanced Python Features**: Move beyond basic syntax to understand the "why" behind Python's design, including generators, context managers, decorators, and the data model.
1.  **고급 파이썬 기능**: 제너레이터, 컨텍스트 매니저, 데코레이터, 데이터 모델 등 파이썬 설계의 배경을 이해하여 단순 문법을 넘어섭니다.
2.  **Dependency Management at Scale**: Transition from `pip-tools` to a fully integrated project management tool like `Poetry` or `PDM`.
2.  **확장 가능한 의존성 관리**: `pip-tools`에서 나아가 `Poetry`나 `PDM`처럼 통합된 프로젝트 관리 도구로 전환합니다.
3.  **Monorepo Strategy**: Understand how to manage multiple related projects within a single repository for streamlined development.
3.  **모노레포 전략**: 여러 관련 프로젝트를 하나의 저장소에서 관리하여 개발 흐름을 단순화합니다.

---

## 1. Deeper into Python: The Language's "Magic"
## 1. 파이썬의 “마법”을 더 깊이 이해하기

To write truly "Pythonic" and efficient code, you need to understand the protocols that underpin the language.
진정으로 “파이썬다운” 효율적인 코드를 작성하려면, 언어를 지탱하는 프로토콜을 이해해야 합니다.

### Generators and Coroutines
### 제너레이터와 코루틴
You've used `asyncio`, but do you understand the generator foundations it's built upon?
`asyncio`를 사용해봤다면, 그 기반이 되는 제너레이터 개념도 이해하고 있나요?
-   **`yield` vs. `return`**: A function with `yield` becomes a generator, producing a sequence of values over time without holding them all in memory.
-   **`yield`와 `return` 비교**: `yield`를 사용하는 함수는 제너레이터가 되어 모든 값을 메모리에 유지하지 않고도 순차적으로 값을 생성합니다.
-   **Generator Expressions**: A concise way to create generators: `(i*i for i in range(1000))` vs a list comprehension `[i*i for i in range(1000)]`. The former is memory-efficient.
-   **제너레이터 표현식**: `(i*i for i in range(1000))`처럼 간결하게 제너레이터를 만드는 방법으로, `[i*i for i in range(1000)]` 리스트 컴프리헨션보다 메모리를 절약합니다.
-   **`yield from`**: A way to chain generators, which is conceptually similar to how `await` delegates control in `asyncio`.
-   **`yield from`**: 제너레이터를 이어 붙이는 방법으로, `asyncio`에서 `await`가 제어를 위임하는 방식과 개념적으로 비슷합니다.

**Practice:** rewrite one of your Streamlit data loaders from Level 1 so it streams rows from disk using a generator. Measure memory usage with `sys.getsizeof` to see the difference.
**실습:** 레벨 1에서 만든 Streamlit 데이터 로더 중 하나를 제너레이터로 바꿔 디스크에서 행을 스트리밍하도록 만들고, `sys.getsizeof`로 메모리 사용량 차이를 측정해 보세요.

### Context Managers (`with` statement)
### 컨텍스트 매니저 (`with` 구문)
You use `with open(...)` all the time. How does it work? By implementing the context management protocol.
`with open(...)` 구문을 자주 사용하지만, 이것이 어떻게 동작하는지 알고 있나요? 컨텍스트 관리 프로토콜을 구현하기 때문입니다.
-   **`__enter__` and `__exit__`**: Any class with these two methods can be used in a `with` statement. `__enter__` sets up the context (e.g., opens the file), and `__exit__` guarantees teardown (e.g., closes the file), even if errors occur.
-   **`__enter__`와 `__exit__`**: 이 두 메서드를 가진 클래스는 `with` 구문에서 사용할 수 있으며, `__enter__`는 컨텍스트를 설정하고 `__exit__`는 오류가 발생해도 정리 작업을 보장합니다.
-   **`@contextmanager` decorator**: A generator-based way to create a simple context manager from the `contextlib` module.
-   **`@contextmanager` 데코레이터**: `contextlib` 모듈에서 제너레이터 기반으로 간단한 컨텍스트 매니저를 만드는 방법입니다.

```python
from contextlib import contextmanager
import time

@contextmanager
def timer(label: str):
    start_time = time.time()
    try:
        yield
    finally:
        end_time = time.time()
        print(f"{label} took {end_time - start_time:.3f} seconds")

with timer("My Code Block"):
    # some long-running code
    time.sleep(1)
```

**Practice:** Create a context manager that acquires a temporary directory, writes a file, and cleans up automatically. Use it to wrap an existing ETL step from your project.
**실습:** 임시 디렉터리를 생성하고 파일을 작성한 뒤 자동으로 정리하는 컨텍스트 매니저를 만들어보세요. 프로젝트의 기존 ETL 단계를 감싸는 데 활용해 봅니다.

### Decorators
### 데코레이터
A decorator is a function that takes another function and extends its behavior without explicitly modifying it.
데코레이터는 다른 함수를 인자로 받아 원본 코드를 직접 수정하지 않고 동작을 확장하는 함수입니다.
-   **Function as First-Class Objects**: In Python, functions can be passed as arguments, returned from other functions, and assigned to variables. This is what makes decorators possible.
-   **일급 함수**: 파이썬에서는 함수가 인자로 전달되고, 반환되며, 변수에 할당될 수 있기 때문에 데코레이터가 가능합니다.
-   **`@` syntax**: Syntactic sugar for `my_function = my_decorator(my_function)`.
-   **`@` 구문**: `my_function = my_decorator(my_function)`을 더 간결하게 표현한 문법 설탕입니다.
-   **`functools.wraps`**: A helper decorator that ensures the decorated function retains its original name, docstring, etc.
-   **`functools.wraps`**: 데코레이터가 적용된 함수의 이름, 독스트링 등을 보존해 주는 도우미 데코레이터입니다.

```python
import functools

def log_function_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Calling function '{func.__name__}'...")
        result = func(*args, **kwargs)
        print(f"Function '{func.__name__}' finished.")
        return result
    return wrapper

@log_function_call
def greet(name):
    """A simple greeting function."""
    print(f"Hello, {name}!")

greet("Naru")
```

**Practice:** Decorate one of your FastAPI dependency functions to add structured logging. Compare this approach to duplicating logging statements inside every endpoint.
**실습:** FastAPI 의존성 함수 하나에 데코레이터를 적용해 구조화된 로깅을 추가하고, 각 엔드포인트마다 로깅 코드를 반복하는 방식과 비교해 보세요.

---

## 2. Next-Level Dependency Management: Poetry
## 2. 차세대 의존성 관리: Poetry

While `pip-tools` is great, tools like `Poetry` offer a more integrated experience for managing dependencies, packaging, and publishing your project.
`pip-tools`도 훌륭하지만, `Poetry` 같은 도구는 의존성 관리부터 패키징, 배포까지 더 통합된 경험을 제공합니다.

**Why Poetry?**
**Poetry를 선택하는 이유**
-   **Single Config File**: It uses `pyproject.toml` for everything. No more `requirements.in`, `requirements.txt`, `setup.py`, etc.
-   **하나의 설정 파일**: 모든 구성을 `pyproject.toml` 하나에 담아 `requirements.in`, `requirements.txt`, `setup.py` 등을 따로 관리할 필요가 없습니다.
-   **True Dependency Resolution**: It has a true dependency resolver that prevents conflicting sub-dependencies.
-   **정확한 의존성 해석**: 하위 의존성 충돌을 방지하는 실제 해석기를 포함합니다.
-   **Integrated Tooling**: It manages virtual environments for you (`poetry shell`), builds your project (`poetry build`), and publishes it (`poetry publish`).
-   **통합 도구 제공**: `poetry shell`로 가상 환경을 관리하고, `poetry build`와 `poetry publish`로 빌드와 배포를 처리해 줍니다.

### Migrating to Poetry
### Poetry로 전환하기

1.  **Install Poetry**: Follow the official instructions.
1.  **Poetry 설치**: 공식 문서를 따라 설치합니다.
2.  **Initialize**: Run `poetry init` in your project. It will ask you questions and create a `[tool.poetry]` section in your `pyproject.toml`.
2.  **초기화**: 프로젝트에서 `poetry init`을 실행하면 질의응답을 거쳐 `pyproject.toml`에 `[tool.poetry]` 섹션을 생성합니다.
3.  **Add Dependencies**:
3.  **의존성 추가**:
    ```bash
    # Add a main dependency
    poetry add fastapi

    # Add a development dependency
    poetry add pytest --group dev
    ```
    ```bash
    # 메인 의존성 추가
    poetry add fastapi

    # 개발 의존성 추가
    poetry add pytest --group dev
    ```
    This automatically updates `pyproject.toml` and `poetry.lock` (the new lock file).
    이렇게 하면 `pyproject.toml`과 새로운 잠금 파일인 `poetry.lock`이 자동으로 갱신됩니다.
4.  **Run Commands**:
4.  **명령 실행**:
    -   `poetry install`: Installs all dependencies from `poetry.lock`.
    -   `poetry install`: `poetry.lock`에 정의된 모든 의존성을 설치합니다.
    -   `poetry run pytest`: Runs a command within the project's virtual environment.
    -   `poetry run pytest`: 프로젝트 가상 환경에서 명령을 실행합니다.
    -   `poetry shell`: Activates the virtual environment in your current shell.
    -   `poetry shell`: 현재 셸에서 가상 환경을 활성화합니다.

**Practice:** Convert one Level 1 mini-project to Poetry. Compare the resulting `pyproject.toml` with your previous `pip-tools` setup and note what changed.
**실습:** 레벨 1의 미니 프로젝트 하나를 Poetry로 전환해 보고, 새로 생성된 `pyproject.toml`을 기존 `pip-tools` 설정과 비교하여 무엇이 달라졌는지 기록하세요.

---

## 3. Managing Multiple Projects: Monorepos
## 3. 다중 프로젝트 관리: 모노레포

As your Vibe Coding empire grows, you might have several related services: a web API, a crawler, a data analysis library. A monorepo is a single repository that holds all of these.
Vibe Coding 생태계가 커지면 웹 API, 크롤러, 데이터 분석 라이브러리처럼 서로 연관된 여러 서비스를 다룰 수 있습니다. 모노레포는 이러한 모든 프로젝트를 하나의 저장소에서 관리하는 방식입니다.

**Benefits**:
**장점**:
-   **Atomic Commits Across Projects**: A single commit can change both the API and the library it depends on.
-   **다중 프로젝트 원자적 커밋**: 하나의 커밋으로 API와 그 의존 라이브러리를 동시에 수정할 수 있습니다.
-   **Simplified Dependency Management**: Easier to manage dependencies between your internal projects.
-   **간편한 의존성 관리**: 내부 프로젝트 간 의존 관계를 더 쉽게 다룰 수 있습니다.
-   **Unified Tooling**: One set of linting, testing, and CI/CD configurations for all projects.
-   **통합된 도구 체계**: 모든 프로젝트에 동일한 린트, 테스트, CI/CD 구성을 적용할 수 있습니다.

**Tooling for Python Monorepos**:
**파이썬 모노레포를 위한 도구**:
-   **Poetry's Path Dependencies**: You can specify a dependency as a local path, which is perfect for monorepos.
-   **Poetry 경로 의존성**: 로컬 경로를 의존성으로 지정할 수 있어 모노레포에 적합합니다.
    ```toml
    # in my-api/pyproject.toml
    [tool.poetry.dependencies]
    my-shared-library = { path = "../my-shared-library" }
    ```
    ```toml
    # my-api/pyproject.toml 예시
    [tool.poetry.dependencies]
    my-shared-library = { path = "../my-shared-library" }
    ```
-   **Pants or Bazel**: For very large-scale monorepos (think Google-scale), these build systems offer advanced features like fine-grained dependency tracking and remote caching, but they have a steep learning curve. For most Vibe Coders, Poetry is sufficient to start.
-   **Pants 또는 Bazel**: 구글 규모의 대형 모노레포에서는 세밀한 의존성 추적과 원격 캐시 같은 고급 기능을 제공하지만 학습 곡선이 가파릅니다. 대부분의 Vibe Coder에게는 Poetry만으로도 충분합니다.

By mastering these advanced concepts, you gain a deeper control over your code and development process. You'll write more elegant, efficient Python and be equipped to manage the complexity of growing, multi-service systems.
이러한 고급 개념을 익히면 코드와 개발 프로세스를 더 깊이 통제할 수 있습니다. 더욱 우아하고 효율적인 파이썬 코드를 작성하게 되며, 성장하는 멀티 서비스 시스템의 복잡성을 다룰 준비를 갖추게 됩니다.

## Going Further
## 더 나아가기
-   Build a “tooling sandbox” repo where you can benchmark Poetry vs. PDM environments and document trade-offs.
-   Poetry와 PDM 환경을 벤치마킹하고 트레이드오프를 기록할 “툴링 샌드박스” 저장소를 만들어 보세요.
-   Implement a pre-commit configuration that runs `ruff`, `mypy`, and a custom script to enforce project conventions.
-   `ruff`, `mypy`, 사용자 정의 스크립트를 실행하는 pre-commit 설정을 도입해 프로젝트 규칙을 자동 점검하세요.
-   Read the official Python data model documentation (`docs.python.org/3/reference/datamodel.html`) and summarize three dunder methods that you want to experiment with next week.
-   공식 파이썬 데이터 모델 문서를 읽고, 다음 주에 실험해 보고 싶은 던더 메서드 세 가지를 정리해 보세요.
