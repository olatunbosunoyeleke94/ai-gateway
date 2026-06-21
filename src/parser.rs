use regex::Regex;
use serde_json::json;
use std::fs::OpenOptions;
use std::io::Write;

/// Extract full inference block metrics from llama.cpp logs
pub fn parse_and_store(log: &str) {
    let tokens_re = Regex::new(r"n_decoded\s*=\s*(\d+)").unwrap();
    let tps_re = Regex::new(r"tg\s*=\s*([\d.]+)\s*t/s").unwrap();
    let eval_time_re = Regex::new(r"eval time\s*=\s*([\d.]+)\s*ms").unwrap();
    let total_time_re = Regex::new(r"total time\s*=\s*([\d.]+)\s*ms").unwrap();

    let tokens = tokens_re
        .captures(log)
        .and_then(|c| c.get(1))
        .and_then(|m| m.as_str().parse::<u64>().ok());

    let tokens_per_sec = tps_re
        .captures(log)
        .and_then(|c| c.get(1))
        .and_then(|m| m.as_str().parse::<f64>().ok());

    let eval_time_ms = eval_time_re
        .captures(log)
        .and_then(|c| c.get(1))
        .and_then(|m| m.as_str().parse::<f64>().ok());

    let total_time_ms = total_time_re
        .captures(log)
        .and_then(|c| c.get(1))
        .and_then(|m| m.as_str().parse::<f64>().ok());

    if let (Some(tokens), Some(tps), Some(eval), Some(total)) =
        (tokens, tokens_per_sec, eval_time_ms, total_time_ms)
    {
        let speedup = if tps > 0.0 { tps / 6.0 } else { 1.0 };

        let record = json!({
            "tokens": tokens,
            "tokens_per_sec": tps,
            "eval_time_ms": eval,
            "total_time_ms": total,
            "speedup_factor": speedup
        });

        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open("metrics.jsonl")
            .unwrap();

        writeln!(file, "{}", record).unwrap();
    }
}
