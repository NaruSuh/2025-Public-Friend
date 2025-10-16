# 05 - Observability - Lv.2: Proactive Monitoring and Alerting
# 05 - 가시성 - Lv.2: 선제적 모니터링과 알림

You're collecting logs, metrics, and traces. Level 2 is about using that data proactively to detect and even predict problems before your users notice them. This involves building sophisticated dashboards, setting up intelligent alerts, and understanding Service Level Objectives (SLOs).
로그, 메트릭, 트레이스를 수집하고 있다면 레벨 2에서는 그 데이터를 활용해 사용자가 알아차리기 전에 문제를 감지하고 예측하는 것에 집중합니다. 이를 위해 정교한 대시보드를 구축하고, 똑똑한 알림을 설정하며, 서비스 수준 목표(SLO)를 이해해야 합니다.

## Before You Begin
## 시작하기 전에
-   Confirm Level 1 logging and metrics exporters are running locally; you should be able to open Grafana and view RED metrics already.
-   레벨 1에서 구성한 로깅과 메트릭 익스포터가 로컬에서 실행 중인지 확인하고, Grafana를 열어 RED 메트릭을 확인할 수 있어야 합니다.
-   Install the Prometheus and Grafana CLIs or Docker Compose files so you can iterate quickly without touching production.
-   프로덕션에 영향 없이 빠르게 실험할 수 있도록 Prometheus와 Grafana CLI 또는 도커 컴포즈 구성을 준비하세요.
-   Gather at least one week of sample metrics from your app—historical context makes dashboards and alerts far more meaningful.
-   애플리케이션에서 최소 일주일치 샘플 메트릭을 수집하세요. 과거 데이터가 있어야 대시보드와 알림이 의미를 갖습니다.

## Level 2 Upgrade Goals
## 레벨 2 업그레이드 목표
1.  **Create opinionated dashboards** that spotlight anomalies, not just raw graphs.
1.  **이상 징후를 강조하는 대시보드 만들기** – 단순 그래프가 아닌 판단 가능한 인사이트를 제공합니다.
2.  **Design actionable alerts** with routing, severity, and runbooks that a newcomer could follow.
2.  **실행 가능한 알림 설계** – 라우팅, 심각도, 런북을 포함해 초보자도 따를 수 있게 합니다.
3.  **Define SLOs and error budgets** that connect system reliability to product decisions.
3.  **SLO와 에러 버짓 정의** – 시스템 신뢰도를 제품 의사결정과 연결합니다.

## Core Concepts
## 핵심 개념

1.  **Dashboards**: A curated, visual representation of your system's most important metrics. A good dashboard tells a story and helps you answer key questions quickly during an incident.
1.  **대시보드**: 시스템의 핵심 메트릭을 시각적으로 정리한 것으로, 좋은 대시보드는 상황을 이야기로 보여주고 사고 때 빠르게 핵심 질문에 답하게 해줍니다.
2.  **Alerting**: The process of automatically notifying you when a metric crosses a critical threshold. The goal is to create alerts that are *actionable* and have a low signal-to-noise ratio.
2.  **알림**: 중요한 임계치를 넘을 때 자동으로 알려주는 과정으로, 불필요한 소음을 줄이고 실제로 대응 가능한 알림을 설계하는 것이 목표입니다.
3.  **Service Level Objectives (SLOs)**: A target for a specific metric that you promise to your users (explicitly or implicitly). SLOs are a powerful tool for making data-driven decisions about reliability.
3.  **서비스 수준 목표(SLO)**: 사용자에게 명시적 또는 암묵적으로 약속하는 특정 메트릭의 목표치로, 신뢰성에 관한 데이터 기반 의사결정을 돕는 강력한 도구입니다.

---

## 1. Building Effective Dashboards with Grafana
## 1. Grafana로 효과적인 대시보드 구축하기

You have Prometheus collecting metrics. Grafana is the tool you'll use to visualize them.
Prometheus가 메트릭을 수집하고 있다면, Grafana는 이를 시각화하는 주요 도구입니다.

