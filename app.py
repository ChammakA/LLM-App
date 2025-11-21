import os
import time
import json
import subprocess
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from rag_utils import load_notes, build_index, search_index

load_dotenv()
MODEL_NAME = os.getenv("MODEL_NAME", "mistral")

app = Flask(__name__)

print("Loading and embedding notes...")
docs, sources = load_notes()
index, embeddings = build_index(docs)
print("Notes indexed and ready!")

def is_unsafe_input(q: str):
    q_lower = q.lower()
    if len(q_lower) > 300:
        return "Input too long. Please shorten your query to under 300 characters."
    if "ignore previous" in q_lower or "disregard previous" in q_lower:
        return "Unsafe input detected. Please rephrase your query."
    return None

def log_request(question, latency, pathway):
    with open("telemetry.log", "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "timestamp": time.time(),
            "pathway": pathway,
            "question": question,
            "latency": latency
        }) + "\n")

def call_ollama(prompt):
    result = subprocess.run(
        ["ollama", "run", MODEL_NAME],
        input=prompt.encode("utf-8"),
        stdout=subprocess.PIPE
    )
    return result.stdout.decode("utf-8")

@app.route("/ask", methods=["POST"])
def ask():
    start = time.time()
    q = request.json.get("question", "").strip()
    guard = is_unsafe_input(q)
    if guard:
        return jsonify({"error": guard})
    
    results = search_index(q, index, docs, sources)
    context = "\n\n".join([r[0]] for r in results)

    system_prompt = (
        "You are a helpful study assistant. "
        "Only answer using the provided notes. "
        "If unsure, say 'I am not sure, please check notes'"
    )

    full_prompt = f"{system_prompt}\n\nNOTES:\n{context}\n\nQUESTION: {q}\nANSWER:"
    answer = call_ollama(full_prompt)

    latency = round(time.time() - start, 2)
    log_request(q, latency, "RAG")

    return jsonify({"answer": answer.strip(), "latency": latency})

@app.route("/")
def home():
    return """<h2> Study Buddy</h2>
    <p>POST /ask with {"question": "your question"} to get answers based on your notes.</p>"""

if __name__ == "__main__":
    app.run(port=5000, debug=True)