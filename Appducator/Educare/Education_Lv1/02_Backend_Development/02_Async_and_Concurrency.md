# 02.02 - Async Python and Concurrency
# 02.02 - 비동기 파이썬과 동시성

Your crawler project involves waiting for network responses, which is a classic I/O-bound problem. `asyncio` is the perfect tool for this, allowing you to handle many network requests concurrently instead of one by one. This is a fundamental concept for building high-performance Vibe Coding applications.
크롤러 프로젝트는 네트워크 응답을 기다리는 작업을 포함하는데, 이는 전형적인 I/O 바운드 문제입니다. `asyncio`는 이 문제에 완벽한 도구로, 많은 네트워크 요청을 하나씩 처리하는 대신 동시에 처리할 수 있게 해줍니다. 이것은 고성능 Vibe Coding 애플리케이션을 구축하기 위한 기본 개념입니다.

## Core Concepts
## 핵심 개념

1.  **Coroutines**: An `async def` function defines a coroutine. It's a special function that can be paused and resumed.
    **코루틴**: `async def` 함수는 코루틴을 정의합니다. 이것은 일시 중지하고 다시 시작할 수 있는 특별한 함수입니다.
2.  **Event Loop**: The heart of `asyncio`. It manages and runs all the coroutines, deciding who gets to run and when.
    **이벤트 루프**: `asyncio`의 심장입니다. 모든 코루틴을 관리하고 실행하며, 어떤 코루틴을 언제 실행할지 결정합니다.
3.  **`await`**: The keyword used to pause a coroutine and give control back to the event loop. You can only `await` other awaitables (like other coroutines or I/O operations).
    **`await`**: 코루틴을 일시 중지하고 이벤트 루프에 제어권을 돌려주기 위해 사용되는 키워드입니다. 다른 awaitable(다른 코루틴이나 I/O 작업 등)만 `await`할 수 있습니다.
4.  **Concurrency vs. Parallelism**:
    **동시성 대 병렬성**:
    -   **Concurrency (what `asyncio` does)**: Juggling multiple tasks at once. One worker (a single CPU core) quickly switches between tasks while waiting for I/O. Think of a chef managing multiple pots on a stove.
        **동시성 (`asyncio`가 하는 일)**: 한 번에 여러 작업을 저글링하는 것입니다. 하나의 작업자(단일 CPU 코어)가 I/O를 기다리는 동안 작업 간에 빠르게 전환합니다. 스토브에서 여러 냄비를 관리하는 요리사를 생각해보세요.
    -   **Parallelism**: Running multiple tasks at the exact same time on different CPU cores. Think of multiple chefs, each with their own stove. This is for CPU-bound work and is handled by `multiprocessing`.
        **병렬성**: 다른 CPU 코어에서 여러 작업을 정확히 동시에 실행하는 것입니다. 각자 자신의 스토브를 가진 여러 요리사를 생각해보세요. 이것은 CPU 바운드 작업을 위한 것이며 `multiprocessing`으로 처리됩니다.

---

## Refactoring Your Crawler to be Asynchronous
## 크롤러를 비동기적으로 리팩토링하기

Let's take the logic from your `druid_full_auto` crawler and make it asynchronous. We'll use `httpx` as our async HTTP client.
`druid_full_auto` 크롤러의 로직을 가져와 비동기적으로 만들어 보겠습니다. 비동기 HTTP 클라이언트로 `httpx`를 사용합니다.

First, install `httpx`:
먼저 `httpx`를 설치합니다:
```bash
pip install httpx
```

### 1. The Synchronous (Original) Approach
### 1. 동기적 (기존) 접근 방식

This is how a traditional, sequential crawler works.
이것이 전통적인 순차적 크롤러가 작동하는 방식입니다.

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
### 2. 비동기 (`asyncio`) 접근 방식

