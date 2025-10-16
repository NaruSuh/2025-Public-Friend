# 02 - Backend Development - Lv.2: Advanced API Design and Data Handling
# 02 - 백엔드 개발 - Lv.2: 고급 API 설계와 데이터 처리

You've built robust APIs. Now it's time to make them smarter, more resilient, and better integrated with the data layer. This level focuses on advanced API patterns, database mastery, and handling data at scale.
튼튼한 API를 이미 만들었다면 이제는 더 똑똑하고, 탄탄하며, 데이터 계층과 긴밀하게 통합된 형태로 발전시켜야 합니다. 이 단계에서는 고급 API 패턴, 데이터베이스 숙련도, 대용량 데이터 처리 전략에 집중합니다.

## Before You Begin
## 시작하기 전에
-   Refresh Level 1’s FastAPI module so routing, dependency injection, and Pydantic models are second nature.
-   레벨 1의 FastAPI 모듈을 다시 복습하여 라우팅, 의존성 주입, Pydantic 모델이 자연스럽게 느껴지도록 하세요.
-   Make sure you can run a local PostgreSQL instance (Docker or managed service) and that Alembic is installed globally or in your virtual environment.
-   로컬에서 PostgreSQL 인스턴스를 실행할 수 있고(도커나 관리형 서비스 활용), Alembic이 전역 또는 프로젝트 가상 환경에 설치되어 있는지 확인하세요.
-   Prepare a small demo service (e.g., the Forest crawler API) that you can safely evolve while practicing the advanced topics.
-   실습 중 안전하게 확장할 수 있는 간단한 데모 서비스(예: Forest 크롤러 API)를 마련해 두세요.

## Level 2 Upgrade Goals
## 레벨 2 업그레이드 목표
1.  **Ship production-grade API ergonomics**: pagination, filtering, background work, and real-time updates.
1.  **프로덕션 수준의 API 사용성 제공**: 페이지네이션, 필터링, 백그라운드 작업, 실시간 업데이트를 구현합니다.
2.  **Treat the database as a peer component** by understanding query plans, migrations, and performance knobs.
2.  **데이터베이스를 동등한 구성요소로 다루기**: 쿼리 계획, 마이그레이션, 성능 튜닝 포인트를 이해합니다.
3.  **Introduce asynchronous workers** to keep the main request lifecycle fast for your users.
3.  **비동기 워커 도입하기**: 사용자 요청 흐름을 빠르게 유지하기 위해 백그라운드 워커를 추가합니다.

## Core Concepts
## 핵심 개념

1.  **Advanced API Patterns**: Move beyond basic CRUD to implement features like pagination, filtering, and real-time communication with WebSockets.
1.  **고급 API 패턴**: 기본 CRUD를 넘어 페이지네이션, 필터링, WebSocket 기반 실시간 통신 같은 기능을 구현합니다.
2.  **Database Mastery**: Go deeper than the ORM. Understand database performance, advanced query patterns, and how to manage data migrations.
2.  **데이터베이스 숙련도**: ORM을 넘어 데이터베이스 성능, 고급 쿼리 패턴, 마이그레이션 관리를 이해합니다.
3.  **Asynchronous Task Queues**: Decouple your API from slow, long-running tasks using a dedicated worker system like Celery.
3.  **비동기 작업 큐**: Celery 같은 전용 워커 시스템을 활용해 느린 장기 작업을 API에서 분리합니다.

---

## 1. Advanced FastAPI Patterns
## 1. 고급 FastAPI 패턴

### Pagination
### 페이지네이션
Returning thousands of records in a single API call is slow and inefficient. Pagination is essential.
한 번의 API 호출로 수천 건을 반환하면 느리고 비효율적입니다. 페이지네이션은 필수입니다.

**Cursor-based Pagination**: More efficient for real-time data than traditional offset-based pagination.
**커서 기반 페이지네이션**: 전통적인 오프셋 방식보다 실시간 데이터에 효율적입니다.
-   The client receives a "cursor" (an opaque identifier, often the ID or timestamp of the last item seen).
-   클라이언트는 “커서”(마지막 아이템의 ID나 타임스탬프 같은 식별자)를 전달받습니다.
-   The next request asks for items "after" that cursor.
-   다음 요청은 해당 커서 이후의 데이터를 요청합니다.

