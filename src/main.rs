mod metrics;

use axum::{
    extract::State,
    routing::{get, post},
    Json, Router,
};

use serde::{Deserialize, Serialize};
use std::sync::{Arc, Mutex};
use std::time::Instant;
use uuid::Uuid;

use metrics::{PromMetrics, SharedPromMetrics};

#[derive(Clone)]
struct AppState {
    prom: SharedPromMetrics,
}

#[derive(Deserialize)]
struct GenerateRequest {
    prompt: String,
    model: Option<String>,
}

#[derive(Serialize)]
struct GenerateResponse {
    response: String,
    request_id: String,
    model_used: String,
}

#[tokio::main]
async fn main() {
    let prom = Arc::new(PromMetrics::new());

    let state = AppState { prom };

    let app = Router::new()
        .route("/generate", post(generate))
        .route("/metrics", get(metrics))
        .with_state(state);

    println!("🚀 Gateway running on http://localhost:3000");

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000")
        .await
        .unwrap();

    axum::serve(listener, app).await.unwrap();
}

async fn call_ollama(model: &str, prompt: &str) -> String {
    let client = reqwest::Client::new();

    let res = client
        .post("http://localhost:11434/api/generate")
        .json(&serde_json::json!({
            "model": model,
            "prompt": prompt,
            "stream": false
        }))
        .send()
        .await;

    match res {
        Ok(r) => r.text().await.unwrap_or_else(|_| "ollama_error".to_string()),
        Err(_) => "ollama_error".to_string(),
    }
}

async fn generate(
    State(state): State<AppState>,
    Json(req): Json<GenerateRequest>,
) -> Json<GenerateResponse> {
    let request_id = Uuid::new_v4().to_string();
    let start = Instant::now();

    let model_used = req.model.unwrap_or_else(|| "llama3.2:3b".to_string());

    // 🔥 REAL OLLAMA CALL
    let response_text = call_ollama(&model_used, &req.prompt).await;

    let latency_ms = start.elapsed().as_millis() as f64;

    // 📊 PROMETHEUS METRICS
    state
        .prom
        .requests
        .with_label_values(&[&model_used])
        .inc();

    state
        .prom
        .latency
        .with_label_values(&[&model_used])
        .observe(latency_ms);

    println!(
        "[TRACE] id={} model={} latency={}ms",
        request_id, model_used, latency_ms
    );

    Json(GenerateResponse {
        response: response_text,
        request_id,
        model_used,
    })
}

async fn metrics(State(state): State<AppState>) -> String {
    use prometheus::Encoder;

    let encoder = prometheus::TextEncoder::new();
    let metric_families = state.prom.registry.gather();

    let mut buffer = Vec::new();
    encoder.encode(&metric_families, &mut buffer).unwrap();

    String::from_utf8(buffer).unwrap()
}
