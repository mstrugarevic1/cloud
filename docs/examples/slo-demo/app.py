import time
import random
from flask import Flask, Response, request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# Metrics
REQUESTS = Counter(
    'slo_demo_http_requests_total',
    'Total HTTP requests',
    ['method', 'route', 'status']
)

LATENCY = Histogram(
    'slo_demo_http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'route']
)

@app.before_request
def start_timer():
    request.start_time = time.time()

@app.after_request
def record_metrics(response):
    # Normalize route names
    if request.url_rule:
        route = request.url_rule.rule
    else:
        route = 'unknown'

    # Exclude metrics and healthz from labels if needed, or handle in PromQL
    # We include them here but the PromQL will filter them out as requested.
    
    latency = time.time() - request.start_time
    
    REQUESTS.labels(
        method=request.method,
        route=route,
        status=str(response.status_code)
    ).inc()
    
    LATENCY.labels(
        method=request.method,
        route=route
    ).observe(latency)
    
    return response

@app.route('/')
def root():
    return "OK", 200

@app.route('/fail')
def fail():
    return "Internal Server Error", 500

@app.route('/slow')
def slow():
    delay = random.uniform(0.5, 2.0)
    time.sleep(delay)
    return f"Response delayed by {delay:.2f}s", 200

@app.route('/healthz')
def healthz():
    return "OK", 200

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
