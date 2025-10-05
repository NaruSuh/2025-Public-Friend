# 02.01 - Building Robust APIs with FastAPI
# 02.01 - FastAPI로 강력한 API 구축하기

FastAPI is an excellent choice for Vibe Coding. It's modern, fast, and leverages Python type hints for validation and documentation. This guide focuses on building robust, production-ready APIs.
FastAPI는 Vibe Coding에 탁월한 선택입니다. 현대적이고 빠르며, 유효성 검사와 문서를 위해 파이썬 타입 힌트를 활용합니다. 이 가이드는 강력하고 프로덕션 준비가 된 API를 구축하는 데 중점을 둡니다.

## Core FastAPI Concepts for Vibe Coders
## Vibe 코더를 위한 핵심 FastAPI 개념

1.  **Pydantic for Validation**: Use Pydantic models to define your data schemas. This gives you "free" data validation, serialization, and documentation.
    **유효성 검사를 위한 Pydantic**: Pydantic 모델을 사용하여 데이터 스키마를 정의합니다. 이를 통해 데이터 유효성 검사, 직렬화 및 문서를 "무료로" 얻을 수 있습니다.
2.  **Dependency Injection (DI)**: Use `Depends` to manage resources, database connections, and authentication. This makes your code modular and easy to test.
    **의존성 주입(DI)**: `Depends`를 사용하여 리소스, 데이터베이스 연결 및 인증을 관리합니다. 이를 통해 코드를 모듈화하고 테스트하기 쉽게 만듭니다.
3.  **Async Endpoints**: Use `async def` for I/O-bound operations (database calls, external API requests) to handle high concurrency.
    **비동기 엔드포인트**: I/O 바운드 작업(데이터베이스 호출, 외부 API 요청)에 `async def`를 사용하여 높은 동시성을 처리합니다.
4.  **Structured Error Handling**: Centralize exception handling to return consistent, meaningful error responses.
    **구조화된 오류 처리**: 예외 처리를 중앙 집중화하여 일관되고 의미 있는 오류 응답을 반환합니다.
5.  **Routers for Organization**: Use `APIRouter` to split your API into logical modules.
    **조직화를 위한 라우터**: `APIRouter`를 사용하여 API를 논리적 모듈로 분할합니다.
6.  **Background Tasks**: Offload long-running operations that the user doesn't need to wait for.
    **백그라운드 작업**: 사용자가 기다릴 필요 없는 오래 실행되는 작업을 오프로드합니다.

---

## Example: A Production-Ready User Service
## 예시: 프로덕션 준비가 된 사용자 서비스

Let's build a simple user creation endpoint that demonstrates these concepts.
이러한 개념을 보여주는 간단한 사용자 생성 엔드포인트를 구축해 보겠습니다.

### 1. Project Structure
### 1. 프로젝트 구조

Organize your code for scalability.
확장성을 위해 코드를 구성합니다.

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
### 2. 스키마 (`schemas/user.py`)

Define the data shapes for your API using Pydantic.
Pydantic을 사용하여 API의 데이터 형태를 정의합니다.

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
    `UserCreate`는 입력 유효성 검사(사용자 생성)를 위한 것입니다.
-   `UserRead` is for output serialization (never expose the password).
    `UserRead`는 출력 직렬화(비밀번호를 절대 노출하지 않음)를 위한 것입니다.
-   `orm_mode = True` (or `from_attributes = True` in Pydantic v2) is key for converting SQLAlchemy models to Pydantic schemas.
    `orm_mode = True`(Pydantic v2에서는 `from_attributes = True`)는 SQLAlchemy 모델을 Pydantic 스키마로 변환하는 데 핵심입니다.

### 3. CRUD Layer (`crud/user.py`)
### 3. CRUD 계층 (`crud/user.py`)

This layer is responsible for direct database interactions. It keeps your business logic clean.
이 계층은 직접적인 데이터베이스 상호 작용을 담당합니다. 비즈니스 로직을 깨끗하게 유지합니다.

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
### 4. 의존성 주입 (`api/dependencies.py`)

Create dependencies that can be injected into your path operations.
경로 작동에 주입할 수 있는 의존성을 만듭니다.

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
### 5. API 엔드포인트 (`api/endpoints/users.py`)

This is the "controller" layer. It handles HTTP requests, calls business logic, and returns responses.
이것은 "컨트롤러" 계층입니다. HTTP 요청을 처리하고, 비즈니스 로직을 호출하며, 응답을 반환합니다.

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
**여기서 일어나는 주요 사항:**
-   `response_model=schemas.UserRead`: FastAPI automatically filters the returned object to match this schema. The `hashed_password` is never sent to the client.
    `response_model=schemas.UserRead`: FastAPI는 반환된 객체를 이 스키마와 일치하도록 자동으로 필터링합니다. `hashed_password`는 클라이언트로 절대 전송되지 않습니다.
-   `Depends(dependencies.get_db)`: The DI system provides a database session and handles its cleanup.
    `Depends(dependencies.get_db)`: DI 시스템은 데이터베이스 세션을 제공하고 정리를 처리합니다.
-   `HTTPException`: The standard way to return HTTP error responses.
    `HTTPException`: HTTP 오류 응답을 반환하는 표준 방법입니다.
-   `BackgroundTasks`: The `send_welcome_email` function will run *after* the response has been sent to the user, preventing a slow email server from blocking the API response.
    `BackgroundTasks`: `send_welcome_email` 함수는 사용자에게 응답이 전송된 *후에* 실행되어 느린 이메일 서버가 API 응답을 차단하는 것을 방지합니다.

### 6. Centralized Error Handling (`main.py`)
### 6. 중앙 집중식 오류 처리 (`main.py`)

You can catch custom exceptions and convert them into structured HTTP responses.
사용자 지정 예외를 포착하여 구조화된 HTTP 응답으로 변환할 수 있습니다.

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
이제 CRUD 계층에서 `DuplicateRecordException`을 발생시키면 FastAPI가 자동으로 이를 포착하여 깔끔한 `409 Conflict` JSON 응답을 반환합니다.

### 7. Putting It All Together (`api/routers.py` and `main.py`)
### 7. 모두 합치기 (`api/routers.py` 및 `main.py`)

Use `APIRouter` to keep your `main.py` clean.
`APIRouter`를 사용하여 `main.py`를 깨끗하게 유지하세요.

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
이 구조는 프로젝트가 성장할 수 있도록 합니다. 더 많은 엔드포인트(예: `items.py`, `orders.py`)를 추가하고 `api_router.py`에 해당 라우터를 포함하기만 하면 됩니다. `main.py`는 최소한으로 유지되며 앱 수준 구성에 중점을 둡니다. 이것이 확장 가능하고 유지 관리 가능한 시스템을 구축하는 본질이며 Vibe Coding의 핵심 신조입니다.