**The RED Method for API Dashboards**: A great starting point for any service is to dashboard the RED metrics:
**API 대시보드를 위한 RED 메서드**: 어떤 서비스든 RED 메트릭을 대시보드에 올리는 것부터 시작하세요.
-   **Rate**: The number of requests per second.
-   **Rate**: 초당 요청 수.
-   **Errors**: The number of requests resulting in an error (typically 5xx status codes).
-   **Errors**: 오류로 응답한 요청 수(보통 5xx 상태 코드).
-   **Duration**: The distribution of request latencies (p50, p90, p95, p99).
-   **Duration**: 요청 지연 시간의 분포(p50, p90, p95, p99).

### Example Grafana Dashboard Panels
### Grafana 대시보드 패널 예시

Let's design a dashboard for your FastAPI service.
FastAPI 서비스를 위한 대시보드를 설계해 봅시다.

**Panel 1: Request Rate (Requests per second)**
**패널 1: 요청 처리율(초당 요청 수)**
-   **Query**: `rate(http_requests_total{job="my-vibe-app"}[5m])`
-   **쿼리**: `rate(http_requests_total{job="my-vibe-app"}[5m])`
-   **Visualization**: Graph
-   **시각화**: 그래프
-   **Why**: Shows the overall traffic to your service. A sudden drop or spike can indicate a problem.
-   **이유**: 서비스 전체 트래픽을 보여주며, 갑작스러운 감소나 급증은 문제의 신호일 수 있습니다.

**Panel 2: Error Rate (%)**
**패널 2: 오류율(%)**
-   **Query**: `sum(rate(http_requests_total{job="my-vibe-app", status=~"5.."}[5m])) / sum(rate(http_requests_total{job="my-vibe-app"}[5m])) * 100`
-   **쿼리**: `sum(rate(http_requests_total{job="my-vibe-app", status=~"5.."}[5m])) / sum(rate(http_requests_total{job="my-vibe-app"}[5m])) * 100`
-   **Visualization**: Graph or Stat
-   **시각화**: 그래프 또는 통계 패널
-   **Why**: This is one of your most critical health indicators. A rising error rate is a clear sign of a problem.
-   **이유**: 핵심 건강 지표 중 하나로, 오류율 증가가 곧 문제 발생을 의미합니다.

**Panel 3: 95th Percentile Latency (p95)**
**패널 3: 95퍼센타일 지연 시간(p95)**
-   **Query**: `histogram_quantile(0.95, sum(rate(http_requests_latency_seconds_bucket{job="my-vibe-app"}[5m])) by (le))`
-   **쿼리**: `histogram_quantile(0.95, sum(rate(http_requests_latency_seconds_bucket{job="my-vibe-app"}[5m])) by (le))`
-   **Visualization**: Graph
-   **시각화**: 그래프
-   **Why**: The average (mean) latency can be misleading. The p95 latency tells you that 95% of your users are having an experience at least this fast. It's a much better indicator of user-perceived performance.
-   **이유**: 평균 지연은 오해를 줄 수 있습니다. p95는 95% 사용자가 최소 이 정도 속도를 경험한다는 뜻으로, 체감 성능을 더 잘 나타냅니다.

**Panel 4: Saturation (CPU/Memory)**
**패널 4: 포화도(CPU/메모리)**
-   **Query**: `container_cpu_usage_seconds_total`, `container_memory_working_set_bytes` (from cAdvisor, a common container metrics exporter)
-   **쿼리**: `container_cpu_usage_seconds_total`, `container_memory_working_set_bytes` (일반적인 컨테이너 메트릭 수집기인 cAdvisor 제공)
-   **Visualization**: Graph
-   **시각화**: 그래프
-   **Why**: Shows how close your service is to its physical limits. High saturation can predict future latency increases or crashes.
-   **이유**: 서비스가 물리적 한계에 얼마나 가까운지 보여주며, 포화도가 높으면 지연 증가나 장애를 예측할 수 있습니다.

A good dashboard groups these panels logically, allowing you to go from a high-level overview (is the system healthy?) to specific details (which endpoint is slow?) in just a few clicks.
좋은 대시보드는 패널을 논리적으로 묶어 몇 번의 클릭만으로 전체 상태(건강한가?)에서 세부 정보(어떤 엔드포인트가 느린가?)까지 내려갈 수 있게 합니다.

