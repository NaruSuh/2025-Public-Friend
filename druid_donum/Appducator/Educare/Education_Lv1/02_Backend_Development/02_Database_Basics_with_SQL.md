# 02.02 - Database Basics with SQL and SQLAlchemy
# 02.02 - SQL 및 SQLAlchemy를 사용한 데이터베이스 기초

For most applications, data needs to persist. Databases are how we store, retrieve, and manage data in a structured way. This guide covers the basics of SQL (the language of databases) and SQLAlchemy (the primary tool for working with databases in Python).
대부분의 애플리케이션에서 데이터는 유지되어야 합니다. 데이터베이스는 구조화된 방식으로 데이터를 저장, 검색 및 관리하는 방법입니다. 이 가이드는 SQL(데이터베이스 언어) 및 SQLAlchemy(파이썬에서 데이터베이스 작업을 위한 기본 도구)의 기본 사항을 다룹니다.

## Core Concepts
## 핵심 개념

1.  **Relational Database**: A database that organizes data into tables with rows and columns. Each table has a defined schema (the columns and their data types).
    **관계형 데이터베이스**: 데이터를 행과 열이 있는 테이블로 구성하는 데이터베이스입니다. 각 테이블에는 정의된 스키마(열 및 해당 데이터 유형)가 있습니다.
2.  **SQL (Structured Query Language)**: The standard language for interacting with relational databases. The main commands are `SELECT`, `INSERT`, `UPDATE`, and `DELETE`.
    **SQL(구조적 쿼리 언어)**: 관계형 데이터베이스와 상호 작용하기 위한 표준 언어입니다. 주요 명령어는 `SELECT`, `INSERT`, `UPDATE`, `DELETE`입니다.
3.  **Primary Key**: A unique identifier for each row in a table (e.g., an `id` column).
    **기본 키**: 테이블의 각 행에 대한 고유 식별자입니다(예: `id` 열).
4.  **Foreign Key**: A key used to link two tables together. It's a field in one table that refers to the primary key of another table.
    **외래 키**: 두 테이블을 함께 연결하는 데 사용되는 키입니다. 한 테이블의 필드이며 다른 테이블의 기본 키를 참조합니다.
5.  **ORM (Object-Relational Mapper)**: A library like SQLAlchemy that lets you interact with your database using Python objects instead of writing raw SQL strings. This makes your code more readable, maintainable, and secure.
    **ORM(객체 관계 매퍼)**: 원시 SQL 문자열을 작성하는 대신 파이썬 객체를 사용하여 데이터베이스와 상호 작용할 수 있게 해주는 SQLAlchemy와 같은 라이브러리입니다. 이렇게 하면 코드를 더 읽기 쉽고 유지 관리하기 쉬우며 안전하게 만들 수 있습니다.

---

## 1. Designing Your Schema with SQLAlchemy
## 1. SQLAlchemy로 스키마 설계하기

SQLAlchemy allows you to define your database tables as Python classes. This is called the **declarative model**.
SQLAlchemy를 사용하면 데이터베이스 테이블을 파이썬 클래스로 정의할 수 있습니다. 이를 **선언적 모델**이라고 합니다.

Let's define two related tables: `User` and `Item`. A user can have many items.
관련된 두 테이블인 `User`와 `Item`을 정의해 보겠습니다. 사용자는 여러 항목을 가질 수 있습니다.

```python
# src/models/base.py
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# src/models/user.py
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    # This creates the relationship to the Item model
    items = relationship("Item", back_populates="owner")

# src/models/item.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    # This is the foreign key linking to the users table
    owner_id = Column(Integer, ForeignKey("users.id"))

    # This creates the relationship back to the User model
    owner = relationship("User", back_populates="items")
```

**Key elements:**
**주요 요소:**
-   `__tablename__`: The actual name of the table in the database.
    `__tablename__`: 데이터베이스에 있는 테이블의 실제 이름입니다.
-   `Column`: Defines a column with a specific data type (`Integer`, `String`, etc.).
    `Column`: 특정 데이터 유형(`Integer`, `String` 등)으로 열을 정의합니다.
-   `primary_key=True`: Marks this column as the primary key.
    `primary_key=True`: 이 열을 기본 키로 표시합니다.
-   `ForeignKey("users.id")`: Creates the link to the `id` column in the `users` table.
    `ForeignKey("users.id")`: `users` 테이블의 `id` 열에 대한 링크를 만듭니다.
