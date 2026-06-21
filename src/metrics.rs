use prometheus::{
    IntCounterVec, HistogramVec, Registry,
};

use std::sync::Arc;

#[derive(Clone)]
pub struct PromMetrics {
    pub registry: Registry,
    pub requests: IntCounterVec,
    pub latency: HistogramVec,
}

impl PromMetrics {
    pub fn new() -> Self {
        let registry = Registry::new();

        let requests = IntCounterVec::new(
            prometheus::opts!("llm_requests_total", "Total LLM requests"),
            &["model"],
        )
        .unwrap();

        let latency = HistogramVec::new(
            prometheus::HistogramOpts::new("llm_latency_ms", "Latency in ms"),
            &["model"],
        )
        .unwrap();

        registry.register(Box::new(requests.clone())).unwrap();
        registry.register(Box::new(latency.clone())).unwrap();

        Self {
            registry,
            requests,
            latency,
        }
    }
}

pub type SharedPromMetrics = Arc<PromMetrics>;
