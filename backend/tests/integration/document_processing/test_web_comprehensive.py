import json
import subprocess
import sys
import time
import urllib.request
import urllib.parse
import uuid

HOST = "127.0.0.1"
PORT = 8007

proc = subprocess.Popen(
    [sys.executable, "-c",
     'import uvicorn; uvicorn.run("backend.app.services.document_processing.web.main:app", host="127.0.0.1", port=8007, log_level="warning")'],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)

time.sleep(3)
passed = 0
failed = []

def check(name, condition, detail=""):
    global passed
    if condition:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed.append(f"{name}: {detail}")
        print(f"  FAIL: {name}")

try:
    # 1. Static files served
    r = urllib.request.urlopen(f"http://{HOST}:{PORT}/static/style.css")
    check("CSS served", r.status == 200 and b"body" in r.read())

    r = urllib.request.urlopen(f"http://{HOST}:{PORT}/static/app.js")
    check("JS served", r.status == 200 and b"parse-form" in r.read())

    # 2. Index page
    r = urllib.request.urlopen(f"http://{HOST}:{PORT}/")
    html = r.read().decode()
    check("Title present", "Polaris Parser Tester" in html)
    check("Parse button present", "Parse Document" in html)
    check("Download button present", "Download JSON" in html)
    check("Text area present", "Paste legal text" in html)
    check("File upload present", "Upload document" in html)
    check("Clear button present", "Clear" in html)
    check("TXT support", ".txt" in html)
    check("PDF support", ".pdf" in html)
    check("DOCX support", ".docx" in html)
    check("HTML support", ".html" in html)
    check("Highlight.js loaded", "highlight.js" in html)
    check("Section hierarchy label", "Section Hierarchy" in html)
    check("Metadata panel label", "Metadata" in html)

    # 3. Parse text
    text = "ARTICLE 1: DEFINITIONS\nSection 1.1. Company. The company is ABC Corp.\nSection 1.2. Agreement. This Agreement means the contract.\n\nARTICLE 2: TERM\nThis Agreement shall commence on the Effective Date."
    data = urllib.parse.urlencode({"text": text}).encode()
    r = urllib.request.urlopen(f"http://{HOST}:{PORT}/parse", data=data)
    result = json.loads(r.read())
    check("Parse status complete", result["summary"]["status"] == "complete")
    check("Word count > 0", result["summary"]["word_count"] > 0)
    check("Clause count >= 0", result["summary"]["clause_count"] >= 0)
    check("Section count > 0", result["summary"]["section_count"] > 0)
    check("Filename present", result["summary"]["filename"] == "input.txt")
    check("Format is txt", result["summary"]["format"] == "txt")
    check("Processing time > 0", result["summary"]["processing_time_ms"] > 0)
    check("JSON output valid", json.loads(result["json"]) is not None)
    check("Sections array present", isinstance(result["sections"], list))
    check("Sections have level/heading", all("level" in s and "heading" in s for s in result["sections"]))
    check("JSON has raw_document", "raw_document" in json.loads(result["json"]))

    # 4. File upload
    boundary = "----" + uuid.uuid4().hex
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="contract.txt"\r\n'
        f"Content-Type: text/plain\r\n\r\n"
    ).encode() + text.encode() + b"\r\n" + f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"http://{HOST}:{PORT}/parse",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    r = urllib.request.urlopen(req)
    result = json.loads(r.read())
    check("File upload status complete", result["summary"]["status"] == "complete")
    check("File upload filename correct", result["summary"]["filename"] == "contract.txt")
    check("File upload word count > 0", result["summary"]["word_count"] > 0)

    # 5. Error handling - empty input
    data = urllib.parse.urlencode({"text": ""}).encode()
    try:
        urllib.request.urlopen(f"http://{HOST}:{PORT}/parse", data=data)
        check("Empty input returns 400", False)
    except urllib.error.HTTPError as e:
        check("Empty input returns 400", e.code == 400)
        err_body = json.loads(e.read())
        check("Empty input has error message", "error" in err_body)

    print(f"\nResults: {passed} passed, {len(failed)} failed")
    if failed:
        for f in failed:
            print(f"  - {f}")
        sys.exit(1)

except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    proc.terminate()
    proc.wait()

print("All tests passed!")
