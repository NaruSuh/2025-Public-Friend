# 05.01 - The Observability Trifecta: Logs, Metrics, and Traces
# 05.01 - 관찰 가능성 3요소: 로그, 메트릭, 트레이스

Observability is about being able to understand the internal state of your system from the outside. It's how you answer the question, "Why is this happening?" For a Vibe Coder, it's not an afterthought; it's designed into the system from the beginning.
관찰 가능성은 외부에서 시스템의 내부 상태를 이해할 수 있는 능력에 관한 것입니다. "이것이 왜 일어나고 있는가?"라는 질문에 답하는 방법입니다. Vibe 코더에게 이것은 나중에 생각할 것이 아닙니다. 처음부터 시스템에 설계되어 있습니다.

## The Three Pillars of Observability
## 관찰 가능성의 세 가지 기둥

1.  **Logs**: A detailed, timestamped record of a specific event. They are great for understanding the story of what happened in a single request or process.
    **로그**: 특정 이벤트에 대한 상세하고 타임스탬프가 찍힌 기록입니다. 단일 요청이나 프로세스에서 무슨 일이 일어났는지에 대한 이야기를 이해하는 데 유용합니다.
2.  **Metrics**: A numeric representation of data measured over time (a time-series). They are great for understanding the overall health and performance of your system (e.g., CPU usage, request latency, error rate).
    **메트릭**: 시간에 따라 측정된 데이터의 숫자 표현(시계열)입니다. 시스템의 전반적인 상태와 성능(예: CPU 사용량, 요청 지연 시간, 오류율)을 이해하는 데 유용합니다.
3.  **Traces (Distributed Tracing)**: Shows the end-to-end journey of a request as it travels through multiple services in a distributed system. It connects the dots between microservices.
    **트레이스(분산 추적)**: 분산 시스템에서 여러 서비스를 통과하는 요청의 종단 간 여정을 보여줍니다. 마이크로서비스 간의 점들을 연결합니다.

---

## 1. Structured Logging: More Than Just `print()`
## 1. 구조화된 로깅: 단순한 `print()` 이상

Unstructured logs (`print("User logged in")`) are hard to search and analyze. Structured logs, usually in JSON format, are machine-readable and far more powerful.
구조화되지 않은 로그(`print("사용자 로그인")`)는 검색하고 분석하기 어렵습니다. 일반적으로 JSON 형식의 구조화된 로그는 기계가 읽을 수 있고 훨씬 더 강력합니다.

**Bad: Unstructured Log**
**나쁨: 구조화되지 않은 로그**
```
INFO: User 123 logged in successfully from IP 192.168.1.100
```

**Good: Structured Log (JSON)**
**좋음: 구조화된 로그(JSON)**
```json
{
  "level": "INFO",
  "timestamp": "2025-10-26T10:00:00Z",
  "message": "User logged in successfully",
  "user_id": 123,
  "source_ip": "192.168.1.100",
  "service": "auth-api"
}
```
This allows you to easily filter, search, and aggregate logs. For example, you can find all login events for `user_id: 123` or create a dashboard showing the top 10 `source_ip`s.
이를 통해 로그를 쉽게 필터링, 검색 및 집계할 수 있습니다. 예를 들어, `user_id: 123`에 대한 모든 로그인 이벤트를 찾거나 상위 10개 `source_ip`를 보여주는 대시보드를 만들 수 있습니다.

**Implementation in Python:**
**파이썬에서의 구현:**
Use a library like `structlog` to automatically create structured logs.
`structlog`와 같은 라이브러리를 사용하여 구조화된 로그를 자동으로 생성합니다.

```python
import structlog

log = structlog.get_logger()

log.info(
    "User logged in successfully", 
    user_id=123, 
    source_ip="192.168.1.100"
)
```

---

## 2. Metrics: Your System's Pulse
## 2. 메트릭: 시스템의 맥박

Metrics are collected and stored in a time-series database (TSDB) like Prometheus and visualized with tools like Grafana.
메트릭은 Prometheus와 같은 시계열 데이터베이스(TSDB)에 수집 및 저장되고 Grafana와 같은 도구로 시각화됩니다.

### Key Metrics for a Web Service (The RED Method)
### 웹 서비스의 주요 메트릭(RED 방법)

-   **Rate**: The number of requests per second your service is handling.
    **비율**: 서비스가 초당 처리하는 요청 수입니다.
-   **Errors**: The number of requests that are failing.
    **오류**: 실패하는 요청 수입니다.
-   **Duration**: The amount of time it takes to process a request (latency).
    **기간**: 요청을 처리하는 데 걸리는 시간(지연 시간)입니다.

**Implementation with FastAPI and Prometheus:**
**FastAPI 및 Prometheus를 사용한 구현:**
Libraries like `starlette-prometheus` can automatically expose these metrics for you.
`starlette-prometheus`와 같은 라이브러리는 이러한 메트릭을 자동으로 노출할 수 있습니다.

