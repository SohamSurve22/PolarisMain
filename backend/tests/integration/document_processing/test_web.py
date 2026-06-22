import json
import subprocess
import sys
import time
import urllib.request
import urllib.parse

proc = subprocess.Popen(
    [sys.executable, '-c',
     'import uvicorn; uvicorn.run("backend.app.services.document_processing.web.main:app", host="127.0.0.1", port=8003, log_level="warning")'],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)

time.sleep(3)
try:
    r = urllib.request.urlopen("http://127.0.0.1:8003/")
    print(f"GET /: {r.status} ({len(r.read())} bytes)")

    data = urllib.parse.urlencode({
        "text": 'Section 1. Definitions. "Agreement" means this contract.\nSection 2. Term. This Agreement shall commence on the Effective Date.'
    }).encode()
    r = urllib.request.urlopen("http://127.0.0.1:8003/parse", data=data)
    result = json.loads(r.read())
    print(f"POST /parse: {r.status}")
    print(f"  status: {result['summary']['status']}")
    print(f"  words: {result['summary']['word_count']}")
    print(f"  clauses: {result['summary']['clause_count']}")
    print(f"  sections: {result['summary']['section_count']}")
    print(f"  sections found: {len(result['sections'])}")
    print(f"  JSON size: {len(result['json'])} chars")
    print("OK - all checks passed")
finally:
    proc.terminate()
    proc.wait()
