# 04.01 - CI/CD with GitHub Actions
# 04.01 - GitHub Actions를 사용한 CI/CD

Continuous Integration (CI) and Continuous Deployment (CD) are the backbone of modern software development and a core practice for Vibe Coding. They automate the process of testing and deploying your code, allowing you to release features faster and more reliably. GitHub Actions is a powerful and easy-to-use tool for this.
지속적 통합(CI)과 지속적 배포(CD)는 현대 소프트웨어 개발의 중추이며 Vibe Coding의 핵심 관행입니다. 코드 테스트 및 배포 프로세스를 자동화하여 기능을 더 빠르고 안정적으로 릴리스할 수 있도록 합니다. GitHub Actions는 이를 위한 강력하고 사용하기 쉬운 도구입니다.

## Core Concepts
## 핵심 개념

1.  **Workflow**: An automated process defined by a YAML file in the `.github/workflows/` directory.
    **워크플로**: `.github/workflows/` 디렉토리의 YAML 파일에 정의된 자동화된 프로세스입니다.
2.  **Event**: A specific activity that triggers a workflow (e.g., a `push` to a branch, opening a `pull_request`).
    **이벤트**: 워크플로를 트리거하는 특정 활동입니다(예: 브랜치에 `push`, `pull_request` 열기).
3.  **Job**: A set of steps that execute on the same runner. You can have multiple jobs that run in parallel.
    **작업**: 동일한 실행기에서 실행되는 단계 집합입니다. 병렬로 실행되는 여러 작업을 가질 수 있습니다.
4.  **Step**: An individual task that can run commands or an "action" (a reusable piece of code).
    **단계**: 명령 또는 "액션"(재사용 가능한 코드 조각)을 실행할 수 있는 개별 작업입니다.
5.  **Runner**: A server (managed by GitHub or self-hosted) that runs your workflows.
    **실행기**: 워크플로를 실행하는 서버(GitHub에서 관리하거나 자체 호스팅)입니다.

---

## A Practical CI/CD Workflow for a Python Project
## 파이썬 프로젝트를 위한 실용적인 CI/CD 워크플로

Let's create a workflow that:
다음과 같은 워크플로를 만들어 보겠습니다.
1.  Triggers on pushes and pull requests to the `main` branch.
    `main` 브랜치에 대한 푸시 및 풀 리퀘스트 시 트리거됩니다.
2.  Sets up a specific Python version.
    특정 파이썬 버전을 설정합니다.
3.  Caches dependencies to speed up subsequent runs.
    후속 실행 속도를 높이기 위해 의존성을 캐시합니다.
4.  Runs linting, type checking, and tests in parallel.
    린팅, 타입 검사 및 테스트를 병렬로 실행합니다.
