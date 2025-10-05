# 06 - Performance and Scalability - Lv.2: Distributed Systems and Data Engineering

You know how to scale a single application. Level 2 is about designing systems composed of multiple services that can handle data at a massive scale. This involves understanding the challenges of distributed systems and applying data engineering principles.

## Core Concepts

1.  **Distributed System Challenges**: When you move from a monolith to multiple services, you introduce new problems: network latency, partial failures, and data consistency.
2.  **Event-Driven Architecture**: Decoupling services by having them communicate asynchronously through events, rather than direct API calls.
3.  **Data Warehousing and ETL/ELT**: Moving data from your production databases into a specialized analytical database (a data warehouse) for large-scale analysis.
4.  **Batch vs. Stream Processing**: The two primary modes of processing large volumes of data.

---

## 1. Designing Resilient Distributed Systems

### The Circuit Breaker Pattern
In a distributed system, one service calling another can lead to cascading failures. If Service B is slow, Service A's requests to it will pile up, potentially crashing Service A as well.

A circuit breaker is a component that wraps network calls and monitors them for failures.
-   **Closed**: Requests flow normally.
-   **Open**: If the failure rate exceeds a threshold, the circuit "opens," and all subsequent calls fail immediately without even making a network request. This protects the calling service.
-   **Half-Open**: After a timeout, the breaker enters a "half-open" state, allowing a single request through. If it succeeds, the breaker closes. If it fails, it stays open.

Libraries like `pybreaker` can implement this pattern in Python.

### Idempotency
In a distributed system, network errors can mean you don't know if your request was processed or not. You might retry, but what if the first request actually succeeded? An idempotent API is one where making the same request multiple times has the same effect as making it once.

-   **Example**: A `POST /users` endpoint is not idempotent (it creates a new user each time). A `PUT /users/123` endpoint is idempotent (it updates the same user each time).
-   **Implementation**: To make a creation endpoint idempotent, you can require the client to generate a unique "idempotency key" (e.g., a UUID) for each transaction. The server then keeps track of processed keys and can safely reject duplicate requests.

---

## 2. Event-Driven Architecture with Kafka

Instead of services calling each other directly via APIs, they can communicate through a central message bus like Apache Kafka.

**How it works**:
-   A service (the **Producer**) produces an "event" (a message, e.g., `UserSignedUp`) and publishes it to a "topic" in Kafka.
-   Other services (the **Consumers**) subscribe to that topic and are notified whenever a new event arrives. They can then react accordingly.

**Benefits**:
-   **Decoupling**: The producer doesn't know or care who is listening. You can add new consumer services without changing the producer.
-   **Resilience**: If a consumer service is down, the events pile up in Kafka. When the service comes back online, it can process the backlog of events.
-   **Scalability**: Kafka is designed for massive throughput and can be scaled horizontally.

This is a fundamental shift from a "command-driven" (API call) architecture to an "event-driven" one.

---

## 3. Data Warehousing and ETL

Your production database (OLTP - Online Transaction Processing) is optimized for fast reads and writes of single records. It's terrible for large-scale analytical queries. A Data Warehouse (OLAP - Online Analytical Processing) is a special type of database (like Google BigQuery, Snowflake, or Amazon Redshift) that is designed for fast aggregations over huge datasets.

**ETL (Extract, Transform, Load)** is the process of getting data into your warehouse.
1.  **Extract**: Pull data from your production databases (e.g., a nightly dump).
2.  **Transform**: Clean, enrich, and reshape the data into a format suitable for analysis. This is the heavy-lifting part.
3.  **Load**: Load the transformed data into the data warehouse.

**ELT (Extract, Load, Transform)** is a more modern variation where you load the raw data into the warehouse first and then use the power of the warehouse itself to perform the transformations.

Tools like **Apache Airflow** are commonly used to orchestrate complex ETL/ELT pipelines. Airflow allows you to define your pipeline as a Directed Acyclic Graph (DAG) of tasks with complex dependencies and scheduling.

---

## 4. Batch vs. Stream Processing

### Batch Processing (e.g., with Apache Spark)
-   **What it is**: Processing large, finite datasets.
-   **Example**: A nightly job that calculates the daily active users for your application from a day's worth of log files.
-   **Tooling**: **Apache Spark** is the leading open-source framework for distributed batch processing. It can read data from various sources, perform complex transformations in parallel across a cluster of machines, and write the results out. You can use its Python API (`pyspark`).

### Stream Processing (e.g., with Kafka Streams or Apache Flink)
-   **What it is**: Processing an infinite stream of data in real-time (or near real-time).
-   **Example**: A system that continuously monitors a stream of click events from your website to detect fraudulent activity as it happens.
-   **Tooling**: **Apache Flink** and **Kafka Streams** are popular frameworks for stateful stream processing. They allow you to perform aggregations (like counts or sums) over time windows (e.g., "the number of logins per minute over the last hour").

By mastering these concepts, you can move beyond building single applications and start designing and building complex, data-intensive systems that are resilient, scalable, and capable of extracting valuable insights from massive volumes of data. This is the domain of the Staff or Principal-level Vibe Coder.
