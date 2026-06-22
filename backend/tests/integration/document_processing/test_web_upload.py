import json
import subprocess
import sys
import time
import urllib.request
import urllib.parse

HOST = "127.0.0.1"
PORT = 8006

proc = subprocess.Popen(
    [sys.executable, "-c",
     'import uvicorn; uvicorn.run("backend.app.services.document_processing.web.main:app", host="127.0.0.1", port=8006, log_level="warning")'],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)

time.sleep(3)
errors = []

try:
    # Test file upload with bytes using multipart/form-data
    import io
    import uuid

    test_text = b"ARTICLE 1: DEFINITIONS\nSection 1.1. Company. The company is ABC Corp.\nSection 1.2. Agreement. This Agreement means the contract.\n\nARTICLE 2: TERM\nThis Agreement shall commence on the Effective Date."

    boundary = "----" + uuid.uuid4().hex
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="test_upload.txt"\r\n'
        f"Content-Type: text/plain\r\n\r\n"
    ).encode() + test_text + b"\r\n" + f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"http://{HOST}:{PORT}/parse",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    r = urllib.request.urlopen(req)
    assert r.status == 200
    result = json.loads(r.read())
    assert result["summary"]["status"] == "complete"
    assert result["summary"]["word_count"] > 0
    assert result["summary"]["clause_count"] >= 0
    assert len(result["sections"]) > 0
    json.loads(result["json"])  # valid JSON
    print(f"File upload: OK — {result['summary']['word_count']} words, {result['summary']['clause_count']} clauses, {len(result['sections'])} sections")

    # Test download button (just verify JSON is valid)
    parsed = json.loads(result["json"])
    assert "raw_document" in parsed
    assert "metadata" in parsed
    assert "structured_document" in parsed
    assert "clause_document" in parsed
    print("Download JSON: OK — all CIR fields present")

    print("All file upload tests passed!")

except Exception as e:
    errors.append(str(e))
    import traceback
    traceback.print_exc()
finally:
    proc.terminate()
    proc.wait()

if errors:
    print("ERRORS:", errors)
    sys.exit(1)
else:
    print("Done")