```python
# schemas.py
class PaginatedUsers(BaseModel):
    users: List[UserRead]
    next_cursor: Optional[str]

# endpoints/users.py
@router.get("/", response_model=PaginatedUsers)
async def get_users(cursor: Optional[str] = None, limit: int = 20):
    query = db.query(models.User)
    if cursor:
        # Assume cursor is the base64-encoded ID of the last user
        # 커서는 마지막 사용자의 ID를 base64로 인코딩한 것이라고 가정합니다.
        last_id = int(base64.b64decode(cursor.encode()).decode())
        query = query.filter(models.User.id > last_id)
    
    users = query.order_by(models.User.id).limit(limit).all()
    
    next_cursor = None
    if users and len(users) == limit:
        last_user_id = users[-1].id
        next_cursor = base64.b64encode(str(last_user_id).encode()).decode()
        
    return {"users": users, "next_cursor": next_cursor}
```

**Practice:** add cursor pagination to one of your existing list endpoints. Use SQLite with a few hundred seed rows so you can verify the logic quickly before pointing at production data.
**실습:** 기존 목록 엔드포인트 중 하나에 커서 기반 페이지네이션을 추가하고, 수백 건의 샘플 데이터가 담긴 SQLite로 빠르게 검증해 보세요.

### WebSockets for Real-Time Communication
### 실시간 통신을 위한 WebSocket
For features like live notifications or dashboards, WebSockets provide a persistent, two-way communication channel between the client and server.
실시간 알림이나 대시보드 같은 기능에는 WebSocket이 클라이언트와 서버 간 지속적인 양방향 채널을 제공합니다.

```python
# endpoints/notifications.py
@router.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket, user: User = Depends(get_current_user)):
    await connection_manager.connect(user.id, websocket) # Your connection manager class
    try:
        while True:
            # You can receive messages from the client if needed
            # 필요한 경우 클라이언트로부터 메시지를 받을 수 있습니다.
            data = await websocket.receive_text()
            # Or just keep the connection open to push server-side events
            # 또는 서버 측 이벤트를 푸시하기 위해 연결을 열어 둘 수도 있습니다.
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        connection_manager.disconnect(user.id, websocket)
```
You can then have other parts of your application (e.g., a background worker) send messages to users through the `connection_manager`.
이후 애플리케이션의 다른 부분(예: 백그라운드 워커)이 `connection_manager`를 통해 사용자에게 메시지를 보낼 수 있습니다.

**Practice:** build a minimal WebSocket endpoint that broadcasts the progress of a Celery task (below) so you can observe the round trip end-to-end.
**실습:** 아래 Celery 작업의 진행 상황을 방송하는 최소한의 WebSocket 엔드포인트를 만들어 엔드투엔드 동작을 확인해 보세요.

---

## 2. Database Mastery with SQLAlchemy and Alembic
## 2. SQLAlchemy와 Alembic으로 데이터베이스 깊이 파고들기

### Beyond the ORM: Core Expression Language
### ORM을 넘어: 코어 표현 언어
For complex queries, dropping down to SQLAlchemy's Core Expression Language gives you the power of SQL with the safety of Python objects.
복잡한 쿼리를 다룰 때는 SQLAlchemy의 코어 표현 언어를 사용하면 SQL의 강력함과 파이썬 객체의 안전성을 동시에 얻을 수 있습니다.

```python
from sqlalchemy import select, func, and_

# A complex query to get the count of high-value bids per department,
# but only for bids in the last 30 days.
# 부서별 고가 입찰 수를 가져오는 복잡한 쿼리,
# 단, 지난 30일 동안의 입찰에 대해서만.
thirty_days_ago = datetime.utcnow() - timedelta(days=30)
high_value_threshold = 1000

stmt = (
    select(
        models.Bid.department,
        func.count(models.Bid.id).label("high_value_bid_count")
    )
    .where(
        and_(
            models.Bid.views > high_value_threshold,
            models.Bid.post_date >= thirty_days_ago
        )
    )
    .group_by(models.Bid.department)
    .order_by(func.count(models.Bid.id).desc())
)

results = db.execute(stmt).all()
```

