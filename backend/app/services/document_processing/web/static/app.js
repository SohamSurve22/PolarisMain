(function () {
  const formEl = document.getElementById("parse-form");
  const textEl = document.getElementById("text");
  const fileEl = document.getElementById("file");
  const parseBtn = document.getElementById("parse-btn");
  const clearBtn = document.getElementById("clear-btn");
  const errorBox = document.getElementById("error-box");
  const metadataPanel = document.getElementById("metadata-panel");
  const jsonPanel = document.getElementById("json-panel");
  const emptyState = document.getElementById("empty-state");
  const jsonOutput = document.getElementById("json-output");
  const downloadBtn = document.getElementById("download-btn");
  const hierarchyEl = document.getElementById("hierarchy");
  const sectionCountBadge = document.getElementById("section-count-badge");

  ["m-status","m-filename","m-format","m-language","m-words","m-chars","m-pages","m-sections","m-clauses","m-time"].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.textContent = "-";
  });

  function showError(msg) {
    errorBox.textContent = msg;
    errorBox.classList.remove("hidden");
    metadataPanel.classList.add("hidden");
    jsonPanel.classList.add("hidden");
    emptyState.classList.add("hidden");
  }

  function hideError() {
    errorBox.classList.add("hidden");
  }

  function setLoading(v) {
    if (v) {
      parseBtn.disabled = true;
      parseBtn.innerHTML = '<span id="spinner"></span> Parsing...';
    } else {
      parseBtn.disabled = false;
      parseBtn.textContent = "Parse Document";
    }
  }

  function fillMetadata(summary) {
    document.getElementById("m-status").textContent = summary.status || "-";
    document.getElementById("m-filename").textContent = summary.filename || "-";
    document.getElementById("m-format").textContent = summary.format || "-";
    document.getElementById("m-language").textContent = summary.language || "-";
    document.getElementById("m-words").textContent = summary.word_count != null ? summary.word_count.toLocaleString() : "-";
    document.getElementById("m-chars").textContent = summary.char_count != null ? summary.char_count.toLocaleString() : "-";
    document.getElementById("m-pages").textContent = summary.page_count != null ? summary.page_count : "-";
    document.getElementById("m-sections").textContent = summary.section_count != null ? summary.section_count : "-";
    document.getElementById("m-clauses").textContent = summary.clause_count != null ? summary.clause_count : "-";
    document.getElementById("m-time").textContent = summary.processing_time_ms != null ? summary.processing_time_ms + " ms" : "-";
  }

  function fillHierarchy(sections) {
    hierarchyEl.innerHTML = "";
    sectionCountBadge.textContent = sections.length;

    if (sections.length === 0) {
      hierarchyEl.innerHTML = '<div class="section-entry" style="color:#8b949e;">(no sections detected)</div>';
      return;
    }

    sections.forEach(function (s) {
      var div = document.createElement("div");
      div.className = "section-entry";

      var indent = document.createElement("span");
      indent.className = "level-indent";
      indent.textContent = "  ".repeat(s.level) + "-";
      div.appendChild(indent);

      var heading = document.createElement("span");
      heading.className = "heading-text";
      heading.textContent = " " + s.heading;
      div.appendChild(heading);

      if (s.page_number != null) {
        var page = document.createElement("span");
        page.className = "page-tag";
        page.textContent = "[p. " + s.page_number + "]";
        div.appendChild(page);
      }

      hierarchyEl.appendChild(div);
    });
  }

  function showResult(data) {
    hideError();
    emptyState.classList.add("hidden");
    metadataPanel.classList.remove("hidden");
    jsonPanel.classList.remove("hidden");

    fillMetadata(data.summary);
    fillHierarchy(data.sections);

    jsonOutput.textContent = data.json;
    hljs.highlightElement(jsonOutput);
  }

  formEl.addEventListener("submit", async function (e) {
    e.preventDefault();
    hideError();

    var fd = new FormData();
    fd.append("text", textEl.value);

    if (fileEl.files.length > 0) {
      fd.append("file", fileEl.files[0]);
    }

    if (!textEl.value.trim() && fileEl.files.length === 0) {
      showError("Paste text or upload a file.");
      return;
    }

    setLoading(true);

    try {
      var resp = await fetch("/parse", { method: "POST", body: fd });
      var data = await resp.json();

      if (!resp.ok) {
        showError(data.error || "Request failed with status " + resp.status);
        return;
      }

      if (data.error) {
        showError(data.error);
        return;
      }

      showResult(data);
    } catch (err) {
      showError("Network error: " + err.message);
    } finally {
      setLoading(false);
    }
  });

  clearBtn.addEventListener("click", function () {
    textEl.value = "";
    fileEl.value = "";
    hideError();
    metadataPanel.classList.add("hidden");
    jsonPanel.classList.add("hidden");
    emptyState.classList.remove("hidden");
  });

  downloadBtn.addEventListener("click", function () {
    var text = jsonOutput.textContent;
    if (!text || text === "-") return;
    var blob = new Blob([text], { type: "application/json" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = "polaris_ir.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });

  fileEl.addEventListener("change", function () {
    if (this.files.length > 0) {
      textEl.placeholder = "File selected: " + this.files[0].name + " (text will be ignored)";
    } else {
      textEl.placeholder = "Paste legal document text here, or upload a file below...";
    }
  });
})();
