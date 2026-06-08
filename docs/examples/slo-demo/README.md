# SLO Demo - Service Reliability

This demo provides a practical example of Service Level Indicators (SLIs), Service Level Objectives (SLOs), and Service Level Agreements (SLAs) using a simple Kubernetes application and Prometheus/Grafana.

## Purpose

- Demonstrate how to measure availability using Prometheus metrics.
- Visualize the relationship between SLI, SLO, and SLA.
- Track error budget consumption in real-time.

## Directory Structure

```text
examples/slo-demo/
├── app.py                  # Flask application with Prometheus metrics
├── requirements.txt        # Python dependencies
├── Dockerfile              # Minimal container image
├── README.md               # This guide
├── k8s/
│   ├── app.yaml            # Namespace, Deployment, and Service
│   ├── servicemonitor.yaml # Prometheus Operator ServiceMonitor
│   └── load-generator.yaml # Optional traffic generator
└── grafana/
    └── slo-dashboard.json  # Importable Grafana dashboard
```

## Prerequisites

- A Kubernetes cluster.
- `kube-prometheus-stack` installed (Prometheus Operator and Grafana).
- `kubectl` configured to access the cluster.

## Build and Push the Image

1. Build the Docker image:
   ```bash
   docker build -t ghcr.io/strugi032/slo-demo:0.1.0 .
   ```

2. Push the image to your registry:
   ```bash
   docker push ghcr.io/strugi032/slo-demo:0.1.0
   ```

*Note: Ensure your Kubernetes cluster has access to the registry.*

## Deploy the Application

1. Apply the core manifests:
   ```bash
   kubectl apply -f k8s/app.yaml
   ```

2. Verify the pods are running:
   ```bash
   kubectl get pods -n slo-demo
   ```

## Deploy the ServiceMonitor

The `ServiceMonitor` tells the Prometheus Operator to scrape metrics from our service.

1. Apply the ServiceMonitor:
   ```bash
   kubectl apply -f k8s/servicemonitor.yaml
   ```

*Important: The `release: kube-prometheus-stack` label in `servicemonitor.yaml` must match your Prometheus installation. If your release name is different, update the label accordingly.*

## Verify the Prometheus Target

1. Port-forward to the application to check metrics manually:
   ```bash
   kubectl port-forward -n slo-demo svc/slo-demo 8080:80
   ```
2. Visit `http://localhost:8080/metrics` in your browser or use curl:
   ```bash
   curl http://localhost:8080/metrics
   ```
3. Ensure the target appears as "UP" in the Prometheus UI (usually at `/targets`).

## Start the Optional Traffic Generator

To see meaningful data in Grafana, start the load generator which produces ~99.7% successful requests and ~0.3% failures.

1. Apply the load generator:
   ```bash
   kubectl apply -f k8s/load-generator.yaml
   ```

## Import the Grafana Dashboard

1. Open Grafana and go to **Dashboards -> Import**.
2. Upload `grafana/slo-dashboard.json`.
3. Select your Prometheus datasource when prompted.
4. View the "SLO Demo - Service Reliability" dashboard.

## Interpret the Six Panels

1. **Availability vs SLO and SLA**: Shows the SLI (actual) against the internal target (SLO) and contractual commitment (SLA).
2. **Current Availability**: A real-time gauge of availability, color-coded by performance against targets.
3. **Error Budget Remaining**: Shows how much of the allowed 0.1% unreliability (SLO) remains.
4. **Request Rate**: Volume of traffic per second, split by HTTP status code.
5. **HTTP 5xx Error Rate**: Focuses on service failures and their impact as a percentage of traffic.
6. **P95 Request Latency**: Measures the response time for the 95th percentile of requests.

## Troubleshooting

- **No data in Grafana**: Check if the ServiceMonitor label matches your Prometheus release. Verify that the app is exposing metrics at `/metrics`.
- **Target Down in Prometheus**: Ensure the Service in `k8s/app.yaml` has the correct selector and port name (`http`).
- **Load generator not reaching app**: Check the DNS resolution of `slo-demo.slo-demo.svc.cluster.local` within the cluster.

## Remove the Demo

To clean up all resources:

```bash
kubectl delete -f k8s/load-generator.yaml
kubectl delete -f k8s/servicemonitor.yaml
kubectl delete -f k8s/app.yaml
```
