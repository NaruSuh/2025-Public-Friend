# 01 - Foundations - Lv.2: Advanced Python and Tooling

You've mastered the basics of a modern development environment. Now, it's time to deepen your understanding of Python itself and adopt more powerful tooling to manage complexity.

## Core Concepts

1.  **Advanced Python Features**: Move beyond basic syntax to understand the "why" behind Python's design, including generators, context managers, decorators, and the data model.
2.  **Dependency Management at Scale**: Transition from `pip-tools` to a fully integrated project management tool like `Poetry` or `PDM`.
3.  **Monorepo Strategy**: Understand how to manage multiple related projects within a single repository for streamlined development.

---

## 1. Deeper into Python: The Language's "Magic"

To write truly "Pythonic" and efficient code, you need to understand the protocols that underpin the language.

### Generators and Coroutines
You've used `asyncio`, but do you understand the generator foundations it's built upon?
-   **`yield` vs. `return`**: A function with `yield` becomes a generator, producing a sequence of values over time without holding them all in memory.
-   **Generator Expressions**: A concise way to create generators: `(i*i for i in range(1000))` vs a list comprehension `[i*i for i in range(1000)]`. The former is memory-efficient.
-   **`yield from`**: A way to chain generators, which is conceptually similar to how `await` delegates control in `asyncio`.

### Context Managers (`with` statement)
You use `with open(...)` all the time. How does it work? By implementing the context management protocol.
-   **`__enter__` and `__exit__`**: Any class with these two methods can be used in a `with` statement. `__enter__` sets up the context (e.g., opens the file), and `__exit__` guarantees teardown (e.g., closes the file), even if errors occur.
-   **`@contextmanager` decorator**: A generator-based way to create a simple context manager from the `contextlib` module.

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

### Decorators
A decorator is a function that takes another function and extends its behavior without explicitly modifying it.
-   **Function as First-Class Objects**: In Python, functions can be passed as arguments, returned from other functions, and assigned to variables. This is what makes decorators possible.
-   **`@` syntax**: Syntactic sugar for `my_function = my_decorator(my_function)`.
-   **`functools.wraps`**: A helper decorator that ensures the decorated function retains its original name, docstring, etc.

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

---

## 2. Next-Level Dependency Management: Poetry

While `pip-tools` is great, tools like `Poetry` offer a more integrated experience for managing dependencies, packaging, and publishing your project.

**Why Poetry?**
-   **Single Config File**: It uses `pyproject.toml` for everything. No more `requirements.in`, `requirements.txt`, `setup.py`, etc.
-   **True Dependency Resolution**: It has a true dependency resolver that prevents conflicting sub-dependencies.
-   **Integrated Tooling**: It manages virtual environments for you (`poetry shell`), builds your project (`poetry build`), and publishes it (`poetry publish`).

### Migrating to Poetry

1.  **Install Poetry**: Follow the official instructions.
2.  **Initialize**: Run `poetry init` in your project. It will ask you questions and create a `[tool.poetry]` section in your `pyproject.toml`.
3.  **Add Dependencies**:
    ```bash
    # Add a main dependency
    poetry add fastapi

    # Add a development dependency
    poetry add pytest --group dev
    ```
    This automatically updates `pyproject.toml` and `poetry.lock` (the new lock file).
4.  **Run Commands**:
    -   `poetry install`: Installs all dependencies from `poetry.lock`.
    -   `poetry run pytest`: Runs a command within the project's virtual environment.
    -   `poetry shell`: Activates the virtual environment in your current shell.

---

## 3. Managing Multiple Projects: Monorepos

As your Vibe Coding empire grows, you might have several related services: a web API, a crawler, a data analysis library. A monorepo is a single repository that holds all of these.

**Benefits**:
-   **Atomic Commits Across Projects**: A single commit can change both the API and the library it depends on.
-   **Simplified Dependency Management**: Easier to manage dependencies between your internal projects.
-   **Unified Tooling**: One set of linting, testing, and CI/CD configurations for all projects.

**Tooling for Python Monorepos**:
-   **Poetry's Path Dependencies**: You can specify a dependency as a local path, which is perfect for monorepos.
    ```toml
    # in my-api/pyproject.toml
    [tool.poetry.dependencies]
    my-shared-library = { path = "../my-shared-library" }
    ```
-   **Pants or Bazel**: For very large-scale monorepos (think Google-scale), these build systems offer advanced features like fine-grained dependency tracking and remote caching, but they have a steep learning curve. For most Vibe Coders, Poetry is sufficient to start.

By mastering these advanced concepts, you gain a deeper control over your code and development process. You'll write more elegant, efficient Python and be equipped to manage the complexity of growing, multi-service systems.
