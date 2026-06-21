import redis
import json
import os

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(redis_url, decode_responses=True)

MODELS = [
    "llama3.2:3b",
    "qwen2.5:3b",
    "qwen3:latest",
    "qwen2.5-coder:7b",
    "gpt-oss:20b"
]

def get_model_stats(model: str):
    data = redis_client.get(f"model_stats:{model}")
    if data:
        return json.loads(data)
    # Default
    stats = {"latency": [], "tokens": []}
    save_model_stats(model, stats)
    return stats

def save_model_stats(model: str, stats: dict):
    redis_client.set(f"model_stats:{model}", json.dumps(stats))

# Initialize all models
for m in MODELS:
    get_model_stats(m)
