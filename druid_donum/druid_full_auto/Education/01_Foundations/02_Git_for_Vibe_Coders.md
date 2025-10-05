# 01.02 - Git for Vibe Coders: Beyond the Basics

Git is more than just a tool for saving code. It's a system for structuring your development process, collaborating safely, and maintaining a clean, understandable project history. A Vibe Coder uses Git with intention.

## Core Concepts

1.  **Atomic Commits**: Each commit should represent a single, complete, logical change.
2.  **Meaningful History**: Your commit history should read like a story of the project's development.
3.  **Branching Strategy**: A clear strategy for managing features, releases, and hotfixes.
4.  **Code Review**: Using Pull/Merge Requests as a quality gate.

---

## 1. Crafting Atomic Commits

A commit should be the smallest change that leaves the codebase in a consistent state.

-   **Good**: "Add user authentication endpoint" (includes model, service, route, and tests).
-   **Bad**: "Fix typo" followed by "Add login route" followed by "Add user model". These should be one commit.
-   **Bad**: "Implement user profile and payment processing". This is too large; it should be at least two separate commits.

### The `git add -p` (Patch) Command

This is a Vibe Coder's secret weapon. Instead of `git add .`, use `git add -p` to review and stage changes hunk by hunk.

```bash
git add -p src/main.py
```

Git will show you a block of changes and ask what to do:
-   `y`: Stage this hunk.
-   `n`: Do not stage this hunk.
-   `s`: Split this hunk into smaller hunks (if possible).
-   `e`: Edit the hunk manually (for advanced users).
-   `q`: Quit.

This practice forces you to review your own code and helps you build atomic commits by staging only related changes.

### Writing Great Commit Messages

A well-written commit message is crucial for a readable history. Follow the "50/72" rule.

-   **Subject Line (max 50 chars)**:
    -   Use the imperative mood (e.g., "Add," "Fix," "Refactor," not "Added," "Fixes").
    -   Capitalize the first letter.
    -   Do not end with a period.
    -   Example: `feat: Add user login endpoint`

-   **Body (optional, wrapped at 72 chars)**:
    -   Separated from the subject by a blank line.
    -   Explain the "what" and "why," not the "how." The code shows the "how."
    -   Reference issue numbers (e.g., "Resolves #42").

**Good Commit Message Template:**

```
feat: Implement password reset functionality

Adds the /request-reset and /reset-password endpoints.
This allows users who have forgotten their password to securely
reset it via a token sent to their email address.

Resolves: #23
```

**Conventional Commits**: For extra structure, use prefixes like `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`. This is highly recommended for automated versioning and changelog generation.

---

## 2. A Simple and Effective Branching Strategy: `main` + Feature Branches

For solo developers or small teams, a complex GitFlow is often overkill. A simpler approach is more effective.

1.  **`main` Branch**:
    -   Always represents the stable, production-ready state of the code.
    -   You should be able to deploy from `main` at any time.
    -   Direct commits to `main` are forbidden. Changes are only merged via Pull Requests.

2.  **Feature Branches**:
    -   Create a new branch for every new feature, bugfix, or chore.
    -   Branch off from the latest `main`.
    -   Name them descriptively, e.g., `feat/user-auth`, `fix/parsing-error`, `chore/update-deps`.

### The Workflow

```bash
# 1. Start a new feature, making sure your main is up-to-date
git checkout main
git pull origin main

# 2. Create a new feature branch
git checkout -b feat/new-cool-feature

# 3. Work on your feature, making atomic commits
# ... write code, run tests ...
git add -p
git commit -m "feat: Add core logic for cool feature"
# ... write more code, run tests ...
git add -p
git commit -m "feat: Add tests for cool feature"

# 4. Push your branch to the remote repository
git push origin feat/new-cool-feature

# 5. Open a Pull Request (PR) on GitHub/GitLab
#    - The PR compares your feature branch to `main`.
#    - Your CI pipeline (tests, linting) should run automatically.
#    - Review your own code one last time. If you have a team, assign a reviewer.

# 6. After review and all checks pass, merge the PR
#    - Use a "Squash and Merge" or "Rebase and Merge" strategy if possible.
#      - **Squash and Merge**: Combines all of your feature branch's commits into a single, clean commit on `main`. This keeps the `main` branch history very tidy. Highly recommended for Vibe Coders.
#      - **Rebase and Merge**: Replays your feature branch's commits on top of the latest `main`, creating a linear history. Cleaner than a standard merge, but can be more complex.

# 7. Clean up
git checkout main
git pull origin main # Update your local main
git branch -d feat/new-cool-feature # Delete the local feature branch
```

---

## 3. Interactive Rebase: Your Time Machine

`git rebase -i` is one of Git's most powerful features. It allows you to rewrite the history of your *local, unpushed* commits. This is perfect for cleaning up your work *before* you open a Pull Request.

Imagine your local history looks messy:
-   `commit 1`: "feat: Start user model"
-   `commit 2`: "oops, fix typo"
-   `commit 3`: "refactor: Clean up user model"
-   `commit 4`: "WIP"

You can clean this up before pushing.

```bash
# Rebase the last 4 commits
git rebase -i HEAD~4
```

This opens an editor with a list of your commits:

```
pick <hash1> feat: Start user model
pick <hash2> oops, fix typo
pick <hash3> refactor: Clean up user model
pick <hash4> WIP
```

You can change `pick` to other commands:
-   `r` or `reword`: Keep the commit, but change the message.
-   `s` or `squash`: Combine this commit with the one above it.
-   `f` or `fixup`: Like `squash`, but discard this commit's message.
-   `d` or `drop`: Delete the commit entirely.

To clean up our example, you could change it to:

```
pick <hash1> feat: Start user model
f <hash2> oops, fix typo
f <hash3> refactor: Clean up user model
d <hash4> WIP
```
Then, you'll be prompted to write a new, single commit message for the combined commits. You can reword the first one to be "feat: Add user model".

**Golden Rule of Rebasing**: Never rebase commits that have already been pushed and are being used by others. It rewrites history, which can cause major problems for collaborators. It's safe to rebase your own local feature branch before you've shared it.

By mastering this workflow, you treat your project's history as a first-class citizen. This discipline pays huge dividends in maintainability and makes it easier to find bugs (`git bisect`), understand features, and onboard new developers (even if that's just your future self).
