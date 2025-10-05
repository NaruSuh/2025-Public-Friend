# 06 - Performance and Scalability - Lv.2: Distributed Systems and Data Engineering
# 06 - 성능과 확장성 - Lv.2: 분산 시스템과 데이터 엔지니어링

You know how to scale a single application. Level 2 is about designing systems composed of multiple services that can handle data at a massive scale. This involves understanding the challenges of distributed systems and applying data engineering principles.
단일 애플리케이션을 확장하는 법을 알았다면, 레벨 2에서는 여러 서비스로 이루어진 시스템을 설계하여 대규모 데이터를 처리할 수 있게 만드는 법을 배웁니다. 이를 위해 분산 시스템의 난제를 이해하고 데이터 엔지니어링 원칙을 적용해야 합니다.

## Before You Begin
## 시작하기 전에
-   Review Level 1 performance notes on profiling and caching—you’ll reuse those fundamentals inside larger architectures.
-   레벨 1의 프로파일링과 캐싱 노트를 다시 복습하세요. 대형 아키텍처에서도 이 기본기가 필요합니다.
-   Install Docker Compose with Kafka, ZooKeeper, and a database so you can spin up a sandbox cluster on your laptop.
-   Kafka, ZooKeeper, 데이터베이스가 포함된 Docker Compose 구성을 설치해 노트북에서 샌드박스 클러스터를 띄울 수 있게 하세요.
-   Sketch a rough architecture diagram of your current project; you’ll extend it with queues, workers, and warehouses as you learn.
-   현재 프로젝트의 대략적인 아키텍처 다이어그램을 그려 두고, 학습하면서 큐, 워커, 데이터 웨어하우스를 추가해 보세요.

## Level 2 Upgrade Goals
## 레벨 2 업그레이드 목표
1.  **Think in failure modes:** design services that expect partial outages and degraded performance.
1.  **장애 모드를 고려한 사고**: 부분 장애와 성능 저하를 예상하는 서비스를 설계합니다.
2.  **Adopt event-driven patterns** to decouple components and unlock independent scaling.
2.  **이벤트 주도 패턴 채택**: 구성 요소를 느슨하게 결합해 독립적인 확장을 가능하게 합니다.
3.  **Treat data flow as a product** by building repeatable pipelines from OLTP to analytics.
3.  **데이터 흐름을 제품처럼 다루기**: OLTP에서 분석까지 이어지는 반복 가능한 파이프라인을 구축합니다.

## Core Concepts
## 핵심 개념

1.  **Distributed System Challenges**: When you move from a monolith to multiple services, you introduce new problems: network latency, partial failures, and data consistency.
1.  **분산 시스템의 도전 과제**: 모놀리식을 여러 서비스로 나누면 네트워크 지연, 부분 장애, 데이터 일관성 같은 문제가 새로 등장합니다.
2.  **Event-Driven Architecture**: Decoupling services by having them communicate asynchronously through events, rather than direct API calls.
2.  **이벤트 주도 아키텍처**: 직접 API 호출 대신 이벤트 기반 비동기 통신으로 서비스를 느슨하게 연결합니다.
3.  **Data Warehousing and ETL/ELT**: Moving data from your production databases into a specialized analytical database (a data warehouse) for large-scale analysis.
3.  **데이터 웨어하우징과 ETL/ELT**: 프로덕션 데이터베이스의 데이터를 분석용 데이터 웨어하우스로 옮겨 대규모 분석을 수행합니다.
4.  **Batch vs. Stream Processing**: The two primary modes of processing large volumes of data.
4.  **배치 처리 vs. 스트림 처리**: 대량 데이터를 처리하는 두 가지 주요 방식입니다.

---

## 1. Designing Resilient Distributed Systems
## 1. 복원력 있는 분산 시스템 설계하기

### The Circuit Breaker Pattern
### 서킷 브레이커 패턴
In a distributed system, one service calling another can lead to cascading failures. If Service B is slow, Service A's requests to it will pile up, potentially crashing Service A as well.
분산 시스템에서 한 서비스가 다른 서비스를 호출하면 연쇄 장애가 발생할 수 있습니다. 서비스 B가 느리면 서비스 A의 요청이 쌓여 A까지 장애로 이어질 수 있습니다.

