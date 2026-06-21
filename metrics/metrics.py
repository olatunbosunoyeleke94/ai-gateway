from prometheus_client import (
    Counter,
    Histogram,
    Gauge
)

# Total requests
LLM_REQUESTS = Counter(
    "llm_requests_total",
    "Total LLM requests",
    ["model", "route"]
)

# Routing decisions
ROUTE_COUNTER = Counter(
    "llm_routes_total",
    "LLM routing decisions",
    ["route"]
)

# Request latency distribution
LATENCY = Histogram(
    "llm_latency_ms",
    "LLM request latency in milliseconds",
    ["model", "route"]
)

# Average/latest latency per model
AVG_LATENCY = Gauge(
    "llm_latency_ms_avg",
    "Average latency in ms",
    ["model"]
)

TOKENS_COUNTER = Counter(
    "llm_tokens_total",
    "Total tokens generated",
    ["model", "route"]
)

TOKENS_PER_REQUEST = Gauge(
    "llm_tokens_per_request",
    "Average tokens per request",
    ["model"]
)

COMPLEXITY_SCORE = Gauge(
    "llm_prompt_complexity",
    "Prompt complexity score"
)

MODEL_SELECTIONS = Counter(
    "llm_model_selections_total",
    "Model selections",
    ["model"]
)

MODEL_LATENCY = Histogram(
    "llm_model_latency_ms",
    "Latency per model",
    ["model"]
)

MODEL_TOKENS = Counter(
    "llm_model_tokens_total",
    "Tokens generated",
    ["model"]
)

MODEL_SCORE = Gauge(
    "llm_model_score",
    "Adaptive routing score",
    ["model"]
)
