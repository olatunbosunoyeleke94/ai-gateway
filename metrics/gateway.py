from flask import Flask, request, jsonify
import os
import time
import requests
import logging
import json
from datetime import datetime, UTC

# Updated imports for Redis-backed stats
from model_stats import get_model_stats, save_model_stats

from metrics import (
    LLM_REQUESTS,
    LATENCY,
    AVG_LATENCY,
    ROUTE_COUNTER,
    TOKENS_COUNTER,
    TOKENS_PER_REQUEST,
    COMPLEXITY_SCORE,
    MODEL_SELECTIONS,
    MODEL_LATENCY,
    MODEL_TOKENS,
    MODEL_SCORE
)

from router import (
    route_request,
    score_prompt,
    calculate_score
)

from telemetry import (
    tracer,
    get_trace_id
)

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s"
)

logger = logging.getLogger("llm-gateway")

history_latency = {}

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434/api/generate")

def write_log(entry):
    with open("logs.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")


@app.route("/", methods=["GET"])
def home():
    return {
        "status": "ok",
        "service": "llm-gateway",
        "endpoints": [
            "/generate",
            "/metrics",
            "/models/performance"
        ]
    }


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "missing JSON body"}), 400

    if "prompt" not in data:
        return jsonify({"error": "missing prompt"}), 400

    prompt = data["prompt"]

    with tracer.start_as_current_span("generate_request") as span:
        start = time.time()

        complexity = score_prompt(prompt)
        COMPLEXITY_SCORE.set(complexity)

        model, route = route_request(prompt, history_latency)

        trace_id = get_trace_id()

        span.set_attribute("model", model)
        span.set_attribute("route", route)
        span.set_attribute("trace_id", trace_id)
        span.set_attribute("prompt_complexity", complexity)

        MODEL_SELECTIONS.labels(model=model).inc()
        ROUTE_COUNTER.labels(route=route).inc()

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }

        try:
            resp = requests.post(
                OLLAMA_URL,
                json=payload,
                timeout=300
            )
            resp.raise_for_status()
            result = resp.json()

        except requests.exceptions.RequestException as e:
            return jsonify({
                "error": "ollama request failed",
                "details": str(e)
            }), 500

        latency = (time.time() - start) * 1000
        tokens = result.get("eval_count", 0)

        # === Adaptive model learning (Redis version) ===
        stats = get_model_stats(model)
        stats["latency"].append(latency)
        stats["tokens"].append(tokens)
        save_model_stats(model, stats)

        adaptive_score = calculate_score(stats)

        MODEL_SCORE.labels(model=model).set(adaptive_score)
        history_latency[model] = latency

        # Prometheus Metrics
        LLM_REQUESTS.labels(model=model, route=route).inc()
        ROUTE_COUNTER.labels(route=route).inc()
        LATENCY.labels(model=model, route=route).observe(latency)
        AVG_LATENCY.labels(model=model).set(latency)
        TOKENS_COUNTER.labels(model=model, route=route).inc(tokens)
        TOKENS_PER_REQUEST.labels(model=model).set(tokens)
        MODEL_LATENCY.labels(model=model).observe(latency)
        MODEL_TOKENS.labels(model=model).inc(tokens)

        # Structured Log
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event": "llm_request",
            "trace_id": trace_id,
            "model": model,
            "route": route,
            "complexity": complexity,
            "tokens": tokens,
            "latency_ms": round(latency, 2),
            "adaptive_score": round(adaptive_score, 6)
        }

        logger.info(log_entry)
        write_log(log_entry)

        # Response
        return jsonify({
            "response": result.get("response"),
            "model_used": model,
            "route": route,
            "trace_id": trace_id,
            "complexity": complexity,
            "tokens": tokens,
            "adaptive_score": adaptive_score,
            "latency_ms": latency
        })


@app.route("/models/performance", methods=["GET"])
def models_performance():
    performance = []
    
    for model in ["llama3.2:3b", "qwen2.5:3b", "qwen3:latest", "qwen2.5-coder:7b", "gpt-oss:20b"]:
        stats = get_model_stats(model)
        
        latencies = stats.get("latency", [])
        tokens_list = stats.get("tokens", [])
        
        if not latencies or not tokens_list:
            avg_latency = 0.0
            avg_tokens = 0.0
            adaptive_score = 0.0
        else:
            avg_latency = sum(latencies) / len(latencies)
            avg_tokens = sum(tokens_list) / len(tokens_list)
            adaptive_score = calculate_score(stats)
        
        performance.append({
            "model": model,
            "avg_latency_ms": round(avg_latency, 2),
            "avg_tokens": round(avg_tokens, 1),
            "adaptive_score": round(adaptive_score, 5),
            "request_count": len(latencies)
        })
    
    performance.sort(key=lambda x: x["adaptive_score"], reverse=True)
    return jsonify(performance)


@app.route("/metrics")
def metrics():
    from prometheus_client import generate_latest
    return (
        generate_latest(),
        200,
        {"Content-Type": "text/plain; version=0.0.4"}
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
