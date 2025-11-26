import re, json, time
from datetime import datetime

TELEMETRY_FILE = "telemetry.log"

def check_input(text):
    if len(text) > 2000:
        raise ValueError("Input too long")
    if re.search(r"ignore previous instructions", text, re.I):
        raise ValueError("Prompt injection detected")
    return True

def log_telemetry(input_text, pathway, latency, tokens=None):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "pathway": pathway,
        "latency": latency,
        "input_length": len(input_text),
        "tokens": tokens
    }
    with open(TELEMETRY_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def get_version_tag():
    return datetime.utcnow().strftime("v%Y.%m.%d")

def estimate_tokens(text: str) -> int:
    """Simple token appximation: 1 token ~ 4 chars"""
    return len(text) // 4