**Practice:** profile this query with `EXPLAIN ANALYZE` in PostgreSQL. Copy the plan into a notebook and annotate which parts correspond to your SQLAlchemy expression.
**실습:** PostgreSQL에서 `EXPLAIN ANALYZE`로 이 쿼리를 프로파일링하고 결과 플랜을 노트에 복사한 뒤, 각 단계가 SQLAlchemy 표현에서 어떤 부분과 연결되는지 주석을 달아보세요.

### Database Migrations with Alembic
### Alembic을 활용한 데이터베이스 마이그레이션
As your application evolves, your database schema will change. `Alembic` is the standard tool for managing these changes programmatically. It's like Git for your database.
애플리케이션이 성장하면 데이터베이스 스키마도 변합니다. `Alembic`은 이러한 변화를 코드로 관리하는 표준 도구로, 데이터베이스용 Git이라 할 수 있습니다.

1.  **Install**: `pip install alembic`
1.  **설치**: `pip install alembic`
2.  **Initialize**: `alembic init alembic`
2.  **초기화**: `alembic init alembic`
3.  **Configure**: Point `alembic.ini` to your database URL.
3.  **설정**: `alembic.ini`의 데이터베이스 URL을 프로젝트에 맞게 수정합니다.
4.  **Generate a Migration**: After you change your SQLAlchemy models (e.g., add a new column), run:
4.  **마이그레이션 생성**: SQLAlchemy 모델을 변경한 뒤(예: 새 컬럼 추가) 다음을 실행합니다.
    ```bash
    alembic revision --autogenerate -m "Add last_login column to user table"
    ```
    Alembic will compare your models to the database and generate a Python script in `alembic/versions/` with the necessary changes.
    그러면 Alembic이 모델과 데이터베이스를 비교해 필요한 변경 사항을 `alembic/versions/`에 파이썬 스크립트로 생성합니다.
5.  **Apply the Migration**:
5.  **마이그레이션 적용**:
    ```bash
    alembic upgrade head
    ```
    This applies the changes to your database. You can also downgrade: `alembic downgrade -1`.
    위 명령으로 데이터베이스에 변경 사항을 적용합니다. 필요하면 `alembic downgrade -1`로 되돌릴 수도 있습니다.

**Checklist:** keep a running `alembic/README.md` that documents why each migration exists and how to verify it locally. Future you (or a teammate) will thank you.
**체크리스트:** 각 마이그레이션의 목적과 로컬 검증 방법을 기록한 `alembic/README.md`를 유지하세요. 훗날 스스로(또는 팀원)가 크게 도움이 됩니다.

---

## 3. Asynchronous Task Queues with Celery
## 3. Celery로 비동기 작업 큐 구성하기

Your crawler is a perfect example of a long-running task that shouldn't block your API. Celery is a powerful, distributed task queue that integrates well with FastAPI.
크롤러는 API를 막아서는 안 되는 대표적인 장기 작업입니다. Celery는 FastAPI와 잘 어울리는 강력한 분산 작업 큐입니다.

**Architecture**:
**구조**:
-   **FastAPI App**: The user-facing API. When a long task is needed, it sends a message to the Broker.
-   **FastAPI 앱**: 사용자와 맞닿아 있으며, 장기 작업이 필요하면 브로커로 메시지를 보냅니다.
-   **Message Broker**: A system like RabbitMQ or Redis that holds messages (tasks) until a worker is ready.
-   **메시지 브로커**: RabbitMQ나 Redis처럼 워커가 처리할 준비가 될 때까지 작업을 보관합니다.
-   **Celery Workers**: Separate Python processes that listen for tasks from the Broker, execute them, and (optionally) store results in a Backend.
-   **Celery 워커**: 브로커에서 작업을 수신하고 실행하며(필요 시) 결과를 백엔드에 저장하는 별도의 파이썬 프로세스입니다.
-   **Result Backend**: A place (like Redis or a database) to store the results of tasks.
-   **결과 백엔드**: Redis나 데이터베이스처럼 작업 결과를 저장하는 공간입니다.

