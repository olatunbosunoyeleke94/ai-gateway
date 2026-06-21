use std::fs::OpenOptions;
use std::io::Write;
use serde::Serialize;

#[derive(Serialize)]
pub struct InferenceLog {
    pub request_id: String,
    pub prompt: String,
    pub model: String,
    pub start_time: String,
    pub end_time: String,
    pub latency_ms: u128,
}

pub fn write_log(log: &InferenceLog) {
    let mut file = OpenOptions::new()
        .create(true)
        .append(true)
        .open("logs.jsonl")
        .unwrap();

    let json = serde_json::to_string(log).unwrap();
    writeln!(file, "{}", json).unwrap();
}
