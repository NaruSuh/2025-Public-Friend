# 06.01 - Python Performance and Scalability

Writing code that works is the first step. Writing code that performs well under load is the mark of a professional. This guide covers the fundamentals of profiling, optimizing, and scaling Python applications.

## Core Concepts

1.  **Profiling**: Measuring your code to find out where it's spending its time (CPU) and memory. **Never optimize without profiling first.**
2.  **CPU-bound vs. I/O-bound**:
    -   **CPU-bound**: The task is limited by the speed of your processor (e.g., complex calculations, data compression). Scaling requires parallelism (`multiprocessing`).
    -   **I/O-bound**: The task is limited by waiting for external resources like networks or disks (e.g., API calls, database queries). Scaling requires concurrency (`asyncio`, threading).
3.  **Caching**: Storing the results of expensive operations to avoid re-computing them.
4.  **Horizontal vs. Vertical Scaling**:
    -   **Vertical Scaling**: Making your server more powerful (more CPU, more RAM). It's easy but has a hard limit and gets expensive.
    -   **Horizontal Scaling**: Adding more servers. It's more complex but can scale almost infinitely. Containerization (Docker) is a prerequisite for easy horizontal scaling.

---

## 1. Profiling: Finding the Bottleneck

Your intuition about what's slow in your code is often wrong. Measure, don't guess.

### Using `cProfile` for CPU Profiling

`cProfile` is a built-in Python profiler that's a great starting point.

Let's say you have a slow function:
```python
# slow_code.py
def slow_function():
    total = 0
    for i in range(10**6):
        total += i
    # ... and other complex logic ...
    return total

if __name__ == "__main__":
    slow_function()
```

You can profile it from the command line:
```bash
python -m cProfile -s tottime slow_code.py
```
-   `-m cProfile`: Runs the profiler module.
-   `-s tottime`: Sorts the output by the total time spent *in* the function (excluding sub-calls).

The output will look something like this:
```
         5 function calls in 0.042 seconds

   Ordered by: internal time

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.035    0.035    0.035    0.035 slow_code.py:2(slow_function)
        ...
```
This tells you that `slow_function` is where the most time is being spent.

### Using `py-spy` for Running Processes

`cProfile` is great, but it modifies your code's execution. `py-spy` is a sampling profiler that can attach to a running Python process without slowing it down. This is invaluable for profiling production applications.

**Install it**: `pip install py-spy`

1.  Find the Process ID (PID) of your running Python app: `pgrep python`.
2.  Run `py-spy`:
    ```bash
    # Record 30 seconds of activity and save it to a flame graph
    sudo py-spy record -o profile.svg --pid 12345 --duration 30

    # Or, show a live `top`-like view of your functions
    sudo py-spy top --pid 12345
    ```
The generated SVG flame graph is a powerful visualization that shows you exactly which functions are taking up the most CPU time.

---

## 2. Caching Strategies

Caching is one of the most effective ways to improve performance for repeated computations or data fetches.

### In-Memory Caching with `functools.lru_cache`

For functions whose return value depends only on their arguments, this is the easiest and fastest form of caching.

```python
import time
from functools import lru_cache

@lru_cache(maxsize=128)
def fetch_user_data(user_id: int):
    """
    A slow function that simulates fetching data from a database.
    """
    print(f"Fetching data for user {user_id}...")
    time.sleep(1)
    return {"id": user_id, "name": f"User {user_id}"}

# First call is slow
print(fetch_user_data(1)) # Takes 1 second

# Second call is instantaneous because the result is cached
print(fetch_user_data(1)) # Returns immediately

# The cache has a max size, and the "Least Recently Used" item is evicted.
```
**Use cases**: Caching configuration, results of pure functions, user permission lookups.
**Warning**: Be careful with memory usage. Don't cache large objects indefinitely.

### External Caching with Redis

For a distributed system (multiple servers), you need a shared, external cache like Redis. Redis is an in-memory key-value store that is incredibly fast.

```python
import redis
import json

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)

def get_article(article_id: str):
    cache_key = f"article:{article_id}"
    
    # 1. Try to get the article from the cache
    cached_article = r.get(cache_key)
    if cached_article:
        print("Cache HIT")
        return json.loads(cached_article)
    
    # 2. If not in cache, get it from the database (the slow part)
    print("Cache MISS")
    # article_from_db = ... fetch from database ...
    article_from_db = {"id": article_id, "title": "My Awesome Article", "content": "..."}
    
    # 3. Store it in the cache for next time, with an expiration (TTL)
    r.set(cache_key, json.dumps(article_from_db), ex=3600) # Cache for 1 hour
    
    return article_from_db
```
This is a common pattern called "cache-aside". It dramatically reduces the load on your primary database.

---

## 3. Scaling Your Application

### Scaling I/O-Bound Applications (like your crawler or a web API)

-   **Use `asyncio`**: As covered in the async guide, this is the first and most important step.
-   **Use a Production Server (`gunicorn`)**: A single Python process can only use one CPU core. `gunicorn` acts as a process manager, allowing you to run multiple worker processes, each with its own event loop. This lets you utilize all available CPU cores.
    ```bash
    # Run 4 worker processes
    gunicorn -k uvicorn.workers.UvicornWorker -w 4 src.main:app
    ```
    A common rule of thumb for the number of workers (`-w`) is `(2 * number_of_cpu_cores) + 1`.
-   **Horizontal Scaling**: Put your Docker container behind a load balancer (like Nginx or a cloud provider's load balancer). You can then run multiple instances of your container on different machines, and the load balancer will distribute traffic between them.

### Scaling CPU-Bound Applications

-   **Use `multiprocessing`**: This module allows you to spawn processes that run on different CPU cores, bypassing the Global Interpreter Lock (GIL).
-   **Use a Task Queue (Celery, RQ)**: For long-running, heavy computations, it's best to offload them from the web process to a dedicated pool of background workers.
    1.  A user makes an API request.
    2.  The API server quickly puts a "job" onto a message queue (like RabbitMQ or Redis).
    3.  The API server immediately returns a "202 Accepted" response to the user.
    4.  A separate pool of Celery workers, running on different machines, picks up jobs from the queue and does the heavy lifting.
    5.  The user can check the status of the job later via another endpoint.

This architecture is fundamental to building scalable, responsive systems. By understanding and applying these principles, you can ensure your Vibe Coding projects are not just functional, but fast and resilient under pressure.