A circuit breaker is a component that wraps network calls and monitors them for failures.
서킷 브레이커는 네트워크 호출을 감싸고 실패 여부를 감시하는 구성 요소입니다.
-   **Closed**: Requests flow normally.
-   **Closed**: 요청이 정상적으로 흐릅니다.
-   **Open**: If the failure rate exceeds a threshold, the circuit "opens," and all subsequent calls fail immediately without even making a network request. This protects the calling service.
-   **Open**: 실패율이 임계값을 넘으면 회로가 “열리고”, 이후 호출은 네트워크 요청조차 하지 않고 즉시 실패하여 호출한 서비스를 보호합니다.
-   **Half-Open**: After a timeout, the breaker enters a "half-open" state, allowing a single request through. If it succeeds, the breaker closes. If it fails, it stays open.
-   **Half-Open**: 타임아웃 후 하나의 요청만 통과시키며 성공하면 닫히고 실패하면 열린 상태를 유지합니다.

Libraries like `pybreaker` can implement this pattern in Python.
`pybreaker` 같은 라이브러리는 파이썬에서 이 패턴을 구현할 수 있게 해줍니다.

**Practice:** wrap a flaky external API call in `pybreaker`, then deliberately introduce failures (e.g., via a mock server) to observe the circuit moving through closed → open → half-open states.
**실습:** 불안정한 외부 API 호출을 `pybreaker`로 감싸고, 목 서버 등으로 인위적으로 실패를 유도해 서킷이 Closed→Open→Half-Open으로 이동하는 과정을 관찰하세요.

### Idempotency
### 멱등성
In a distributed system, network errors can mean you don't know if your request was processed or not. You might retry, but what if the first request actually succeeded? An idempotent API is one where making the same request multiple times has the same effect as making it once.
분산 시스템에서는 네트워크 오류로 요청이 처리됐는지 알 수 없는 경우가 많습니다. 재시도할 수 있지만 첫 요청이 이미 성공했다면? 멱등 API는 동일한 요청을 여러 번 보내도 한 번 보낸 것과 같은 결과를 반환합니다.

-   **Example**: A `POST /users` endpoint is not idempotent (it creates a new user each time). A `PUT /users/123` endpoint is idempotent (it updates the same user each time).
-   **예시**: `POST /users`는 호출할 때마다 새 사용자를 만들어 멱등이 아닙니다. `PUT /users/123`는 같은 사용자를 갱신하므로 멱등입니다.
-   **Implementation**: To make a creation endpoint idempotent, you can require the client to generate a unique "idempotency key" (e.g., a UUID) for each transaction. The server then keeps track of processed keys and can safely reject duplicate requests.
-   **구현**: 생성 엔드포인트를 멱등하게 만들려면 클라이언트가 각 거래마다 고유한 “멱등 키”(예: UUID)를 생성하도록 하고, 서버는 처리한 키를 기록하여 중복 요청을 안전하게 거부합니다.

**Checklist:** audit your existing write endpoints and label each one as idempotent or not. For any non-idempotent critical path, draft a plan to add idempotency keys or compensating transactions.
**체크리스트:** 기존 쓰기 엔드포인트를 점검해 멱등 여부를 표시하고, 멱등이 아닌 중요 경로에는 멱등 키 또는 보상 거래를 추가할 계획을 수립하세요.

---

## 2. Event-Driven Architecture with Kafka
## 2. Kafka로 이벤트 주도 아키텍처 구현하기

Instead of services calling each other directly via APIs, they can communicate through a central message bus like Apache Kafka.
서비스끼리 직접 API 호출을 주고받는 대신 Apache Kafka 같은 중앙 메시지 버스를 통해 통신할 수 있습니다.

**How it works**:
**동작 방식**:
-   A service (the **Producer**) produces an "event" (a message, e.g., `UserSignedUp`) and publishes it to a "topic" in Kafka.
-   서비스(프로듀서)가 `UserSignedUp` 같은 이벤트 메시지를 생성해 Kafka의 토픽에 발행합니다.
-   Other services (the **Consumers**) subscribe to that topic and are notified whenever a new event arrives. They can then react accordingly.
-   다른 서비스(컨슈머)는 그 토픽을 구독하고 새 이벤트가 도착하면 알림을 받아 적절히 처리합니다.

