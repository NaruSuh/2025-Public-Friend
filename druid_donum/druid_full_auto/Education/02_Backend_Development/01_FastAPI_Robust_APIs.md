# 02.01 - Building Robust APIs with FastAPI

FastAPI is an excellent choice for Vibe Coding. It's modern, fast, and leverages Python type hints for validation and documentation. This guide focuses on building robust, production-ready APIs.

## Core FastAPI Concepts for Vibe Coders

1.  **Pydantic for Validation**: Use Pydantic models to define your data schemas. This gives you "free" data validation, serialization, and documentation.
2.  **Dependency Injection (DI)**: Use `Depends` to manage resources, database connections, and authentication. This makes your code modular and easy to test.
3.  **Async Endpoints**: Use `async def` for I/O-bound operations (database calls, external API requests) to handle high concurrency.
4.  **Structured Error Handling**: Centralize exception handling to return consistent, meaningful error responses.
5.  **Routers for Organization**: Use `APIRouter` to split your API into logical modules.
6.  **Background Tasks**: Offload long-running operations that the user doesn't need to wait for.

---

## Example: A Production-Ready User Service

Let's build a simple user creation endpoint that demonstrates these concepts.

### 1. Project Structure

Organize your code for scalability.

```
my-vibe-project/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints/
│   │   │   ├── __init__.py
│   │   │   └── users.py
│   │   └── routers.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── security.py
│   ├── crud/
│   │   ├── __init__.py
│   │   └── user.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── user.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── email_service.py
│   └── main.py
├── tests/
└── pyproject.toml
```

### 2. Schemas (`schemas/user.py`)

Define the data shapes for your API using Pydantic.

```python
# schemas/user.py
from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserRead(UserBase):
    id: int

    class Config:
        orm_mode = True # Allows mapping from ORM models
```
-   `UserCreate` is for input validation (creating a user).
-   `UserRead` is for output serialization (never expose the password).
-   `orm_mode = True` (or `from_attributes = True` in Pydantic v2) is key for converting SQLAlchemy models to Pydantic schemas.

### 3. CRUD Layer (`crud/user.py`)

This layer is responsible for direct database interactions. It keeps your business logic clean.

```python
# crud/user.py
from sqlalchemy.orm import Session
from .. import models, schemas
from ..core.security import get_password_hash

# This is a synchronous example. In a real async app, you'd use an async DB driver.
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
```

### 4. Dependency Injection (`api/dependencies.py`)

Create dependencies that can be injected into your path operations.

```python
# api/dependencies.py
from sqlalchemy.orm import Session
from ..database import SessionLocal # Assume you have this setup

def get_db():
    """
    Dependency that provides a database session.
    It ensures the session is always closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 5. API Endpoint (`api/endpoints/users.py`)

This is the "controller" layer. It handles HTTP requests, calls business logic, and returns responses.

```python
# api/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from ... import crud, schemas, services
from .. import dependencies

router = APIRouter()

@router.post("/", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    user_in: schemas.UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(dependencies.get_db),
):
    """
    Create a new user and send a welcome email.
    """
    db_user = crud.get_user_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )
    
    # The actual creation logic is in the CRUD layer
    created_user = crud.create_user(db=db, user=user_in)

    # Offload slow tasks to the background
    background_tasks.add_task(
        services.email_service.send_welcome_email,
        email_to=created_user.email,
        name=created_user.email.split('@')[0]
    )

    return created_user
```
**Key things happening here:**
-   `response_model=schemas.UserRead`: FastAPI automatically filters the returned object to match this schema. The `hashed_password` is never sent to the client.
-   `Depends(dependencies.get_db)`: The DI system provides a database session and handles its cleanup.
-   `HTTPException`: The standard way to return HTTP error responses.
-   `BackgroundTasks`: The `send_welcome_email` function will run *after* the response has been sent to the user, preventing a slow email server from blocking the API response.

### 6. Centralized Error Handling (`main.py`)

You can catch custom exceptions and convert them into structured HTTP responses.

```python
# main.py
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from .api.routers import api_router
from .crud.exceptions import DuplicateRecordException # A custom exception

app = FastAPI()

@app.exception_handler(DuplicateRecordException)
async def duplicate_record_exception_handler(request: Request, exc: DuplicateRecordException):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"message": f"Conflict: {exc.detail}"},
    )

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "ok"}
```
Now, if your CRUD layer raises `DuplicateRecordException`, FastAPI will automatically catch it and return a clean `409 Conflict` JSON response.

### 7. Putting It All Together (`api/routers.py` and `main.py`)

Use `APIRouter` to keep your `main.py` clean.

```python
# api/routers.py
from fastapi import APIRouter
from .endpoints import users

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["Users"])

# main.py
from fastapi import FastAPI
from .api.routers import api_router

app = FastAPI(title="My Vibe Project API")
app.include_router(api_router, prefix="/api/v1")
```

This structure allows your project to grow. You can add more endpoints (e.g., `items.py`, `orders.py`) and simply include their routers in `api_router.py`. Your `main.py` remains minimal and focused on app-level configuration. This is the essence of building scalable and maintainable systems—a core tenet of Vibe Coding.