-   `relationship`: Defines the object-oriented view of the link. It lets you access `user.items` (a list of Item objects) and `item.owner` (a User object) directly in Python.
    `relationship`: 링크의 객체 지향 뷰를 정의합니다. 파이썬에서 직접 `user.items`(Item 객체 목록) 및 `item.owner`(User 객체)에 액세스할 수 있습니다.

---

## 2. Connecting to the Database
## 2. 데이터베이스에 연결하기

You need to create a database "engine" and a "session maker".
데이터베이스 "엔진"과 "세션 메이커"를 만들어야 합니다.

```python
# src/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# The database URL. For this example, we use SQLite.
# For PostgreSQL, it would be: "postgresql://user:password@host/dbname"
SQLALCHEMY_DATABASE_URL = "sqlite:///./vibe_project.db"

# The engine is the entry point to the database.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    # connect_args is only needed for SQLite
    connect_args={"check_same_thread": False}
)

# The SessionLocal class is a factory for creating new Session objects.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# You also need to create the tables from your models
from .models.base import Base
from .models.user import User
from .models.item import Item

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
```

## 3. CRUD Operations with the ORM
## 3. ORM을 사용한 CRUD 작업

CRUD stands for Create, Read, Update, Delete. These are the fundamental operations you perform on data. With an ORM, you do this using a `Session` object.
CRUD는 생성, 읽기, 업데이트, 삭제를 의미합니다. 이것들은 데이터에 대해 수행하는 기본적인 작업입니다. ORM을 사용하면 `Session` 객체를 사용하여 이 작업을 수행합니다.

Let's look at the `crud/user.py` file from the FastAPI guide.
FastAPI 가이드의 `crud/user.py` 파일을 살펴보겠습니다.

```python
# src/crud/user.py
from sqlalchemy.orm import Session
from .. import models, schemas

# READ operation
def get_user_by_email(db: Session, email: str):
    # The session object can build queries.
    # .query(models.User) is like "SELECT * FROM users"
    # .filter() is the WHERE clause.
    # .first() gets the first result or None.
    return db.query(models.User).filter(models.User.email == email).first()

# CREATE operation
def create_user(db: Session, user: schemas.UserCreate):
    # Create a Python instance of the model
    db_user = models.User(
        email=user.email, 
        hashed_password=get_password_hash(user.password)
    )
    # Add the object to the session
    db.add(db_user)
    # Commit the transaction to the database
    db.commit()
    # Refresh the object to get the new ID from the database
    db.refresh(db_user)
    return db_user

# UPDATE operation (example)
def update_user_activity(db: Session, user_id: int, is_active: bool) -> models.User:
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db_user.is_active = is_active
        db.commit()
        db.refresh(db_user)
    return db_user

# DELETE operation (example)
def delete_user(db: Session, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user
```

### The Session Lifecycle
### 세션 수명 주기

This is a critical concept for web applications.
이것은 웹 애플리케이션에 대한 중요한 개념입니다.

1.  **Create Session**: A new session is created when a request comes in.
    **세션 생성**: 요청이 들어오면 새 세션이 생성됩니다.
2.  **Perform Operations**: Your CRUD functions use the session to query, add, update, or delete objects.
    **작업 수행**: CRUD 함수는 세션을 사용하여 객체를 쿼리, 추가, 업데이트 또는 삭제합니다.
3.  **Commit or Rollback**: If all operations are successful, the transaction is `commit()`-ed to the database. If an error occurs, the transaction is rolled back, leaving the database in its original state.
    **커밋 또는 롤백**: 모든 작업이 성공하면 트랜잭션이 데이터베이스에 `commit()`됩니다. 오류가 발생하면 트랜잭션이 롤백되어 데이터베이스가 원래 상태로 남습니다.
4.  **Close Session**: The session is closed after the request is finished.
    **세션 닫기**: 요청이 완료된 후 세션이 닫힙니다.

FastAPI's dependency injection system is perfect for managing this lifecycle, as shown in the `get_db` dependency in the previous guide.
FastAPI의 의존성 주입 시스템은 이전 가이드의 `get_db` 의존성에서 보여주듯이 이 수명 주기를 관리하는 데 완벽합니다.

By using an ORM like SQLAlchemy, you abstract away the raw SQL, reduce the risk of SQL injection vulnerabilities, and create a more Pythonic, maintainable data access layer. This is a cornerstone of building robust, data-driven applications.
SQLAlchemy와 같은 ORM을 사용하면 원시 SQL을 추상화하고 SQL 주입 취약점의 위험을 줄이며 더 파이썬스럽고 유지 관리하기 쉬운 데이터 액세스 계층을 만들 수 있습니다. 이것은 강력하고 데이터 기반 애플리케이션을 구축하는 초석입니다.