5.  (Optional CD part) Deploys the application if tests on the `main` branch pass.
    (`main` 브랜치의 테스트가 통과하면 애플리케이션을 배포합니다(선택적 CD 부분).

Create the file `.github/workflows/ci-cd.yml`.
`.github/workflows/ci-cd.yml` 파일을 만듭니다.

```yaml
name: Python CI/CD

# 1. Trigger on pushes and pull requests to the main branch
on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

jobs:
  # This job handles linting and formatting checks
    steps:
      - name: Check out code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install ruff black

      - name: Run Ruff linter
        run: ruff .

      - name: Run Black formatter check
        run: black --check .

  # This job handles testing across different Python versions
  test:
    name: Test Suite
    runs-on: ubuntu-latest
    needs: lint # This job will only start after the 'lint' job succeeds
    steps:
      - name: Check out code
        uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      # Caching is crucial for speed!
      - name: Cache pip dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          # Create a unique key based on the Python version and the requirements files
          key: ${{ runner.os }}-pip-${{ matrix.python-version }}-${{ hashFiles('**/requirements*.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-${{ matrix.python-version }}-

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r dev-requirements.txt

      - name: Run Pytest
        run: pytest

  # This is the Continuous Deployment (CD) part
  deploy:
    name: Deploy to Production
    runs-on: ubuntu-latest
    # This job depends on the 'test' job succeeding
    needs: test
    # IMPORTANT: Only run this job on a push to the 'main' branch, not on pull requests
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
      - name: Check out code
        uses: actions/checkout@v4

      # Example: Deploying to a service like Google Cloud Run
      - name: 'Authenticate to Google Cloud'
        uses: 'google-github-actions/auth@v1'
        with:
          credentials_json: '${{ secrets.GCP_SA_KEY }}' # Store your service account key as a secret!

      - name: 'Deploy to Cloud Run'
        uses: 'google-github-actions/deploy-cloudrun@v1'
        with:
          service: 'my-vibe-project'
          region: 'us-central1'
          # If using Docker, you would first build and push the image here
          source: '.' # Or the directory containing your code
```

### How to Use This File
### 이 파일 사용 방법

1.  **Create the directory and file**: `.github/workflows/ci-cd.yml`.
    **디렉토리 및 파일 생성**: `.github/workflows/ci-cd.yml`.
2.  **Add Secrets**:
    **비밀 추가**:
    -   In your GitHub repository, go to `Settings` > `Secrets and variables` > `Actions`.
        GitHub 저장소에서 `설정` > `비밀 및 변수` > `작업`으로 이동합니다.
    -   Click `New repository secret`.
        `새 저장소 비밀`을 클릭합니다.
    -   Add any required secrets for deployment, like `GCP_SA_KEY` or `AWS_ACCESS_KEY_ID`. **Never commit secrets directly to your code.**
        `GCP_SA_KEY` 또는 `AWS_ACCESS_KEY_ID`와 같이 배포에 필요한 모든 비밀을 추가합니다. **비밀을 코드에 직접 커밋하지 마십시오.**
3.  **Commit and Push**: Commit the YAML file and push it to GitHub. The workflow will automatically be triggered.
    **커밋 및 푸시**: YAML 파일을 커밋하고 GitHub에 푸시합니다. 워크플로가 자동으로 트리거됩니다.

---

## Vibe Coding Best Practices for CI/CD
## CI/CD를 위한 Vibe Coding 모범 사례

-   **Start Small**: Your first CI pipeline can just run `pytest`. You can add linting, formatting, and deployment steps later.
    **작게 시작하기**: 첫 번째 CI 파이프라인은 `pytest`만 실행할 수 있습니다. 나중에 린팅, 포매팅 및 배포 단계를 추가할 수 있습니다.
-   **Keep it Fast**: Use caching (`actions/cache`) for dependencies. Run jobs in parallel. If your test suite gets slow, consider splitting it into multiple jobs (e.g., unit tests vs. integration tests).
    **빠르게 유지하기**: 의존성을 위해 캐싱(`actions/cache`)을 사용합니다. 작업을 병렬로 실행합니다. 테스트 스위트가 느려지면 여러 작업(예: 단위 테스트 대 통합 테스트)으로 분할하는 것을 고려하십시오.
-   **Fail Fast**: Put your quickest checks first. Linting is faster than running a full test suite, so the `lint` job runs first. If it fails, you get immediate feedback without waiting for the tests.
    **빨리 실패하기**: 가장 빠른 확인을 먼저 수행합니다. 린팅은 전체 테스트 스위트를 실행하는 것보다 빠르므로 `lint` 작업이 먼저 실행됩니다. 실패하면 테스트를 기다리지 않고 즉시 피드백을 받습니다.
-   **Protect Your `main` Branch**: In your repository settings (`Settings` > `Branches`), add a branch protection rule for `main`.
    **`main` 브랜치 보호**: 저장소 설정(`설정` > `브랜치`)에서 `main`에 대한 브랜치 보호 규칙을 추가합니다.
    -   Require status checks to pass before merging (e.g., require the `lint` and `test` jobs to succeed).
        병합하기 전에 상태 확인이 통과되도록 요구합니다(예: `lint` 및 `test` 작업이 성공해야 함).
    -   Require pull request reviews.
        풀 리퀘스트 검토를 요구합니다.
    -   This prevents broken code from ever reaching your main branch.
        이렇게 하면 깨진 코드가 메인 브랜치에 도달하는 것을 방지할 수 있습니다.
-   **One-Line Deployment**: Your goal should be to have a system where merging a PR to `main` automatically and safely deploys the change to production. This workflow is the first major step toward that reality.
    **원라인 배포**: `main`에 PR을 병합하면 자동으로 안전하게 변경 사항이 프로덕션에 배포되는 시스템을 갖추는 것이 목표여야 합니다. 이 워크플로는 그 현실을 향한 첫 번째 주요 단계입니다.

By automating your quality gates and deployment process, you create a powerful feedback loop. This allows you to code with confidence, knowing that a safety net is always there to catch mistakes before they reach users. This is the essence of shipping high-quality software at speed.
품질 게이트와 배포 프로세스를 자동화함으로써 강력한 피드백 루프를 만듭니다. 이를 통해 실수가 사용자에게 도달하기 전에 항상 잡아주는 안전망이 있다는 것을 알고 자신 있게 코딩할 수 있습니다. 이것이 빠른 속도로 고품질 소프트웨어를 제공하는 것의 본질입니다.