# Kubernetes Workload Sizing with Goldilocks

## Resource Fundamentals

| Concept | Purpose | Over-provisioned | Under-provisioned |
| :--- | :--- | :--- | :--- |
| **Requests** | Scheduling & Reservation | Wasted Cost (Slack) | Resource Contention |
| **Limits** | Hard Ceiling | N/A | OOMKilled (RAM) / Throttling (CPU) |

---

## Installation (via Helm)

### 1. Prerequisite: Vertical Pod Autoscaler (VPA)
Goldilocks requires VPA in recommendation mode to analyze usage.

```bash
helm repo add fairwinds-stable https://charts.fairwinds.com/stable
helm install vpa fairwinds-stable/vpa --namespace vpa --create-namespace
```

### 2. Goldilocks
```bash
helm install goldilocks fairwinds-stable/goldilocks --namespace goldilocks --create-namespace
```

---

## Usage Workflow

### 1. Enable Analysis
Label the target namespace to start tracking deployments:
```bash
kubectl label ns <namespace> goldilocks.fairwinds.com/enabled=true
```

### 2. View Recommendations
Port-forward to access the dashboard:
```bash
kubectl -n goldilocks port-forward svc/goldilocks-dashboard 8080:80
```
Open `http://localhost:8080`.

---

## Sizing Strategies

*   **Guaranteed (Production):** `Requests == Limits`. Prevents eviction and ensures predictable performance.
*   **Burstable (Dev/Test):** `Requests < Limits`. Allows sharing idle resources but risks throttling during peak.
*   **Safety Buffer:** Aim for peak usage + 20% for limits to handle unexpected spikes.
*   **Continuous Review:** Re-check Goldilocks after every major release or traffic shift.