**Benefits**:
**장점**:
-   **Decoupling**: The producer doesn't know or care who is listening. You can add new consumer services without changing the producer.
-   **느슨한 결합**: 프로듀서는 누가 듣는지 신경 쓸 필요가 없어 새로운 컨슈머를 추가해도 프로듀서를 수정할 필요가 없습니다.
-   **Resilience**: If a consumer service is down, the events pile up in Kafka. When the service comes back online, it can process the backlog of events.
-   **복원력**: 컨슈머가 다운되어도 이벤트는 Kafka에 쌓이고, 서비스가 복구되면 밀린 이벤트를 처리할 수 있습니다.
-   **Scalability**: Kafka is designed for massive throughput and can be scaled horizontally.
-   **확장성**: Kafka는 대규모 처리량을 위해 설계되어 수평 확장이 용이합니다.

This is a fundamental shift from a "command-driven" (API call) architecture to an "event-driven" one.
이는 “명령 기반”(API 호출) 아키텍처에서 “이벤트 기반” 아키텍처로의 근본적인 전환입니다.

**Practice:** model a single flow (e.g., “bid created”) as an event. Produce events from your existing API and consume them in a separate worker that writes to a log file. Notice how easy it becomes to add additional consumers later.
**실습:** 하나의 흐름(예: “입찰 생성”)을 이벤트로 모델링해 보세요. 기존 API에서 이벤트를 발행하고, 별도의 워커가 이를 소비해 로그 파일에 기록하도록 하면 나중에 다른 소비자를 추가하기 쉬워집니다.

---

## 3. Data Warehousing and ETL
## 3. 데이터 웨어하우징과 ETL

Your production database (OLTP - Online Transaction Processing) is optimized for fast reads and writes of single records. It's terrible for large-scale analytical queries. A Data Warehouse (OLAP - Online Analytical Processing) is a special type of database (like Google BigQuery, Snowflake, or Amazon Redshift) that is designed for fast aggregations over huge datasets.
프로덕션 데이터베이스(OLTP)는 단일 레코드의 빠른 읽기·쓰기에 최적화되어 있어 대규모 분석 쿼리에는 적합하지 않습니다. 데이터 웨어하우스(OLAP)는 Google BigQuery, Snowflake, Amazon Redshift처럼 방대한 데이터셋을 빠르게 집계하도록 설계된 특수 데이터베이스입니다.

**ETL (Extract, Transform, Load)** is the process of getting data into your warehouse.
**ETL(추출, 변환, 적재)**은 데이터를 웨어하우스로 옮기는 과정입니다.
1.  **Extract**: Pull data from your production databases (e.g., a nightly dump).
1.  **Extract**: 프로덕션 데이터베이스에서 데이터를 추출합니다(예: 야간 덤프).
2.  **Transform**: Clean, enrich, and reshape the data into a format suitable for analysis. This is the heavy-lifting part.
2.  **Transform**: 데이터를 정제하고 보강하여 분석에 적합한 형태로 변환합니다. 가장 손이 많이 가는 부분입니다.
3.  **Load**: Load the transformed data into the data warehouse.
3.  **Load**: 변환된 데이터를 데이터 웨어하우스에 적재합니다.

**ELT (Extract, Load, Transform)** is a more modern variation where you load the raw data into the warehouse first and then use the power of the warehouse itself to perform the transformations.
**ELT**는 최신 방식으로, 원시 데이터를 먼저 웨어하우스에 적재하고 그 안에서 변환을 수행합니다.

Tools like **Apache Airflow** are commonly used to orchestrate complex ETL/ELT pipelines. Airflow allows you to define your pipeline as a Directed Acyclic Graph (DAG) of tasks with complex dependencies and scheduling.
**Apache Airflow** 같은 도구를 사용하면 복잡한 ETL/ELT 파이프라인을 오케스트레이션할 수 있습니다. Airflow는 복잡한 의존성과 스케줄을 가진 작업들을 DAG(방향 비순환 그래프)로 정의하게 해줍니다.