**Practice:** snapshot your dashboard layout, then run a chaos experiment (e.g., throttle CPU) to verify the panels make the problem obvious within 60 seconds.
**실습:** 대시보드 레이아웃을 스냅샷으로 저장한 뒤 CPU 제한 같은 카오스 실험을 수행해 60초 안에 문제를 확인할 수 있는지 검증해 보세요.

---

## 2. Intelligent Alerting with Alertmanager
## 2. Alertmanager로 지능형 알림 구성하기

Alert fatigue is a real problem. If you are constantly bombarded with meaningless alerts, you will start to ignore them. The goal is to create alerts that signify a real, user-facing problem.
알림 피로는 실제 문제입니다. 의미 없는 알림이 계속 쏟아지면 결국 무시하게 되죠. 목표는 사용자에게 영향이 있는 실제 문제만 알려주는 것입니다.

Prometheus, combined with its Alertmanager component, provides a powerful alerting framework.
Prometheus와 Alertmanager를 함께 사용하면 강력한 알림 프레임워크를 구축할 수 있습니다.

### Principles of Good Alerting
### 좋은 알림의 원칙

-   **Alert on Symptoms, Not Causes**: Alert on high error rates or high latency (the user-facing symptom), not high CPU usage (a potential cause). High CPU is not a problem if users aren't affected.
-   **원인보다 증상을 알림**: CPU 사용량 같은 원인보다 오류율, 지연 증가 등 사용자에게 체감되는 증상에 대해 알림을 설정하세요.
-   **Use Appropriate Severity Levels**:
-   **적절한 심각도 사용**:
    -   **Page/Critical**: Something is broken *right now* and requires immediate human intervention (e.g., "The site is down").
    -   **페이지/크리티컬**: 지금 당장 무언가가 고장났고 즉시 사람이 개입해야 할 때(예: “사이트 다운”).
    -   **Warn/Ticket**: Something will break *soon* if no action is taken (e.g., "Disk space will be full in 4 hours").
    -   **경고/티켓**: 조치를 취하지 않으면 곧 문제가 될 상황(예: “4시간 뒤 디스크가 가득 참”).
-   **Include a Playbook**: Every alert notification should include a link to a document (a "playbook") that explains what the alert means and provides step-by-step instructions for diagnosing and fixing the issue.
-   **플레이북 포함**: 알림에는 의미와 해결 단계를 설명한 문서(플레이북) 연결을 반드시 포함하세요.

### Example Prometheus Alert Rule
### Prometheus 알림 규칙 예시

This rule would be defined in a file that Prometheus loads.
이 규칙은 Prometheus가 읽는 파일에 정의됩니다.

```yaml
groups:
- name: api_alerts
  rules:
  - alert: HighApiErrorRate
    # The condition for the alert to fire
    expr: (sum(rate(http_requests_total{job="my-vibe-app", status=~"5.."}[5m])) / sum(rate(http_requests_total{job="my-vibe-app"}[5m]))) * 100 > 5
    # How long the condition must be true before firing
    for: 2m
    # Annotations that will be sent in the notification
    annotations:
      summary: "High API error rate detected for job {{ $labels.job }}"
      description: "The error rate is {{ $value | printf \"%.2f\" }}%, which is above the 5% threshold."
      playbook_url: "https://your-wiki.com/playbooks/high-error-rate"
    # Labels for routing the alert in Alertmanager
    labels:
      severity: page
```
This alert will only fire if the API error rate is above 5% for a continuous period of 2 minutes. Alertmanager can then be configured to send this alert to PagerDuty, Slack, or email.
이 알림은 API 오류율이 2분 동안 5%를 초과할 때만 발생합니다. Alertmanager는 이 알림을 PagerDuty, Slack, 이메일 등으로 전송하도록 설정할 수 있습니다.

**Practice:** configure a dummy Slack channel and send alerts there first. Iterate until every alert includes: what broke, why it matters, immediate mitigation steps, and a link to relevant dashboards.
**실습:** 테스트용 Slack 채널을 만들어 알림을 먼저 보내 보세요. “무엇이 고장났는지, 왜 중요한지, 즉각적인 완화 단계, 관련 대시보드 링크”가 모두 포함될 때까지 반복해 보세요.

---

