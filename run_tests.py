import json
import re
from app import generate_patch_notes

# Load tests
with open("data/tests.json", "r") as f:
    TESTS = json.load(f)

results = []
passed_count = 0

for i, t in enumerate(TESTS, start=1):
    # Generate patch notes with a fixed version for testing
    output = generate_patch_notes(t["input"], "vTEST", notes_for_rag=[])
    
    # Check expected patterns using substring/regex match
    missing = [p for p in t["expected_patterns"] if not re.search(re.escape(p), output, re.IGNORECASE)]
    passed = len(missing) == 0
    if passed:
        passed_count += 1

    results.append({
        "test_number": i,
        "input": t["input"],
        "output": output,
        "expected_patterns": t["expected_patterns"],
        "missing_patterns": missing,
        "passed": passed
    })

# Save results
with open("data/test_results.json", "w") as f:
    json.dump(results, f, indent=2)

# Print summary
total = len(TESTS)
print(f"Pass rate: {passed_count}/{total} ({passed_count/total*100:.1f}%)")
for r in results:
    if not r["passed"]:
        print(f"Test {r['test_number']} FAILED")
        print("Input:", r["input"])
        print("Missing patterns:", r["missing_patterns"])
        print("-" * 50)
