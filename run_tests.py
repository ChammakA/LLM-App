import json
import requests
import re

tests = json.load(open("tests.json"))
passed = 0

for t in tests:
    r = requests.post("http://127.0.0.1:5000/ask", json={"question": t["input"]})
    data = r.json()
    answer = data.get("answer", "")

    if re.search(t["expected"], answer, re.I):
        passed += 1
    print(f"Q: {t['input']}\nA: {answer[:120]}...\n")

print(f"\n Pass Rate: {passed}/{len(tests)} = {passed/len(tests)*100:.1f}%")