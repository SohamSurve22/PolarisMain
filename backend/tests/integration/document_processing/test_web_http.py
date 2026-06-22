import json
import subprocess
import sys
import time
import urllib.request
import urllib.parse

HOST = "127.0.0.1"
PORT = 8005

proc = subprocess.Popen(
    [sys.executable, "-c",
     'import uvicorn; uvicorn.run("backend.app.services.document_processing.web.main:app", host="127.0.0.1", port=8005, log_level="warning")'],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)

time.sleep(3)
errors = []

try:
    # Test GET /
    r = urllib.request.urlopen(f"http://{HOST}:{PORT}/")
    assert r.status == 200
    html = r.read().decode()
    assert "Polaris Parser Tester" in html
    assert "Parse Document" in html
    assert "Download JSON" in html
    assert ".txt" in html
    assert ".pdf" in html
    assert ".docx" in html
    assert ".html" in html
    print(f"GET /: OK ({len(html)} bytes, form elements present)")

    # Test POST with text
    data = urllib.parse.urlencode({
        "text": "Section 1. Definitions. Agreement means this contract.\nSection 2. Term. The term shall be one year."
    }).encode()
    r = urllib.request.urlopen(f"http://{HOST}:{PORT}/parse", data=data)
    assert r.status == 200
    result = json.loads(r.read())
    assert result["summary"]["status"] == "complete"
    assert result["summary"]["word_count"] > 0
    assert result["summary"]["clause_count"] >= 0
    json.loads(result["json"])  # valid JSON
    print(f"POST /parse (text): OK — {result['summary']['word_count']} words, {result['summary']['clause_count']} clauses")

    # Test POST with empty input -> 400
    data = urllib.parse.urlencode({"text": ""}).encode()
    try:
        urllib.request.urlopen(f"http://{HOST}:{PORT}/parse", data=data)
        errors.append("Empty input should have returned 400")
    except urllib.error.HTTPError as e:
        assert e.code == 400
        err_body = json.loads(e.read())
        assert "error" in err_body
        print(f"POST /parse (empty): OK — 400: {err_body['error']}")

    print("All HTTP endpoint tests passed!")

except Exception as e:
    errors.append(str(e))
finally:
    proc.terminate()
    proc.wait()

if errors:
    print("ERRORS:", errors)
    sys.exit(1)
else:
    print("Done")
