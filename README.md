# Patch Note Writer (LLM + RAG)

## Overview
This is a small web app that converts user-submitted bullet points into professional patch notes using an LLM.  
It also uses RAG (TF-IDF over previous patch notes) to maintain style consistency.

## Presentation Video

[YouTube Presentaion Video](https://youtu.be/F7YPTNyQ6qI)

## Features
- Categorizes changes: Security, UI, Bug Fixes, Features.
- Adds version numbers automatically (`vYYYY.MM.DD`).
- Logs telemetry: timestamp, pathway (RAG/tool/none), latency, tokens.
- Safety: input length guard, basic prompt-injection detection.
- Offline evaluation: 15+ test cases with pass/fail report.

## Setup
1. Clone the repo
```bash
git clone <repo-url>
cd <repo-folder>
````

2. Create virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

3. Copy `.env.example` → `.env` and fill in your Ollama API details.

4. Seed data

```text
data/patch_notes.json  # Already included
data/style_examples.json
```

## Running the app

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

## Running tests

```bash
python run_tests.py
```

Generates `data/test_results.json` with pass/fail results.

## Notes

* RAG fetches previous notes for style guidance.
* LLM is guarded against prompt injection and oversized inputs.
* Telemetry logged in `telemetry.log`.

---

## Optional fixes for test failures

- **Test 14, 15** fail mostly due to:
  - Rephrasing in Features or UI sections.
  - Multi-category bullets not appearing in both sections.

