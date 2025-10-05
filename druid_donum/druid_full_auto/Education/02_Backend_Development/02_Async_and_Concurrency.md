# 02.02 - Async Python and Concurrency

Your crawler project involves waiting for network responses, which is a classic I/O-bound problem. `asyncio` is the perfect tool for this, allowing you to handle many network requests concurrently instead of one by one. This is a fundamental concept for building high-performance Vibe Coding applications.

## Core Concepts

1.  **Coroutines**: An `async def` function defines a coroutine. It's a special function that can be paused and resumed.
2.  **Event Loop**: The heart of `asyncio`. It manages and runs all the coroutines, deciding who gets to run and when.
3.  **`await`**: The keyword used to pause a coroutine and give control back to the event loop. You can only `await` other awaitables (like other coroutines or I/O operations).
4.  **Concurrency vs. Parallelism**:
    -   **Concurrency (what `asyncio` does)**: Juggling multiple tasks at once. One worker (a single CPU core) quickly switches between tasks while waiting for I/O. Think of a chef managing multiple pots on a stove.
    -   **Parallelism**: Running multiple tasks at the exact same time on different CPU cores. Think of multiple chefs, each with their own stove. This is for CPU-bound work and is handled by `multiprocessing`.

---

## Refactoring Your Crawler to be Asynchronous

Let's take the logic from your `druid_full_auto` crawler and make it asynchronous. We'll use `httpx` as our async HTTP client.

First, install `httpx`:
```bash
pip install httpx
```

### 1. The Synchronous (Original) Approach

This is how a traditional, sequential crawler works.

```python
import requests
import time

def fetch_page(url):
    print(f"Fetching {url}...")
    response = requests.get(url)
    print(f"Finished {url}")
    return response.text

def main_sync():
    start_time = time.time()
    urls = ["http://example.com"] * 5
    for url in urls:
        fetch_page(url)
    duration = time.time() - start_time
    print(f"Synchronous version took {duration:.2f} seconds.")

# If each request takes 1 second, this will take ~5 seconds.
# main_sync()
```

### 2. The Asynchronous (`asyncio`) Approach

Now, let's convert this to be concurrent.

```python
import asyncio
import httpx
import time

async def fetch_page_async(client: httpx.AsyncClient, url: str):
    """This is a coroutine."""
    print(f"Fetching {url}...")
    # 'await' pauses this function, allowing others to run.
    response = await client.get(url)
    print(f"Finished {url}")
    return response.text

async def main_async():
    """The main coroutine that orchestrates everything."""
    start_time = time.time()
    urls = ["http://example.com"] * 5
    
    # Use an AsyncClient as a context manager for proper connection handling.
    async with httpx.AsyncClient() as client:
        # Create a list of coroutine "tasks" to run.
        # These are not yet running, just scheduled.
        tasks = [fetch_page_async(client, url) for url in urls]
        
        # asyncio.gather runs all tasks concurrently and waits for them all to complete.
        results = await asyncio.gather(*tasks)
    
    duration = time.time() - start_time
    print(f"Asynchronous version took {duration:.2f} seconds.")
    # If each request takes 1 second, this will take just over 1 second.

# To run the top-level async function:
# asyncio.run(main_async())
```

**What's happening?**
1.  `fetch_page_async` is now a coroutine. When it hits `await client.get(url)`, it says to the event loop: "I'm waiting for the network. You can go run something else in the meantime."
2.  The event loop then finds another scheduled task (like another `fetch_page_async` call) and starts running it until *it* has to wait.
3.  This juggling act continues. All 5 network requests are fired off almost simultaneously. The total time is determined by the *longest* single request, not the sum of all of them.
4.  `asyncio.gather` is a powerful tool that takes a list of awaitables and runs them concurrently, returning the results in the same order once they are all complete.

---

## Practical Application: Rate Limiting and Semaphores

Crawling too fast can get you blocked. `asyncio` provides an elegant way to control concurrency with `asyncio.Semaphore`. A semaphore is like a bouncer at a club: it only lets a certain number of coroutines "in" (run) at a time.

Let's limit our crawler to 3 concurrent requests.

```python
import asyncio
import httpx
import time

async def fetch_with_semaphore(
    semaphore: asyncio.Semaphore, 
    client: httpx.AsyncClient, 
    url: str
):
    # This 'async with' block will wait until the semaphore's counter is > 0.
    # It decrements the counter on entry and increments it on exit.
    async with semaphore:
        print(f"Semaphore acquired, fetching {url}...")
        response = await client.get(url)
        print(f"Finished {url}, releasing semaphore.")
        # Add a small delay to be a good web citizen
        await asyncio.sleep(1) 
        return response.text

async def main_with_rate_limit():
    start_time = time.time()
    urls = ["http://example.com"] * 10
    
    # Create a semaphore that allows 3 concurrent operations.
    semaphore = asyncio.Semaphore(3)
    
    async with httpx.AsyncClient() as client:
        tasks = [fetch_with_semaphore(semaphore, client, url) for url in urls]
        results = await asyncio.gather(*tasks)
        
    duration = time.time() - start_time
    print(f"Rate-limited async version took {duration:.2f} seconds.")

# asyncio.run(main_with_rate_limit())
```

In this example, the first 3 `fetch_with_semaphore` tasks will acquire the semaphore and start their `httpx.get` calls. The 4th task will wait at `async with semaphore:` until one of the first 3 finishes and releases its spot. This is a much more efficient and controlled way to manage concurrent operations than manually managing a thread pool.

## When to use `asyncio`

-   **Good for**: I/O-bound tasks (network requests, database queries, reading/writing files). Your `druid_full_auto` crawler is a perfect use case.
-   **Bad for**: CPU-bound tasks (heavy calculations, image processing, complex data transformation). For these, `multiprocessing` is the right tool, as it uses multiple CPU cores.

By integrating `asyncio` into your Vibe Coding toolkit, you can build applications that are significantly faster and more efficient at handling real-world, I/O-heavy workloads.
