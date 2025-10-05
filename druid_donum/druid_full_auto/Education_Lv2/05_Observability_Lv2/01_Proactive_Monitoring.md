# 05 - Observability - Lv.2: Proactive Monitoring and Alerting

You're collecting logs, metrics, and traces. Level 2 is about using that data proactively to detect and even predict problems before your users notice them. This involves building sophisticated dashboards, setting up intelligent alerts, and understanding Service Level Objectives (SLOs).

## Core Concepts

1.  **Dashboards**: A curated, visual representation of your system's most important metrics. A good dashboard tells a story and helps you answer key questions quickly during an incident.
2.  **Alerting**: The process of automatically notifying you when a metric crosses a critical threshold. The goal is to create alerts that are *actionable* and have a low signal-to-noise ratio.
3.  **Service Level Objectives (SLOs)**: A target for a specific metric that you promise to your users (explicitly or implicitly). SLOs are a powerful tool for making data-driven decisions about reliability.

---

## 1. Building Effective Dashboards with Grafana

You have Prometheus collecting metrics. Grafana is the tool you'll use to visualize them.

**The RED Method for API Dashboards**: A great starting point for any service is to dashboard the RED metrics:
-   **Rate**: The number of requests per second.
-   **Errors**: The number of requests resulting in an error (typically 5xx status codes).
-   **Duration**: The distribution of request latencies (p50, p90, p95, p99).

### Example Grafana Dashboard Panels

Let's design a dashboard for your FastAPI service.

**Panel 1: Request Rate (Requests per second)**
-   **Query**: `rate(http_requests_total{job="my-vibe-app"}[5m])`
-   **Visualization**: Graph
-   **Why**: Shows the overall traffic to your service. A sudden drop or spike can indicate a problem.

**Panel 2: Error Rate (%)**
-   **Query**: `sum(rate(http_requests_total{job="my-vibe-app", status=~"5.."}[5m])) / sum(rate(http_requests_total{job="my-vibe-app"}[5m])) * 100`
-   **Visualization**: Graph or Stat
-   **Why**: This is one of your most critical health indicators. A rising error rate is a clear sign of a problem.

**Panel 3: 95th Percentile Latency (p95)**
-   **Query**: `histogram_quantile(0.95, sum(rate(http_requests_latency_seconds_bucket{job="my-vibe-app"}[5m])) by (le))`
-   **Visualization**: Graph
-   **Why**: The average (mean) latency can be misleading. The p95 latency tells you that 95% of your users are having an experience at least this fast. It's a much better indicator of user-perceived performance.

**Panel 4: Saturation (CPU/Memory)**
-   **Query**: `container_cpu_usage_seconds_total`, `container_memory_working_set_bytes` (from cAdvisor, a common container metrics exporter)
-   **Visualization**: Graph
-   **Why**: Shows how close your service is to its physical limits. High saturation can predict future latency increases or crashes.

A good dashboard groups these panels logically, allowing you to go from a high-level overview (is the system healthy?) to specific details (which endpoint is slow?) in just a few clicks.

---

## 2. Intelligent Alerting with Alertmanager

Alert fatigue is a real problem. If you are constantly bombarded with meaningless alerts, you will start to ignore them. The goal is to create alerts that signify a real, user-facing problem.

Prometheus, combined with its Alertmanager component, provides a powerful alerting framework.

### Principles of Good Alerting

-   **Alert on Symptoms, Not Causes**: Alert on high error rates or high latency (the user-facing symptom), not high CPU usage (a potential cause). High CPU is not a problem if users aren't affected.
-   **Use Appropriate Severity Levels**:
    -   **Page/Critical**: Something is broken *right now* and requires immediate human intervention (e.g., "The site is down").
    -   **Warn/Ticket**: Something will break *soon* if no action is taken (e.g., "Disk space will be full in 4 hours").
-   **Include a Playbook**: Every alert notification should include a link to a document (a "playbook") that explains what the alert means and provides step-by-step instructions for diagnosing and fixing the issue.

### Example Prometheus Alert Rule

This rule would be defined in a file that Prometheus loads.

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

---

## 3. Defining Reliability with SLOs

A Service Level Objective (SLO) is a target for a Service Level Indicator (SLI).

-   **SLI (Indicator)**: A quantitative measure of your service's performance. Example: The proportion of successful HTTP requests (`good_requests / total_requests`).
-   **SLO (Objective)**: The target for that SLI over a period of time. Example: "99.9% of HTTP requests will be successful over a rolling 28-day period."
-   **Error Budget**: The inverse of your SLO. An SLO of 99.9% gives you an "error budget" of 0.1%. This is the amount of "unreliability" you are allowed to have.

**Why are SLOs so powerful?**
They transform reliability from a vague goal into a concrete metric that can drive business and engineering decisions.

-   **If you are meeting your SLO (your error budget is full)**: You have room to take risks. You can ship features faster, experiment more, and prioritize development over reliability work.
-   **If you are violating your SLO (you have exhausted your error budget)**: This is a strong, data-driven signal that you must stop all feature development and focus exclusively on reliability improvements (e.g., fixing bugs, improving tests, reducing technical debt).

By adopting SLOs, you create a shared language between engineering, product, and business stakeholders, allowing you to make rational, data-informed trade-offs between innovation and stability. This is the pinnacle of operating a mature, production-grade service.