```python
# In your main.py
from fastapi import FastAPI
from starlette_prometheus import metrics, PrometheusMiddleware

app = FastAPI()
app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", metrics)

@app.get("/")
async def root():
    return {"message": "Hello World"}
```
Now, a `/metrics` endpoint is available on your service. You configure a Prometheus server to scrape (periodically fetch) data from this endpoint. In Grafana, you can then build dashboards to visualize this data, for example, plotting the 95th percentile latency over the last hour.
이제 서비스에서 `/metrics` 엔드포인트를 사용할 수 있습니다. 이 엔드포인트에서 데이터를 스크레이핑(주기적으로 가져오기)하도록 Prometheus 서버를 구성합니다. 그런 다음 Grafana에서 이 데이터를 시각화하기 위한 대시보드를 구축할 수 있습니다. 예를 들어, 지난 한 시간 동안의 95번째 백분위수 지연 시간을 플로팅할 수 있습니다.

---

## 3. Distributed Tracing: The Story of a Request
## 3. 분산 추적: 요청 이야기

In a microservices architecture, a single user action might trigger a chain of requests across multiple services. If one of those services is slow, how do you find the bottleneck?
마이크로서비스 아키텍처에서 단일 사용자 작업은 여러 서비스에 걸쳐 요청 체인을 트리거할 수 있습니다. 그 서비스 중 하나가 느리면 병목 현상을 어떻게 찾을 수 있습니까?

Distributed tracing solves this. When a request enters the system, it's assigned a unique **Trace ID**. As the request travels from one service to another, this Trace ID is passed along. Each individual operation within a service (e.g., a database call, an API call to another service) is a **Span**. All spans belonging to the same request share the same Trace ID.
분산 추적이 이것을 해결합니다. 요청이 시스템에 들어오면 고유한 **추적 ID**가 할당됩니다. 요청이 한 서비스에서 다른 서비스로 이동할 때 이 추적 ID가 전달됩니다. 서비스 내의 각 개별 작업(예: 데이터베이스 호출, 다른 서비스에 대한 API 호출)은 **스팬**입니다. 동일한 요청에 속하는 모든 스팬은 동일한 추적 ID를 공유합니다.

**Visualization:**
**시각화:**
Tools like Jaeger or Zipkin visualize this as a flame graph, showing:
Jaeger 또는 Zipkin과 같은 도구는 이것을 다음과 같이 보여주는 불꽃 그래프로 시각화합니다.
-   Which services were called.
    어떤 서비스가 호출되었는지.
-   How long each service took.
    각 서비스에 걸린 시간.
-   The full sequence of events.
    전체 이벤트 시퀀스.

This makes it easy to spot the one slow database query in a chain of 10 microservice calls that is causing the entire request to be slow.
이렇게 하면 전체 요청이 느려지는 원인이 되는 10개의 마이크로서비스 호출 체인에서 느린 데이터베이스 쿼리 하나를 쉽게 찾을 수 있습니다.

**Implementation:**
**구현:**
Implementing tracing often involves using an agent or SDK that integrates with your web framework (like FastAPI) and automatically instruments incoming and outgoing requests. OpenTelemetry is the emerging standard for this.
추적을 구현하려면 웹 프레임워크(예: FastAPI)와 통합되고 들어오고 나가는 요청을 자동으로 계측하는 에이전트나 SDK를 사용하는 경우가 많습니다. OpenTelemetry가 이를 위한 새로운 표준입니다.

## The Vibe Coder's Approach
## Vibe 코더의 접근 방식

-   **Log Everything That Matters**: Log key business events, errors, and state changes. Use structured logging from day one.
    **중요한 모든 것 기록**: 주요 비즈니스 이벤트, 오류 및 상태 변경을 기록합니다. 첫날부터 구조화된 로깅을 사용하십시오.
-   **Instrument for Metrics**: Add metrics for your most important application-level concerns (e.g., number of users registered, number of files processed).
    **메트릭을 위한 계측**: 가장 중요한 애플리케이션 수준의 관심사(예: 등록된 사용자 수, 처리된 파일 수)에 대한 메트릭을 추가합니다.
-   **Trace Your Critical Path**: Set up distributed tracing for the most important user-facing workflows.
    **중요 경로 추적**: 가장 중요한 사용자 대면 워크플로에 대한 분산 추적을 설정합니다.

By building in observability, you move from a reactive state (waiting for users to report problems) to a proactive one (identifying and fixing issues before they impact users). This is essential for building and maintaining reliable, high-vibe systems.
관찰 가능성을 구축함으로써 반응적인 상태(사용자가 문제를 보고하기를 기다리는 것)에서 사전 예방적인 상태(사용자에게 영향을 미치기 전에 문제를 식별하고 수정하는 것)로 이동합니다. 이것은 신뢰할 수 있는 고품격 시스템을 구축하고 유지하는 데 필수적입니다.