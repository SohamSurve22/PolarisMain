import json
import sys
sys.path.insert(0, "D:\\Soham\\Engineering\\Final_Proj\\Codebase")

from backend.app.services.document_processing.web.main import _run_pipeline, _detect_format

# Test 1: basic text
r = _run_pipeline(b"Section 1. Definitions. Agreement means this contract.", "test.txt")
assert r["summary"]["status"] == "complete", r
print(f"Test 1 OK: words={r['summary']['word_count']} clauses={r['summary']['clause_count']} sections={len(r['sections'])}")

# Test 2: with headings
text = b"ARTICLE 1: DEFINITIONS\nSection 1.1. Company. The company is ABC Corp.\nSection 1.2. Agreement. This Agreement means the contract.\n\nARTICLE 2: TERM\nThis Agreement shall commence on the Effective Date."
r2 = _run_pipeline(text, "agreement.txt")
assert r2["summary"]["status"] == "complete", r2
print(f"Test 2 OK: words={r2['summary']['word_count']} clauses={r2['summary']['clause_count']} sections={len(r2['sections'])}")
for s in r2["sections"]:
    print(f"  L{s['level']}: {s['heading'][:60]}")

# Test 3: valid JSON output
parsed = json.loads(r["json"])
print(f"Test 3 OK: JSON roundtrip, {len(r['json'])} chars")

# Test 4: error handling
try:
    _detect_format("test.xyz")
    assert False, "Should have raised"
except Exception as e:
    print(f"Test 4 OK: format detection raises: {e}")

print("All tests passed!")
