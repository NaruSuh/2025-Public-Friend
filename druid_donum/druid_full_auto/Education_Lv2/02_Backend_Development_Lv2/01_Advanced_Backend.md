# 02 - Backend Development - Lv.2: Advanced API Design and Data Handling

You've built robust APIs. Now it's time to make them smarter, more resilient, and better integrated with the data layer. This level focuses on advanced API patterns, database mastery, and handling data at scale.

## Core Concepts

1.  **Advanced API Patterns**: Move beyond basic CRUD to implement features like pagination, filtering, and real-time communication with WebSockets.
2.  **Database Mastery**: Go deeper than the ORM. Understand database performance, advanced query patterns, and how to manage data migrations.
3.  **Asynchronous Task Queues**: Decouple your API from slow, long-running tasks using a dedicated worker system like Celery.

---

## 1. Advanced FastAPI Patterns

### Pagination
Returning thousands of records in a single API call is slow and inefficient. Pagination is essential.

**Cursor-based Pagination**: More efficient for real-time data than traditional offset-based pagination.
-   The client receives a "cursor" (an opaque identifier, often the ID or timestamp of the last item seen).
-   The next request asks for items "after" that cursor.

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
        last_id = int(base64.b64decode(cursor.encode()).decode())
        query = query.filter(models.User.id > last_id)
    
    users = query.order_by(models.User.id).limit(limit).all()
    
    next_cursor = None
    if users and len(users) == limit:
        last_user_id = users[-1].id
        next_cursor = base64.b64encode(str(last_user_id).encode()).decode()
        
    return {"users": users, "next_cursor": next_cursor}
```

### WebSockets for Real-Time Communication
For features like live notifications or dashboards, WebSockets provide a persistent, two-way communication channel between the client and server.

```python
# endpoints/notifications.py
@router.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket, user: User = Depends(get_current_user)):
    await connection_manager.connect(user.id, websocket) # Your connection manager class
    try:
        while True:
            # You can receive messages from the client if needed
            data = await websocket.receive_text()
            # Or just keep the connection open to push server-side events
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        connection_manager.disconnect(user.id, websocket)
```
You can then have other parts of your application (e.g., a background worker) send messages to users through the `connection_manager`.

---

## 2. Database Mastery with SQLAlchemy and Alembic

### Beyond the ORM: Core Expression Language
For complex queries, dropping down to SQLAlchemy's Core Expression Language gives you the power of SQL with the safety of Python objects.

```python
from sqlalchemy import select, func, and_

# A complex query to get the count of high-value bids per department,
# but only for bids in the last 30 days.
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

### Database Migrations with Alembic
As your application evolves, your database schema will change. `Alembic` is the standard tool for managing these changes programmatically. It's like Git for your database.

1.  **Install**: `pip install alembic`
2.  **Initialize**: `alembic init alembic`
3.  **Configure**: Point `alembic.ini` to your database URL.
4.  **Generate a Migration**: After you change your SQLAlchemy models (e.g., add a new column), run:
    ```bash
    alembic revision --autogenerate -m "Add last_login column to user table"
    ```
    Alembic will compare your models to the database and generate a Python script in `alembic/versions/` with the necessary changes.
5.  **Apply the Migration**:
    ```bash
    alembic upgrade head
    ```
    This applies the changes to your database. You can also downgrade: `alembic downgrade -1`.

---

## 3. Asynchronous Task Queues with Celery

Your crawler is a perfect example of a long-running task that shouldn't block your API. Celery is a powerful, distributed task queue that integrates well with FastAPI.

**Architecture**:
-   **FastAPI App**: The user-facing API. When a long task is needed, it sends a message to the Broker.
-   **Message Broker**: A system like RabbitMQ or Redis that holds messages (tasks) until a worker is ready.
-   **Celery Workers**: Separate Python processes that listen for tasks from the Broker, execute them, and (optionally) store results in a Backend.
-   **Result Backend**: A place (like Redis or a database) to store the results of tasks.

### Example: Offloading a Crawl Job

1.  **Install**: `pip install celery redis`
2.  **Configure Celery**:
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
    ```python
    # tasks.py
    from .celery_app import celery
    from .crawler import run_crawl # Your actual crawl logic

    @celery.task(bind=True)
    def crawl_website_task(self, url: str):
        """A Celery task to run a crawl job."""
        # You can update the task's state for progress tracking
        self.update_state(state='PROGRESS', meta={'status': 'Starting crawl...'})
        
        results = run_crawl(url) # This is your blocking function
        
        return {'status': 'Complete', 'results_summary': f"Found {len(results)} items."}
    ```
4.  **Call the Task from FastAPI**:
    ```python
    # endpoints/crawls.py
    from fastapi import APIRouter
    from celery.result import AsyncResult
    from ..tasks import crawl_website_task

    router = APIRouter()

    @router.post("/start-crawl", status_code=202)
    def start_crawl(url: str):
        # .delay() sends the task to the message broker
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
    ```bash
    celery -A your_project.tasks worker --loglevel=info
    ```

Now, your API can accept crawl jobs instantly, and the heavy work is handled by a scalable pool of background workers, making your application far more responsive and resilient.
