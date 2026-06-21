# AI Gateway - Intelligent Distributed LLM Inference Router

A **production-grade intelligent gateway** for serving multiple large language models with adaptive routing, horizontal scaling, and rich observability.

Originally started as a Rust + Axum project, then evolved into a robust Python + Docker Swarm deployment.

## ✨ Highlights

- **Smart Routing Engine**: Dynamically selects the best model using prompt complexity scoring + real-time performance (latency & tokens)
- **Multi-Model Support**: llama3.2:3b, qwen2.5:3b, qwen3, qwen2.5-coder:7b, **gpt-oss:20b**
- **Distributed & Scalable**: 3 gateway replicas with shared Redis state
- **Load Balanced**: Nginx reverse proxy + round-robin / least connections
- **Full Observability**: Prometheus metrics, Grafana dashboards, OpenTelemetry tracing
- **Self-healing**: Docker Swarm ready

## Architecture

```

Client
  |
Nginx :2194
  |
+---------+---------+
|         |         |
GW-1    GW-2    GW-3
  |
Redis + Ollama

Prometheus/Grafana/OpenTelemetry

```



## How to Use

### Option 1: Local Development (Recommended for Dev)

```bash
cd metrics
```

```bash
source .venv/bin/activate #activate venv
```

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

## 2. Make sure Ollama is running locally

```bash
ollama serve
```

## 3. Run the gateway

```bash
python gateway.py
```

## Then test:

```bash
curl -X POST http://localhost:3000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the capital of France?"}'
```

## Useful local endpoints:

```Open in Web Browser

http://localhost:3000/models/performance
http://localhost:3000/metrics
```


# Option 2: Full Distributed Stack (Docker)bash

```bash
docker-compose up -d --build
```


## Access URLs (Docker Mode)

```
Service       	URL			            Description

Gateway		  http://localhost:2194	  Main Inference endpoint
Grafana		  http://localhost:3001	  Dashboards
Prometheus	http://localhost:9090	  Metrics
Ollama		  http://localhost:11434	Direct model access
```


## Grafana Dashboards

- After starting the stack, open 

```http://localhost:3001```
 
Default credentials: admin / admin

You can view:
- Model usage distribution
- Smart routing decisions
- Average latency per model
- Adaptive routing scores
- Prompt complexity over time
- Tokens per request

Useful PromQL Queries:

```promql

# Requests per model
llm_requests_total

# Average latency
rate(llm_latency_ms_sum[5m]) / rate(llm_latency_ms_count[5m])

# Adaptive Model Score
llm_model_score

# Prompt Complexity
llm_prompt_complexity
```

### Grafana Dashboards (Local Run)

![Main Dashboard & Model Distribution](main/grafana-main.png)
![Adaptive Routing](main/adaptive-routing.png)
![Prompt Complexity](main/prompt-complexity.png)


# Tech Stack

- Backend: Python + Flask
- Routing: Custom complexity + adaptive scoring
- State: Redis
- LLM Backend: Ollama
- Load Balancer: Nginx
- Orchestration: Docker Compose + Docker Swarm
- Observability: Prometheus, Grafana, OpenTelemetry
- Original Prototype: Rust + Axum (/src/)




