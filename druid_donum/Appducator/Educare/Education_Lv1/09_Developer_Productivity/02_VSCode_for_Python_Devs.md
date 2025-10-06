# 09.02 - VSCode for Python Vibe Coders
# 09.02 - 파이썬 Vibe 코더를 위한 VSCode

Your editor is your primary tool. A well-configured VSCode setup can dramatically boost your productivity, enforce consistency, and make coding a more joyful experience. This is the Vibe Coder's cockpit.
에디터는 주요 도구입니다. 잘 구성된 VSCode 설정은 생산성을 크게 높이고 일관성을 유지하며 코딩을 더 즐거운 경험으로 만들 수 있습니다. 이것이 Vibe 코더의 조종석입니다.

## Must-Have Extensions
## 필수 확장 프로그램

1.  **Python (Microsoft)**: The official extension. Provides rich support for Python, including features like linting, debugging, code navigation, and virtual environment selection.
    **Python (Microsoft)**: 공식 확장 프로그램입니다. 린팅, 디버깅, 코드 탐색, 가상 환경 선택과 같은 기능을 포함하여 파이썬에 대한 풍부한 지원을 제공합니다.
2.  **Ruff (charliermarsh)**: Integrates the `ruff` linter directly into your editor. It will show you errors and formatting issues in real-time and can often fix them automatically on save.
    **Ruff (charliermarsh)**: `ruff` 린터를 에디터에 직접 통합합니다. 실시간으로 오류 및 서식 문제를 보여주고 저장 시 자동으로 수정할 수 있는 경우가 많습니다.
3.  **Mypy Type Checker (ms-python.mypy-type-checker)**: Integrates the `mypy` type checker, showing type errors directly in your code.
    **Mypy Type Checker (ms-python.mypy-type-checker)**: `mypy` 타입 검사기를 통합하여 코드에서 직접 타입 오류를 보여줍니다.
4.  **GitLens (GitKraken)**: Supercharges the Git capabilities built into VSCode. It helps you visualize code authorship with Git blame annotations, navigate history, and gain powerful insights into your repository.
    **GitLens (GitKraken)**: VSCode에 내장된 Git 기능을 강화합니다. Git 블레임 주석으로 코드 작성자를 시각화하고, 히스토리를 탐색하며, 저장소에 대한 강력한 통찰력을 얻는 데 도움이 됩니다.
5.  **Docker (Microsoft)**: Makes it easy to create, manage, and debug containerized applications.
    **Docker (Microsoft)**: 컨테이너화된 애플리케이션을 쉽게 만들고, 관리하고, 디버그할 수 있도록 합니다.

---

## Configuring `settings.json` for a Vibe Workflow
## Vibe 워크플로를 위한 `settings.json` 구성

Create a workspace settings file at `.vscode/settings.json`. This ensures that anyone who opens the project in VSCode gets the same consistent setup.
`.vscode/settings.json`에 작업 공간 설정 파일을 만듭니다. 이렇게 하면 VSCode에서 프로젝트를 여는 모든 사람이 동일하고 일관된 설정을 갖게 됩니다.

```json
{
    // --- General Editor Settings ---
    "editor.rulers": [88],
    "editor.tabSize": 4,
    "files.insertFinalNewline": true,
    "files.trimTrailingWhitespace": true,

    // --- Python Specific Settings ---
    "[python]": {
        // Use Ruff as the default formatter and enable format on save
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true,
        
        // Enable code actions (like auto-import) on save
        "editor.codeActionsOnSave": {
            "source.fixAll": true,
            "source.organizeImports": true
        },
    },

    // --- Ruff Linter Configuration ---
    "ruff.lint.args": [
        "--select=ALL", // Start with all rules and selectively ignore
        "--ignore=D100,D104,D107" // Ignore missing docstrings in public modules, packages, and __init__ files
    ],

    // --- Pytest Configuration ---
    "python.testing.pytestArgs": [
        "tests"
    ],
    "python.testing.unittestEnabled": false,
    "python.testing.pytestEnabled": true,

    // --- Mypy Type Checker Configuration ---
    "mypy-type-checker.importStrategy": "fromEnvironment",
    "mypy-type-checker.args": [
        "--follow-imports=silent",
        "--ignore-missing-imports",
        "--show-column-numbers",
        "--no-pretty"
    ]
}
```

### What This Configuration Does:
### 이 구성의 역할:

