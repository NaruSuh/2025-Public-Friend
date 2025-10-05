# 06.01 - Performance and Scalability
# 06.01 - 성능 및 확장성

Performance isn't just about making your code fast; it's about ensuring your application remains fast, reliable, and cost-effective as it grows. Scalability is the ability of your system to handle an increasing amount of load. A Vibe Coder thinks about this from the start, not as an afterthought when things are on fire.
성능은 단순히 코드를 빠르게 만드는 것에 관한 것이 아닙니다. 애플리케이션이 성장함에 따라 빠르고 안정적이며 비용 효율적으로 유지되도록 보장하는 것입니다. 확장성은 증가하는 부하를 처리하는 시스템의 능력입니다. Vibe 코더는 상황이 악화되었을 때 나중에 생각하는 것이 아니라 처음부터 이것에 대해 생각합니다.

## Core Concepts
## 핵심 개념

1.  **Latency vs. Throughput**:
    **지연 시간 대 처리량**:
    -   **Latency**: The time it takes to serve a single request. (User-facing metric).
        **지연 시간**: 단일 요청을 처리하는 데 걸리는 시간입니다. (사용자 대면 메트릭).
    -   **Throughput**: The number of requests you can serve in a given time period (e.g., requests per second). (System-facing metric).
        **처리량**: 주어진 시간 동안 처리할 수 있는 요청 수입니다(예: 초당 요청 수). (시스템 대면 메트릭).
2.  **Scaling Up vs. Scaling Out**:
    **스케일 업 대 스케일 아웃**:
    -   **Scaling Up (Vertical Scaling)**: Adding more resources to a single server (e.g., more CPU, more RAM). It's simple but has a hard limit and can be expensive.
        **스케일 업(수직 확장)**: 단일 서버에 더 많은 리소스(예: 더 많은 CPU, 더 많은 RAM)를 추가하는 것입니다. 간단하지만 한계가 있고 비용이 많이 들 수 있습니다.
    -   **Scaling Out (Horizontal Scaling)**: Adding more servers to your system. This is the foundation of modern, cloud-native applications.
        **스케일 아웃(수평 확장)**: 시스템에 더 많은 서버를 추가하는 것입니다. 이것이 현대 클라우드 네이티브 애플리케이션의 기반입니다.
3.  **Stateless vs. Stateful Applications**:
    **상태 비저장 대 상태 저장 애플리케이션**:
    -   **Stateless**: An application that does not store any client session data on the server. Any server can handle any request. This is the key to easy horizontal scaling.
        **상태 비저장**: 서버에 클라이언트 세션 데이터를 저장하지 않는 애플리케이션입니다. 모든 서버가 모든 요청을 처리할 수 있습니다. 이것이 쉬운 수평 확장의 핵심입니다.
    -   **Stateful**: An application that stores session data on the server. This makes scaling harder, as you need to ensure a user is always routed to the server that holds their state, or you need a distributed way to share state.
        **상태 저장**: 서버에 세션 데이터를 저장하는 애플리케이션입니다. 사용자가 항상 자신의 상태를 보유한 서버로 라우팅되도록 하거나 상태를 공유할 분산된 방법이 필요하기 때문에 확장이 더 어려워집니다.

---

## 1. Designing for Statelessness
## 1. 상태 비저장 설계

Your web application should be stateless. This is a non-negotiable principle for Vibe Coding.
웹 애플리케이션은 상태 비저장이어야 합니다. 이것은 Vibe Coding에 대한 타협할 수 없는 원칙입니다.

-   **Don't store state in global variables or in memory.** If you have multiple instances of your app running, the state will be inconsistent.
    **전역 변수나 메모리에 상태를 저장하지 마십시오.** 앱의 여러 인스턴스가 실행 중인 경우 상태가 일관되지 않습니다.
-   **Store state in a dedicated, shared service**: User sessions, shopping carts, etc., should be stored in a database (like Redis for caching/sessions or PostgreSQL for primary data).
    **전용 공유 서비스에 상태 저장**: 사용자 세션, 장바구니 등은 데이터베이스(캐싱/세션용 Redis 또는 기본 데이터용 PostgreSQL 등)에 저장해야 합니다.
-   **Use Tokens for Authentication**: Instead of server-side sessions, use stateless tokens like JWT (JSON Web Tokens). The client sends the token with every request, and the server can validate it without needing to look up a session store.
    **인증에 토큰 사용**: 서버 측 세션 대신 JWT(JSON 웹 토큰)와 같은 상태 비저장 토큰을 사용합니다. 클라이언트는 모든 요청과 함께 토큰을 보내고 서버는 세션 저장소를 조회할 필요 없이 토큰을 검증할 수 있습니다.

Because your application is stateless, you can run 100 identical copies of it behind a **load balancer**. The load balancer's job is to distribute incoming traffic evenly across all the application instances.
애플리케이션이 상태 비저장이기 때문에 **로드 밸런서** 뒤에서 100개의 동일한 복사본을 실행할 수 있습니다. 로드 밸런서의 역할은 들어오는 트래픽을 모든 애플리케이션 인스턴스에 고르게 분산하는 것입니다.

---

## 2. Asynchronous Operations and Background Jobs
## 2. 비동기 작업 및 백그라운드 작업

Users should not have to wait for slow operations.
사용자는 느린 작업을 기다릴 필요가 없습니다.

