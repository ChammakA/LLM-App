import os
import json
import time
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from utils import check_input, log_telemetry, get_version_tag, estimate_tokens
from rag import get_relevant_notes

load_dotenv()
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

app = Flask(__name__)

# --- System prompt ---
SYSTEM_PROMPT = """
You are a professional patch-note writer.
Rules:
- ONLY write patch notes using the user-provided changes.
- DO NOT add any categories or sections that do not have changes.
- MUST categorize every bullet exactly under the correct section (Security, UI, Bug Fixes, Features).
- Expand each bullet into 1–2 sentences if needed, but do not invent new features, bug fixes, or security items.
- Expand each bullet point into 1–2 sub-bullet point sentences.
- DO NOT add any closing statements, greetings, or extra commentary. Only list the categorized changes as bullets and sub-bullets, then stop.
- Use previous notes only to match formatting and style, NEVER content.
- Use only '*' for bullets.
- Include version at the top: Version: vYYYY.MM.DD
- Do NOT hallucinate dates, versions, emojis, or extra sections.
"""

# --- Token limit settings ---
MAX_MODEL_TOKENS = 1500
MAX_RAG_TOKENS = 400
MAX_USER_TOKENS = MAX_MODEL_TOKENS - MAX_RAG_TOKENS
MAX_USER_CHARS = MAX_USER_TOKENS * 4

# --- Helper: categorize user input ---
def categorize_changes(user_text):
    categories = {"Security": [], "UI": [], "Bug Fixes": [], "Features": []}
    for line in user_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        content = line[2:].strip() if line.startswith("- ") else line
        content_lower = content.lower()
        if any(k in content_lower for k in ["security", "auth"]):
            categories["Security"].append(content)
        elif any(k in content_lower for k in ["ui", "interface", "dark mode", "theme"]):
            categories["UI"].append(content)
        elif any(k in content_lower for k in ["bug", "fix", "error", "crash"]):
            categories["Bug Fixes"].append(content)
        else:
            categories["Features"].append(content)
    # Remove empty categories
    return {cat: items for cat, items in categories.items() if items}

# --- Generate patch notes ---
def generate_patch_notes(user_text, version_tag, notes_for_rag):
    # --- Retrieve relevant previous notes dynamically ---
    previous_notes_for_rag = get_relevant_notes(user_text, k=3)
    context_text = "\n".join(previous_notes_for_rag) if previous_notes_for_rag else ""

    # --- Categorize user changes ---
    categories = categorize_changes(user_text)
    category_summary = "\n".join([f"{cat}: {', '.join(lines)}" for cat, lines in categories.items()])

    # --- Token limit check ---
    total_input_tokens = estimate_tokens(user_text) + estimate_tokens(context_text) + estimate_tokens(category_summary)
    if total_input_tokens > MAX_MODEL_TOKENS - 50:
        raise ValueError(f"Input too long! Approx max {MAX_USER_CHARS} characters allowed.")

    # --- LLM payload ---
    prompt = f"""{SYSTEM_PROMPT}

Previous notes for style guidance (DO NOT copy content):
{context_text}

Suggested categories based on input changes:
{category_summary}

Version: {version_tag}
Changes:
{user_text}

Patch Notes:"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "temperature": 0.2,
        "max_tokens": MAX_MODEL_TOKENS
    }

    start_time = time.time()
    response = requests.post(f"{OLLAMA_API_URL}/v1/completions", json=payload)
    latency = time.time() - start_time

    if response.status_code != 200:
        raise RuntimeError(f"LLM error: {response.status_code} {response.text}")

    result = response.json()
    patch_notes = ""
    if "completion" in result:
        patch_notes = result["completion"].strip()
    elif "choices" in result and len(result["choices"]) > 0:
        patch_notes = result["choices"][0].get("text", "").strip()

    if not patch_notes:
        raise RuntimeError("LLM returned empty completion")

    # --- Telemetry ---
    user_tokens = estimate_tokens(user_text)
    response_tokens = estimate_tokens(patch_notes)
    total_tokens = user_tokens + response_tokens
    log_telemetry(user_text, pathway="RAG" if previous_notes_for_rag else "tool", latency=latency, tokens=total_tokens)

    # --- Append previous notes at bottom ---
    previous_notes_text = "\n\n--- Previous Patch Notes ---\n" + "\n".join(notes_for_rag) if notes_for_rag else ""
    final_patch_notes = patch_notes + previous_notes_text

    return final_patch_notes

# --- Routes ---
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    try:
        text = request.form.get("changes", "")
        check_input(text)
        version_tag = get_version_tag()

        # --- Load existing notes ---
        patch_file = "data/patch_notes.json"
        try:
            with open(patch_file, "r") as f:
                notes = json.load(f)
        except FileNotFoundError:
            notes = []

        # --- Prepare note entry for JSON storage ---
        summary_bullets = [line[2:].strip() for line in text.split("\n") if line.startswith("- ")]
        summary_text = "; ".join(summary_bullets)
        version_entry = f"{version_tag}: {summary_text}"

        # --- Generate patch notes, pass full history for previous notes section ---
        patch_notes = generate_patch_notes(text, version_tag, notes)

        # --- Append new note AFTER generating patch notes ---
        notes.append(version_entry)
        with open(patch_file, "w") as f:
            json.dump(notes, f, indent=2)

        return jsonify({"patch_notes": patch_notes, "version": version_tag})

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