**Practice:** build a minimal Airflow DAG that extracts data from SQLite, transforms it with Pandas, and loads it into BigQuery or DuckDB. Schedule it to run every hour and monitor the run history.
**실습:** SQLite에서 데이터를 추출하고 Pandas로 변환한 뒤 BigQuery나 DuckDB에 적재하는 최소한의 Airflow DAG를 만들어 보세요. 매시간 실행되도록 스케줄링하고 실행 이력을 모니터링하세요.

---

## 4. Batch vs. Stream Processing
## 4. 배치 처리와 스트림 처리

### Batch Processing (e.g., with Apache Spark)
### 배치 처리(예: Apache Spark)
-   **What it is**: Processing large, finite datasets.
-   **정의**: 크고 유한한 데이터셋을 일괄 처리합니다.
-   **Example**: A nightly job that calculates the daily active users for your application from a day's worth of log files.
-   **예시**: 매일 로그 파일을 분석해 일일 활성 사용자를 계산하는 야간 작업.
-   **Tooling**: **Apache Spark** is the leading open-source framework for distributed batch processing. It can read data from various sources, perform complex transformations in parallel across a cluster of machines, and write the results out. You can use its Python API (`pyspark`).
-   **도구**: **Apache Spark**는 대표적인 분산 배치 처리 프레임워크로, 다양한 소스에서 데이터를 읽고, 클러스터 전체에서 병렬 변환을 수행하며, 결과를 기록합니다. 파이썬 API인 `pyspark`를 사용할 수 있습니다.

### Stream Processing (e.g., with Kafka Streams or Apache Flink)
### 스트림 처리(예: Kafka Streams, Apache Flink)
-   **What it is**: Processing an infinite stream of data in real-time (or near real-time).
-   **정의**: 실시간 또는 준실시간으로 끝없는 데이터 스트림을 처리합니다.
-   **Example**: A system that continuously monitors a stream of click events from your website to detect fraudulent activity as it happens.
-   **예시**: 웹사이트에서 발생하는 클릭 이벤트 스트림을 실시간으로 감시해 사기 활동을 즉시 탐지하는 시스템.
-   **Tooling**: **Apache Flink** and **Kafka Streams** are popular frameworks for stateful stream processing. They allow you to perform aggregations (like counts or sums) over time windows (e.g., "the number of logins per minute over the last hour").
-   **도구**: **Apache Flink**와 **Kafka Streams**는 상태 기반 스트림 처리를 지원하는 인기 프레임워크로, “지난 한 시간 동안 분당 로그인 수”처럼 시간 창을 기준으로 집계를 수행할 수 있습니다.

By mastering these concepts, you can move beyond building single applications and start designing and building complex, data-intensive systems that are resilient, scalable, and capable of extracting valuable insights from massive volumes of data. This is the domain of the Staff or Principal-level Vibe Coder.
이러한 개념을 익히면 단일 애플리케이션 개발을 넘어 복원력 있고 확장 가능하며 방대한 데이터에서 인사이트를 뽑아내는 복잡한 시스템을 설계하고 구축할 수 있습니다. 이는 스태프 또는 프린시펄 레벨의 Vibe Coder가 다루는 영역입니다.

## Going Further
## 더 나아가기
-   Read "Designing Data-Intensive Applications" chapters 1–4 and summarize CAP theorem trade-offs for your project wiki.
-   『Designing Data-Intensive Applications』 1–4장을 읽고 CAP 정리의 트레이드오프를 프로젝트 위키에 정리하세요.
-   Evaluate managed event buses (e.g., Google Pub/Sub, AWS EventBridge) versus self-hosted Kafka; document the pros/cons for your team.
-   Google Pub/Sub, AWS EventBridge 같은 관리형 이벤트 버스와 자체 호스팅 Kafka를 비교하고 장단점을 팀을 위해 문서화하세요.
-   Run a load test that pushes your stream processor to its limits, then capture how backpressure propagates through the system.
-   스트림 프로세서를 한계까지 밀어붙이는 부하 테스트를 수행하고, 백프레셔가 시스템 전반에 어떻게 전파되는지 기록하세요.
