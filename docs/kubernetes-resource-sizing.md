# Kubernetes Workload Sizing with Goldilocks

## Introduction

### Purpose
This document provides a framework for optimizing Kubernetes resource allocation. The goal is to move away from "guessing" resource needs and instead use data-driven recommendations to ensure application stability and cost efficiency.

### Audience
*   **Platform Engineers:** To establish cluster-wide sizing standards and resource quotas.
*   **DevOps/SRE:** To automate and monitor resource efficiency and prevent outages.
*   **Application Developers:** To understand the resource footprint of their services.
*   **FinOps:** To identify and eliminate "cloud slack" (paid but unused resources).

### Why Proper Sizing Matters
A properly sized cluster avoids the "Goldilocks Problem":
1.  **Too Small:** Leads to CPU throttling (latency) or OOMKilled events (crashes).
2.  **Too Large:** Leads to massive cloud waste and inefficient node utilization.
3.  **Just Right:** Ensures performance during peaks while minimizing costs.

### What is Goldilocks?
Goldilocks is an open-source tool that creates VPA (Vertical Pod Autoscaler) objects in "Recommendation Mode." It monitors real-time CPU and Memory usage and provides suggested `requests` and `limits` via a simple web dashboard.

---

## Installation (via Helm)

### 1. Prerequisite: Vertical Pod Autoscaler (VPA)
Goldilocks relies on the VPA Recommender engine. We install it in its own namespace to isolate management components.

```bash
# Add the Fairwinds repository
helm repo add fairwinds-stable https://charts.fairwinds.com/stable

# Install VPA first; it provides the background analysis engine
# Note: This includes the Recommender, Admission Controller, and Updater.
helm install vpa fairwinds-stable/vpa --namespace vpa --create-namespace
```

### 2. Goldilocks Controller & Dashboard
The Goldilocks controller watches for labeled namespaces, while the dashboard provides the visualization.

```bash
# Install Goldilocks into its own namespace
helm install goldilocks fairwinds-stable/goldilocks --namespace goldilocks --create-namespace
```

---

## Usage Workflow

### 1. Enable Analysis
Analysis is "opt-in" per namespace. This ensures you only track relevant workloads and avoid unnecessary overhead.

```bash
kubectl label ns <target-namespace> goldilocks.fairwinds.com/enabled=true
```
*Note: Once labeled, VPA objects are automatically created for all Deployments in that namespace in "off" mode (no changes to Pods).*

### 2. Wait for Data (Burn-in Period)
Recommendations are not instant. The VPA engine needs to capture representative traffic patterns:
*   **Minimum:** 1 hour (use only for initial rough estimates in non-prod).
*   **Recommended:** **24 to 48 hours** to capture full daily traffic cycles and background jobs.
*   **Ideal:** 7 days to capture weekly cycles (e.g., weekend vs. weekday patterns).

### 3. View Recommendations
Access the local dashboard to see the suggestions.

```bash
# Forward the service to your local machine
kubectl -n goldilocks port-forward svc/goldilocks-dashboard 8080:80
```
Open `http://localhost:8080` to review the two modes: **Guaranteed** and **Burstable**.

---

## Sizing Strategies

*   **Guaranteed (Production):** Set `Requests == Limits`. This ensures the Pod is in the highest Quality of Service (QoS) class, making it the last to be evicted during node pressure.
*   **Burstable (Non-Prod/Batch):** Set `Requests < Limits`. Allows the app to "burst" into spare node capacity during spikes while keeping baseline resource reservation low.
*   **The 20% Buffer:** Always add a ~20% safety margin to the "Maximum Observed" recommendation to handle unexpected traffic micro-bursts or startup spikes.

---

## Resource Fundamentals

| Concept | Purpose | Over-provisioned | Under-provisioned |
| :--- | :--- | :--- | :--- |
| **Requests** | Scheduling & Reservation | Wasted Cost (Slack) | Resource Contention |
| **Limits** | Hard Ceiling | N/A | OOMKilled (RAM) / Throttling (CPU) |

---

## Leadership Review

### QA Perspective
> The "burn-in" period is critical. For performance testing, ensure Goldilocks runs during a full load test cycle to capture true peak memory usage, which is often missed in idle states.

### Staff Engineer Perspective
> This guide addresses the "ROI of Efficiency." By bridging the gap between developers and FinOps, we create a sustainable growth model where scaling doesn't linearly increase costs.

### Platform/Cloud Engineer Perspective
> The use of Helm for VPA and Goldilocks ensures version control and easy updates. Labeling namespaces is a low-friction way to roll this out across a multi-tenant cluster without affecting system performance.