-   **`editor.rulers`**: Adds a vertical line at 88 characters, helping you adhere to code style guides (`black`'s default line length).
    **`editor.rulers`**: 88자 위치에 수직선을 추가하여 코드 스타일 가이드(`black`의 기본 줄 길이)를 준수하는 데 도움을 줍니다.
-   **`editor.formatOnSave`**: Automatically formats your code with `ruff` every time you save. This is a core Vibe Coding practice. No more manual formatting.
    **`editor.formatOnSave`**: 저장할 때마다 `ruff`로 코드를 자동으로 포맷합니다. 이것은 핵심적인 Vibe Coding 관행입니다. 더 이상 수동으로 포맷할 필요가 없습니다.
-   **`editor.codeActionsOnSave`**: Automatically fixes lint errors and organizes your imports on save. This keeps your code clean and consistent with zero effort.
    **`editor.codeActionsOnSave`**: 저장 시 린트 오류를 자동으로 수정하고 임포트를 정리합니다. 이를 통해 노력 없이 코드를 깨끗하고 일관성 있게 유지할 수 있습니다.
-   **`ruff.lint.args`**: Configures Ruff to be very strict (`--select=ALL`) but ignores a few noisy docstring rules. It's better to be explicit about ignoring rules than to have a loose default.
    **`ruff.lint.args`**: Ruff를 매우 엄격하게 구성(`--select=ALL`)하지만 몇 가지 시끄러운 독스트링 규칙은 무시하도록 합니다. 느슨한 기본값을 갖는 것보다 규칙을 무시하는 것에 대해 명시적인 것이 좋습니다.
-   **`python.testing.*`**: Configures VSCode to discover and run tests using `pytest`.
    **`python.testing.*`**: `pytest`를 사용하여 테스트를 검색하고 실행하도록 VSCode를 구성합니다.
-   **`mypy-type-checker.*`**: Enables and configures the Mypy extension for real-time type checking.
    **`mypy-type-checker.*`**: 실시간 타입 검사를 위해 Mypy 확장을 활성화하고 구성합니다.

---

## The Vibe Coder Workflow in VSCode
## VSCode에서의 Vibe 코더 워크플로우

1.  **Select the Interpreter**: Open the Command Palette (`Ctrl+Shift+P`), type `Python: Select Interpreter`, and choose the one inside your project's `.venv` directory. This is crucial for VSCode to find your installed dependencies.
    **인터프리터 선택**: 명령 팔레트(`Ctrl+Shift+P`)를 열고 `Python: 인터프리터 선택`을 입력한 다음 프로젝트의 `.venv` 디렉토리 내에 있는 것을 선택합니다. 이것은 VSCode가 설치된 의존성을 찾는 데 매우 중요합니다.
2.  **Write Code**: As you write, `ruff` and `mypy` will give you immediate feedback in the "Problems" panel.
    **코드 작성**: 코드를 작성하면 `ruff`와 `mypy`가 "문제" 패널에서 즉각적인 피드백을 제공합니다.
3.  **Save File (`Ctrl+S`)**: The moment you save, your code is automatically formatted, and imports are organized. What you see is what you commit.
    **파일 저장 (`Ctrl+S`)**: 저장하는 순간 코드가 자동으로 포맷되고 임포트가 정리됩니다. 보이는 것이 커밋하는 것입니다.
4.  **Run Tests**: Open the Test Explorer view in the sidebar. You can run all tests or individual tests with a single click and see the results visually.
    **테스트 실행**: 사이드바에서 테스트 탐색기 보기를 엽니다. 한 번의 클릭으로 모든 테스트 또는 개별 테스트를 실행하고 결과를 시각적으로 볼 수 있습니다.
5.  **Debug**: Set breakpoints by clicking in the gutter next to the line numbers. Go to the "Run and Debug" view, and launch the debugger. You can inspect variables, step through code, and diagnose issues interactively.
    **디버그**: 줄 번호 옆의 여백을 클릭하여 중단점을 설정합니다. "실행 및 디버그" 보기로 이동하여 디버거를 시작합니다. 변수를 검사하고, 코드를 단계별로 실행하며, 대화식으로 문제를 진단할 수 있습니다.
6.  **Commit with Confidence**: Because your code has been linted, formatted, and type-checked continuously, and your tests are passing, you can commit with high confidence that you are not introducing quality issues.
    **자신감 있게 커밋**: 코드가 지속적으로 린팅, 포맷팅, 타입 검사를 거쳤고 테스트를 통과했기 때문에 품질 문제를 일으키지 않는다는 높은 자신감을 가지고 커밋할 수 있습니다.

This tight feedback loop between writing, checking, and testing is what makes development fast, efficient, and enjoyable. It automates the tedious parts of coding, freeing you up to focus on solving real problems.
작성, 확인, 테스트 사이의 이 긴밀한 피드백 루프는 개발을 빠르고 효율적이며 즐겁게 만듭니다. 코딩의 지루한 부분을 자동화하여 실제 문제 해결에 집중할 수 있도록 해줍니다.