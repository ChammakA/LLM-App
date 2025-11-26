import re, json, time
from datetime import datetime

TELEMETRY_FILE = "telemetry.log"

def check_input(text):
    if not text.strip():
        raise ValueError("Input cannot be empty.")
    if len(text) > 2000:
        raise ValueError("Input too long")
    
    dangerous_phrases = [
        "ignore previous instructions",
        "ignore all previous instructions",
        "reset system instructions",
        "disregard above",
        "jailbreak",
        "break out of role",
        "you are no longer",
        "system prompt is"
    ]
    lowered = text.lower()
    for phrase in dangerous_phrases:
        if phrase in lowered:
            raise ValueError("Prompt injection attempt detected. Request blocked.")
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
