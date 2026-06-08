# Observability Checklist

This checklist ensures that a service provides enough visibility to understand its behavior during normal operation and incidents.

## Table of Contents
* [1. Logs](#1-logs)
* [2. Metrics (Golden Signals)](#2-metrics-golden-signals)
* [3. Traces](#3-traces)
* [4. Dashboards](#4-dashboards)
* [5. Alerts](#5-alerts)
* [6. Kubernetes-Specific Checks](#6-kubernetes-specific-checks)
* [7. SLOs & Operational Ownership](#7-slos--operational-ownership)
* [Example Grafana Dashboard](#example-grafana-dashboard)

## 1. Logs
- [ ] Logs are structured (JSON) for easy parsing.
- [ ] Correlation IDs are included for cross-service requests.
- [ ] Logs are forwarded to a central log management system.

## 2. Metrics (Golden Signals)
- [ ] **Latency:** Time it takes to service a request.
- [ ] **Traffic:** Demand placed on the system.
- [ ] **Errors:** The rate of requests that fail.
- [ ] **Saturation:** How "full" the service is.

## 3. Traces
- [ ] Distributed tracing is implemented for microservices.
- [ ] Trace IDs are propagated through all service boundaries.

## 4. Dashboards
- [ ] High-level service overview dashboard exists.
- [ ] Operational dashboards are linked from runbooks.

## 5. Alerts
- [ ] Alerts are actionable (not "just FYI").
- [ ] Thresholds are based on SLOs.
- [ ] Severity levels are defined (Page vs. Ticket).

## 6. Kubernetes-Specific Checks
- [ ] **Pod Restarts:** Alert on frequent container restarts.
- [ ] **OOMKilled:** Monitor for memory-related crashes.
- [ ] **CPU Throttling:** Track if CPU limits are causing latency.
- [ ] **Node Pressure:** Monitor node health (Disk/Memory pressure).
- [ ] **HPA Behavior:** Ensure horizontal scaling is triggering as expected.

## 7. SLOs & Operational Ownership
- [ ] SLIs/SLOs are clearly defined and measurable.
- [ ] Alert routing is configured to the owning team.

### SLO, SLA and Error Budget Example

* **SLI (Service Level Indicator):** The actual measured service behavior (e.g., successful request percentage).
* **SLO (Service Level Objective):** The internal reliability target.
* **SLA (Service Level Agreement):** The contractual commitment to users.
* **Error Budget:** The amount of acceptable unreliability (1 - SLO).

The SLO should normally be stricter than the SLA to provide a safety margin.

**Availability Formula:**
`Availability = successful requests / total requests × 100`

**Example Values:**
* **SLI:** successful HTTP request percentage
* **SLO:** 99.9%
* **SLA:** 99.5%
* **SLO error budget:** 0.1%

*Note: HTTP 2xx responses are successes, 5xx are failures, and 4xx are excluded. Periods with no traffic must be displayed as `No data` or `N/A`, not 100% availability.*

See the [Kubernetes SLO Demo](examples/slo-demo/README.md) for a practical implementation.

> [!IMPORTANT]
> Observability is not only about collecting data. It is about making the system understandable during normal operation and incidents.

## Example Grafana Dashboard

<!-- Add the exported dashboard screenshot here:
![SLO Demo Grafana Dashboard](images/slo-demo-grafana-dashboard.png)
-->