## 3. Defining Reliability with SLOs
## 3. SLO로 신뢰성 정의하기

A Service Level Objective (SLO) is a target for a Service Level Indicator (SLI).
서비스 수준 목표(SLO)는 서비스 수준 지표(SLI)에 대한 목표치입니다.

-   **SLI (Indicator)**: A quantitative measure of your service's performance. Example: The proportion of successful HTTP requests (`good_requests / total_requests`).
-   **SLI(지표)**: 서비스 성능을 수치로 나타낸 것으로, 예를 들면 성공한 HTTP 요청 비율(`good_requests / total_requests`)입니다.
-   **SLO (Objective)**: The target for that SLI over a period of time. Example: "99.9% of HTTP requests will be successful over a rolling 28-day period."
-   **SLO(목표)**: SLI가 일정 기간 동안 도달해야 할 목표로, 예를 들어 “최근 28일 동안 HTTP 요청의 99.9%가 성공해야 한다”는 식입니다.
-   **Error Budget**: The inverse of your SLO. An SLO of 99.9% gives you an "error budget" of 0.1%. This is the amount of "unreliability" you are allowed to have.
-   **에러 버짓**: SLO의 여유분으로, SLO가 99.9%라면 0.1%가 허용 가능한 “불안정”입니다.

**Why are SLOs so powerful?**
**SLO가 강력한 이유**
They transform reliability from a vague goal into a concrete metric that can drive business and engineering decisions.
신뢰성을 모호한 목표에서 비즈니스와 엔지니어링 의사결정을 이끄는 구체적인 지표로 바꿉니다.

-   **If you are meeting your SLO (your error budget is full)**: You have room to take risks. You can ship features faster, experiment more, and prioritize development over reliability work.
-   **SLO를 달성하고 있다면(에러 버짓이 충분하다면)**: 위험을 감수할 여유가 생기므로 기능 개발과 실험을 우선할 수 있습니다.
-   **If you are violating your SLO (you have exhausted your error budget)**: This is a strong, data-driven signal that you must stop all feature development and focus exclusively on reliability improvements (e.g., fixing bugs, improving tests, reducing technical debt).
-   **SLO를 위반했다면(에러 버짓을 소진했다면)**: 모든 기능 개발을 중단하고 버그 수정, 테스트 개선, 기술 부채 감소 등 신뢰성 향상에 집중해야 한다는 강력한 데이터 신호입니다.

By adopting SLOs, you create a shared language between engineering, product, and business stakeholders, allowing you to make rational, data-informed trade-offs between innovation and stability. This is the pinnacle of operating a mature, production-grade service.
SLO를 도입하면 엔지니어링, 제품, 비즈니스 이해관계자 간에 공통 언어가 생겨 혁신과 안정성 간의 선택을 합리적으로, 데이터에 근거해 할 수 있습니다. 이는 성숙한 프로덕션 서비스를 운영하는 정점입니다.

**Practice:** write down one availability SLO and one latency SLO for your crawler API. Share them with a non-engineering friend and confirm the definitions make sense—if they cannot explain it back to you, simplify the wording.
**실습:** 크롤러 API에 대해 가용성 SLO 하나와 지연 SLO 하나를 작성한 뒤 비기술 친구에게 설명해 보세요. 상대가 이해하지 못한다면 더욱 쉽게 풀어 쓰세요.

## Going Further
## 더 나아가기
-   Implement synthetic monitoring (e.g., k6 or Checkly) that hits your endpoints from another region and feeds the data into Grafana.
-   k6나 Checkly 같은 합성 모니터링을 도입해 다른 지역에서 엔드포인트를 호출하고 결과를 Grafana에 연동하세요.
-   Experiment with error-budget burn-rate alerts: alert when the budget will be exhausted in 1 hour vs. 24 hours to triage severity.
-   에러 버짓 소진 속도를 기준으로 한 알림을 실험해 보세요. 1시간 내 소진, 24시간 내 소진 등으로 심각도를 구분할 수 있습니다.
-   Read Google’s SRE workbook chapter on alerting; capture three checklist items to add to your own incident response playbook.
-   Google SRE 워크북의 알림 챕터를 읽고 사고 대응 플레이북에 추가할 체크리스트 항목 세 가지를 기록하세요.
