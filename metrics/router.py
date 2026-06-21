from statistics import mean
from model_stats import get_model_stats, save_model_stats

def calculate_score(stats):
    latencies = stats.get("latency", [])
    tokens = stats.get("tokens", [])

    avg_latency = mean(latencies) if latencies else 100000
    avg_tokens = mean(tokens) if tokens else 1

    return (avg_tokens * 1000) / (avg_latency + 500)


def score_prompt(prompt: str):
    text = prompt.lower()
    words = len(prompt.split())

    score = 0
    if words > 150: score += 6
    elif words > 80: score += 4
    elif words > 35: score += 2

    code_keywords = ["python", "rust", "code", "function", "class", "debug", "api", "architecture", "```"]
    if any(kw in text for kw in code_keywords):
        score += 3

    reasoning_keywords = ["explain", "compare", "why", "analyze", "design", "tradeoff"]
    if any(kw in text for kw in reasoning_keywords):
        score += 2

    return score


def choose_best_model(candidates):
    scores = {}
    for model in candidates:
        stats = get_model_stats(model)
        scores[model] = calculate_score(stats)
    return max(scores, key=scores.get)


def route_request(prompt, history):
    complexity = score_prompt(prompt)
    gpt_oss_latency = history.get("gpt-oss:20b", 0)

    if complexity <= 2:
        model = choose_best_model(["llama3.2:3b", "qwen2.5:3b"])
        return model, "fast_path"

    elif complexity <= 4:
        model = choose_best_model(["qwen2.5:3b", "qwen3:latest"])
        return model, "reasoning_path"

    elif complexity <= 7:
        model = choose_best_model(["qwen2.5-coder:7b", "qwen3:latest"])
        return model, "code_path"

    else:
        if gpt_oss_latency > 45000:
            print("Warning: gpt-oss:20b too slow, falling back")
            return "qwen3:latest", "premium_fallback"
        return "gpt-oss:20b", "premium_path"