-   **Use `async` for I/O-bound tasks**: As covered in the `asyncio` guide, this is crucial for handling many concurrent network requests or database calls efficiently within a single application instance.
    **I/O 바운드 작업에 `async` 사용**: `asyncio` 가이드에서 다루었듯이, 이것은 단일 애플리케이션 인스턴스 내에서 많은 동시 네트워크 요청이나 데이터베이스 호출을 효율적으로 처리하는 데 중요합니다.
-   **Use a Job Queue for Long-Running Tasks**: For tasks that take more than a few seconds (e.g., sending a welcome email, processing a video, generating a report), you should offload them to a background worker process.
    **장기 실행 작업에 작업 큐 사용**: 몇 초 이상 걸리는 작업(예: 환영 이메일 보내기, 비디오 처리, 보고서 생성)의 경우 백그라운드 작업자 프로세스로 오프로드해야 합니다.

**Common Architecture:**
**일반적인 아키텍처:**
1.  The user makes an API request to your web application.
    사용자가 웹 애플리케이션에 API 요청을 합니다.
2.  The web app immediately responds with `202 Accepted` and places a "job" message onto a message queue (like RabbitMQ or Redis).
    웹 앱은 즉시 `202 Accepted`로 응답하고 메시지 큐(예: RabbitMQ 또는 Redis)에 "작업" 메시지를 넣습니다.
3.  A separate pool of "worker" processes is constantly listening to the queue. One of the workers picks up the job and starts processing it.
    별도의 "작업자" 프로세스 풀이 지속적으로 큐를 수신합니다. 작업자 중 하나가 작업을 선택하고 처리를 시작합니다.
4.  The user is not blocked. They can continue using the application. You can provide a separate endpoint for them to check the status of the job.
    사용자는 차단되지 않습니다. 애플리케이션을 계속 사용할 수 있습니다. 작업 상태를 확인할 수 있는 별도의 엔드포인트를 제공할 수 있습니다.

Popular Python libraries for this are **Celery** and **Dramatiq**.
이를 위한 인기 있는 파이썬 라이브러리는 **Celery**와 **Dramatiq**입니다.

---

## 3. Caching
## 3. 캐싱

Caching is about storing the results of expensive operations and reusing them. It's one of the most effective ways to improve performance.
캐싱은 비용이 많이 드는 작업의 결과를 저장하고 재사용하는 것입니다. 성능을 향상시키는 가장 효과적인 방법 중 하나입니다.

**Levels of Caching:**
**캐싱 수준:**

1.  **In-Memory Cache (within your app)**: Use a simple dictionary or a library like `functools.lru_cache` for data that is frequently accessed and doesn't change often. This is very fast but is not shared between different application instances.
    **인메모리 캐시(앱 내)**: 자주 액세스하고 자주 변경되지 않는 데이터의 경우 간단한 사전이나 `functools.lru_cache`와 같은 라이브러리를 사용합니다. 매우 빠르지만 다른 애플리케이션 인스턴스 간에 공유되지 않습니다.
    ```python
    from functools import lru_cache

    @lru_cache(maxsize=128)
    def get_user_permissions(user_id: int):
        # Expensive database call
        print(f"Fetching permissions for user {user_id} from DB...")
        # ... database logic ...
        return ["read", "write"]
    ```
2.  **Distributed Cache (e.g., Redis)**: An external, in-memory data store that is shared by all your application instances. Redis is extremely fast and is perfect for caching database query results, API responses, or user sessions.
    **분산 캐시(예: Redis)**: 모든 애플리케이션 인스턴스에서 공유되는 외부 인메모리 데이터 저장소입니다. Redis는 매우 빠르며 데이터베이스 쿼리 결과, API 응답 또는 사용자 세션을 캐싱하는 데 적합합니다.
    **Common Strategy**: When a request comes in:
    **일반적인 전략**: 요청이 들어오면:
    -   First, check if the result is in Redis. If yes, return it immediately.
        먼저 결과가 Redis에 있는지 확인합니다. 그렇다면 즉시 반환합니다.
    -   If not, fetch the data from the primary database (the source of truth).
        그렇지 않으면 기본 데이터베이스(진실의 원천)에서 데이터를 가져옵니다.
    -   Store the result in Redis with an expiration time (TTL - Time To Live).
        결과를 만료 시간(TTL - Time To Live)과 함께 Redis에 저장합니다.
    -   Return the result.
        결과를 반환합니다.
3.  **Content Delivery Network (CDN)**: A network of servers distributed around the world that cache your static assets (images, CSS, JavaScript) and sometimes dynamic content. This reduces latency for users by serving content from a server that is geographically close to them.
    **콘텐츠 전송 네트워크(CDN)**: 정적 자산(이미지, CSS, JavaScript) 및 때로는 동적 콘텐츠를 캐시하는 전 세계에 분산된 서버 네트워크입니다. 이렇게 하면 지리적으로 가까운 서버에서 콘텐츠를 제공하여 사용자의 대기 시간을 줄일 수 있습니다.

By designing stateless services, leveraging asynchronicity, and implementing a smart caching strategy, you build systems that can handle massive scale while remaining fast and responsive. This proactive approach to architecture is a hallmark of a senior engineer and a Vibe Coder.
상태 비저장 서비스를 설계하고, 비동기성을 활용하고, 스마트 캐싱 전략을 구현함으로써 빠르고 응답성이 뛰어나면서 대규모 확장을 처리할 수 있는 시스템을 구축합니다. 아키텍처에 대한 이러한 사전 예방적 접근 방식은 시니어 엔지니어와 Vibe 코더의 특징입니다.