### Example: Offloading a Crawl Job
### 예시: 크롤 작업 분리하기

1.  **Install**: `pip install celery redis`
1.  **설치**: `pip install celery redis`
2.  **Configure Celery**:
2.  **Celery 설정**:
    ```python
    # celery_app.py
    from celery import Celery

    celery = Celery(
        "tasks",
        broker="redis://localhost:6379/0",
        backend="redis://localhost:6379/0"
    )

    celery.conf.update(
        task_track_started=True,
    )
    ```
3.  **Create a Task**:
3.  **작업 생성**:
    ```python
    # tasks.py
    from .celery_app import celery
    from .crawler import run_crawl  # 실제 크롤 로직

    @celery.task(bind=True)
    def crawl_website_task(self, url: str):
        """크롤 작업을 실행하는 Celery 태스크"""
        # 진행 상황 추적을 위해 상태를 업데이트할 수 있습니다.
        self.update_state(state='PROGRESS', meta={'status': 'Starting crawl...'})
        
        results = run_crawl(url)  # 블로킹 함수 호출
        
        return {'status': 'Complete', 'results_summary': f"Found {len(results)} items."}
    ```

**Practice:** wire this task into an endpoint that immediately returns a job ID. Poll a status route (or push updates through the WebSocket above) until the job completes. Notice how the API stays responsive.
**실습:** 이 태스크를 즉시 작업 ID를 반환하는 엔드포인트에 연결하고, 작업 완료까지 상태 라우트를 폴링하거나 위 WebSocket을 통해 진행 상황을 푸시해 보세요. API가 얼마나 빠르게 유지되는지 확인해 보세요.

## Going Further
## 더 나아가기
-   Build a “traffic replay” script that sends production-like load to your API and observes latency changes after adding pagination and Celery.
-   프로덕션과 비슷한 부하를 API에 가하는 “트래픽 리플레이” 스크립트를 작성하고, 페이지네이션과 Celery 도입 후 지연이 어떻게 변하는지 관찰하세요.
-   Explore FastAPI dependencies that open and close database sessions per request; benchmark against long-lived sessions.
-   요청마다 데이터베이스 세션을 열고 닫는 FastAPI 의존성 패턴을 살펴보고, 장기간 유지되는 세션과 성능을 비교해 보세요.
-   Read the "High Performance Python" chapter on async I/O to understand when to combine Celery with async endpoints vs. staying synchronous.
-   『High Performance Python』의 비동기 I/O 챕터를 읽고 Celery를 비동기 엔드포인트와 결합할지, 동기 방식으로 유지할지를 판단하는 기준을 세우세요.

4.  **Call the Task from FastAPI**:
4.  **FastAPI에서 태스크 호출하기**:
    ```python
    # endpoints/crawls.py
    from fastapi import APIRouter
    from celery.result import AsyncResult
    from ..tasks import crawl_website_task

    router = APIRouter()

    @router.post("/start-crawl", status_code=202)
    def start_crawl(url: str):
        # .delay()는 작업을 메시지 브로커로 보냅니다.
        task = crawl_website_task.delay(url)
        return {"task_id": task.id}

    @router.get("/crawl-status/{task_id}")
    def get_crawl_status(task_id: str):
        task_result = AsyncResult(task_id, app=crawl_website_task.app)
        return {
            "task_id": task_id,
            "state": task_result.state,
            "details": task_result.info,
        }
    ```
5.  **Run the Worker**:
5.  **워커 실행하기**:
    ```bash
    celery -A your_project.tasks worker --loglevel=info
    ```

Now, your API can accept crawl jobs instantly, and the heavy work is handled by a scalable pool of background workers, making your application far more responsive and resilient.
이제 API는 크롤 작업을 즉시 받아들이며, 무거운 작업은 확장 가능한 백그라운드 워커 풀에서 처리하므로 애플리케이션이 훨씬 빠르고 탄탄해집니다.