Now, let's convert this to be concurrent.
이제 이것을 동시적으로 변환해 보겠습니다.

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
**무슨 일이 일어나고 있나요?**
1.  `fetch_page_async` is now a coroutine. When it hits `await client.get(url)`, it says to the event loop: "I'm waiting for the network. You can go run something else in the meantime."
    `fetch_page_async`는 이제 코루틴입니다. `await client.get(url)`에 도달하면 이벤트 루프에 "네트워크를 기다리고 있으니, 그동안 다른 것을 실행해도 좋습니다."라고 말합니다.
2.  The event loop then finds another scheduled task (like another `fetch_page_async` call) and starts running it until *it* has to wait.
    그러면 이벤트 루프는 다른 예약된 작업(다른 `fetch_page_async` 호출과 같은)을 찾아 *그것이* 기다려야 할 때까지 실행을 시작합니다.
3.  This juggling act continues. All 5 network requests are fired off almost simultaneously. The total time is determined by the *longest* single request, not the sum of all of them.
    이 저글링은 계속됩니다. 5개의 모든 네트워크 요청이 거의 동시에 시작됩니다. 총 시간은 모든 요청의 합이 아니라 *가장 긴* 단일 요청에 의해 결정됩니다.
4.  `asyncio.gather` is a powerful tool that takes a list of awaitables and runs them concurrently, returning the results in the same order once they are all complete.
    `asyncio.gather`는 awaitable 목록을 가져와 동시에 실행하고, 모두 완료되면 동일한 순서로 결과를 반환하는 강력한 도구입니다.

---

## Practical Application: Rate Limiting and Semaphores
## 실제 적용: 속도 제한과 세마포어

Crawling too fast can get you blocked. `asyncio` provides an elegant way to control concurrency with `asyncio.Semaphore`. A semaphore is like a bouncer at a club: it only lets a certain number of coroutines "in" (run) at a time.
너무 빨리 크롤링하면 차단될 수 있습니다. `asyncio`는 `asyncio.Semaphore`를 사용하여 동시성을 제어하는 우아한 방법을 제공합니다. 세마포어는 클럽의 경비원과 같습니다. 한 번에 특정 수의 코루틴만 "들어가도록"(실행되도록) 허용합니다.

Let's limit our crawler to 3 concurrent requests.
크롤러를 3개의 동시 요청으로 제한해 보겠습니다.

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
이 예에서 처음 3개의 `fetch_with_semaphore` 작업은 세마포어를 획득하고 `httpx.get` 호출을 시작합니다. 4번째 작업은 처음 3개 중 하나가 끝나고 자리를 비울 때까지 `async with semaphore:`에서 기다립니다. 이것은 스레드 풀을 수동으로 관리하는 것보다 동시 작업을 관리하는 훨씬 효율적이고 제어된 방법입니다.

## When to use `asyncio`
## `asyncio`를 사용해야 할 때

-   **Good for**: I/O-bound tasks (network requests, database queries, reading/writing files). Your `druid_full_auto` crawler is a perfect use case.
    **적합한 경우**: I/O 바운드 작업(네트워크 요청, 데이터베이스 쿼리, 파일 읽기/쓰기). `druid_full_auto` 크롤러는 완벽한 사용 사례입니다.
-   **Bad for**: CPU-bound tasks (heavy calculations, image processing, complex data transformation). For these, `multiprocessing` is the right tool, as it uses multiple CPU cores.
    **부적합한 경우**: CPU 바운드 작업(무거운 계산, 이미지 처리, 복잡한 데이터 변환). 이러한 작업에는 여러 CPU 코어를 사용하는 `multiprocessing`이 적합한 도구입니다.

By integrating `asyncio` into your Vibe Coding toolkit, you can build applications that are significantly faster and more efficient at handling real-world, I/O-heavy workloads.
`asyncio`를 Vibe Coding 툴킷에 통합함으로써 실제 I/O가 많은 워크로드를 처리하는 데 훨씬 빠르고 효율적인 애플리케이션을 구축할 수 있습니다.