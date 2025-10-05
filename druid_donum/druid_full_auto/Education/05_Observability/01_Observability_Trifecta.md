# 05.01 - Observability: Logging, Metrics, and Tracing

In Vibe Coding, you build systems to last. A running application is a black box unless you make it observable. Observability is the practice of instrumenting your code so you can ask arbitrary questions about its state and behavior without having to ship new code. It's built on three pillars: **Logging**, **Metrics**, and **Tracing**.

## The Three Pillars of Observability

1.  **Logging**:
    -   **What it is**: A record of a discrete event that happened at a specific time.
    -   **Use case**: Answering "What happened?". Debugging specific errors, understanding the lifecycle of a single request.
    -   **Vibe Coder approach**: Use **structured logging** (JSON) so logs are machine-parseable.

2.  **Metrics**:
    -   **What it is**: A numeric, aggregatable measurement of the system's health over time (e.g., request count, error rate, CPU usage).
    -   **Use case**: Answering "How is the system doing overall?". Creating dashboards, setting up alerts on trends (e.g., "error rate is over 5%").
    -   **Vibe Coder approach**: Expose a `/metrics` endpoint in a standardized format (like Prometheus).

3.  **Tracing**:
    -   **What it is**: A representation of the entire journey of a request as it moves through different services or components.
    -   **Use case**: Answering "Where is the bottleneck?". Pinpointing latency issues in a distributed system.
    -   **Vibe Coder approach**: Integrate an OpenTelemetry-compatible library to automatically propagate trace contexts.

---

## 1. Structured Logging in Python

Plain text logs are for humans. JSON logs are for machines. Machines are better and faster at parsing logs.

Let's set up structured logging for a FastAPI application using the `structlog` library.

**Install it**: `pip install structlog`

**Configure it in your app**:

```python
# core/logging_config.py
import logging
import sys
import structlog

def configure_logging():
    """
    Configure structured logging for the application.
    """
    # Base Python logging configuration
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    # structlog configuration
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # The key step for JSON output
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

# In your main.py
from .core.logging_config import configure_logging

configure_logging()
logger = structlog.get_logger(__name__)

app = FastAPI()

@app.get("/")
def read_root():
    logger.info("root_endpoint_called", user_ip="127.0.0.1")
    return {"Hello": "World"}
```

When you run this, the log output will be a JSON object:
```json
{"event": "root_endpoint_called", "user_ip": "127.0.0.1", "log_level": "info", "timestamp": "2025-10-05T12:00:00.123456Z", ...}
```
This is now trivial to ingest into a log management system like Elasticsearch, Datadog, or Loki.

---

## 2. Exposing Metrics with Prometheus

Prometheus is the de-facto standard for metrics collection. It works by "scraping" a `/metrics` endpoint on your application at regular intervals.

Let's add a metrics endpoint to our FastAPI app.

**Install it**: `pip install prometheus-fastapi-instrumentator`

**Instrument your app**:

```python
# main.py
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# This line does all the magic.
# It exposes a /metrics endpoint and instruments your API endpoints.
Instrumentator().instrument(app).expose(app)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int):
    if item_id == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item_id": item_id}
```

Now, if you run your app and go to `http://localhost:8000/metrics`, you'll see output like this:

```
# HELP http_requests_latency_seconds HTTP request latency
# TYPE http_requests_latency_seconds histogram
http_requests_latency_seconds_bucket{handler="/",method="GET",status="200",le="0.005"} 1.0
...
# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{handler="/",method="GET",status="200"} 5.0
http_requests_total{handler="/items/{item_id}",method="GET",status="404"} 2.0
```

This provides a wealth of information out of the box:
-   Request latency (as a histogram).
-   Request counts, broken down by endpoint, method, and status code.

You can then point a Prometheus server at this endpoint and use Grafana to build dashboards and set up alerts (e.g., "Alert me if the rate of 5xx errors is > 1% for 5 minutes").

---

## 3. Distributed Tracing with OpenTelemetry

Tracing is essential for microservices but is also incredibly useful in a monolith for understanding the flow through different layers (e.g., API -> service -> database).

OpenTelemetry is the emerging standard for tracing.

**Install it**:
```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi
```

**Instrument your app**:

```python
# main.py
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

# Set up the tracer provider
provider = TracerProvider()
# Export traces to the console for demonstration
processor = BatchSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

app = FastAPI()

# This automatically instruments incoming requests
FastAPIInstrumentor.instrument_app(app)

tracer = trace.get_tracer(__name__)

def some_database_call():
    # Create a custom span to trace a specific operation
    with tracer.start_as_current_span("database_query") as span:
        span.set_attribute("db.statement", "SELECT * FROM users")
        # ... actual db call ...
        time.sleep(0.1)

@app.get("/")
def read_root():
    some_database_call()
    return {"Hello": "World"}
```

When you hit the `/` endpoint, you'll see console output representing the trace:
-   A **parent span** for the incoming HTTP request to `/`.
-   A **child span** for the `database_query` operation.

Each span has a start time, end time, and metadata. A tracing backend (like Jaeger or Datadog) can visualize this as a flame graph, showing you exactly where time was spent during the request.

By implementing these three pillars, you move from reactive debugging ("something is broken, let's check the logs") to proactive analysis ("what is the p95 latency for user signups, and how does it correlate with CPU usage?"). This is the mark of a mature, production-ready system and a core competency of a Vibe Coder.
