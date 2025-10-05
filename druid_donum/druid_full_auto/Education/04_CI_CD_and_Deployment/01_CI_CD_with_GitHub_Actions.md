# 04.01 - CI/CD with GitHub Actions

Continuous Integration (CI) and Continuous Deployment (CD) are the backbone of modern software development and a core practice for Vibe Coding. They automate the process of testing and deploying your code, allowing you to release features faster and more reliably. GitHub Actions is a powerful and easy-to-use tool for this.

## Core Concepts

1.  **Workflow**: An automated process defined by a YAML file in the `.github/workflows/` directory.
2.  **Event**: A specific activity that triggers a workflow (e.g., a `push` to a branch, opening a `pull_request`).
3.  **Job**: A set of steps that execute on the same runner. You can have multiple jobs that run in parallel.
4.  **Step**: An individual task that can run commands or an "action" (a reusable piece of code).
5.  **Runner**: A server (managed by GitHub or self-hosted) that runs your workflows.

---

## A Practical CI/CD Workflow for a Python Project

Let's create a workflow that:
1.  Triggers on pushes and pull requests to the `main` branch.
2.  Sets up a specific Python version.
3.  Caches dependencies to speed up subsequent runs.
4.  Runs linting, type checking, and tests in parallel.
5.  (Optional CD part) Deploys the application if tests on the `main` branch pass.

Create the file `.github/workflows/ci-cd.yml`.

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
  lint:
    name: Lint & Format Check
    runs-on: ubuntu-latest
    steps:
      - name: Check out code
        uses: actions/checkout@v3

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
    strategy:
      matrix:
        # Run tests on multiple Python versions
        python-version: ['3.10', '3.11']

    steps:
      - name: Check out code
        uses: actions/checkout@v3

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
        uses: actions/checkout@v3

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

1.  **Create the directory and file**: `.github/workflows/ci-cd.yml`.
2.  **Add Secrets**:
    -   In your GitHub repository, go to `Settings` > `Secrets and variables` > `Actions`.
    -   Click `New repository secret`.
    -   Add any required secrets for deployment, like `GCP_SA_KEY` or `AWS_ACCESS_KEY_ID`. **Never commit secrets directly to your code.**
3.  **Commit and Push**: Commit the YAML file and push it to GitHub. The workflow will automatically be triggered.

---

## Vibe Coding Best Practices for CI/CD

-   **Start Small**: Your first CI pipeline can just run `pytest`. You can add linting, formatting, and deployment steps later.
-   **Keep it Fast**: Use caching (`actions/cache`) for dependencies. Run jobs in parallel. If your test suite gets slow, consider splitting it into multiple jobs (e.g., unit tests vs. integration tests).
-   **Fail Fast**: Put your quickest checks first. Linting is faster than running a full test suite, so the `lint` job runs first. If it fails, you get immediate feedback without waiting for the tests.
-   **Protect Your `main` Branch**: In your repository settings (`Settings` > `Branches`), add a branch protection rule for `main`.
    -   Require status checks to pass before merging (e.g., require the `lint` and `test` jobs to succeed).
    -   Require pull request reviews.
    -   This prevents broken code from ever reaching your main branch.
-   **One-Line Deployment**: Your goal should be to have a system where merging a PR to `main` automatically and safely deploys the change to production. This workflow is the first major step toward that reality.

By automating your quality gates and deployment process, you create a powerful feedback loop. This allows you to code with confidence, knowing that a safety net is always there to catch mistakes before they reach users. This is the essence of shipping high-quality software at speed.
