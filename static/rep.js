async function submitQuery() {
    const repId = document.getElementById("rep-id").value;
    const question = document.getElementById("question").value.trim();

    if (!question) {
        alert("Please enter a question.");
        return;
    }

    const btn = document.getElementById("submit-btn");
    const loading = document.getElementById("loading");
    const result = document.getElementById("result");

    btn.disabled = true;
    loading.classList.remove("hidden");
    result.classList.add("hidden");

    try {
        const resp = await fetch("/api/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question, rep_id: repId }),
        });

        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || "Request failed");
        }

        const data = await resp.json();
        displayResult(data);
    } catch (err) {
        alert("Error: " + err.message);
    } finally {
        btn.disabled = false;
        loading.classList.add("hidden");
    }
}

function displayResult(data) {
    const result = document.getElementById("result");
    result.classList.remove("hidden");

    // Confidence badge
    const badge = document.getElementById("confidence-badge");
    const score = data.confidence_score;
    badge.textContent = score + "%";
    badge.className = "confidence-badge";
    if (score >= 80) badge.classList.add("confidence-high");
    else if (score >= 50) badge.classList.add("confidence-medium");
    else badge.classList.add("confidence-low");

    // Reformulated query
    document.getElementById("reformulated-query").textContent = data.reformulated_query;
    document.getElementById("intent-tag").textContent = data.detected_intent;

    // Answer
    document.getElementById("answer-text").textContent = data.answer;

    // Sources
    const sourcesEl = document.getElementById("sources");
    sourcesEl.innerHTML = "";
    for (let i = 0; i < data.source_files.length; i++) {
        const a = document.createElement("a");
        a.href = "/document/" + data.source_files[i];
        a.target = "_blank";
        a.className = "source-link";
        a.textContent = data.source_titles[i];
        sourcesEl.appendChild(a);
    }

    // Validation notes
    document.getElementById("validation-notes").textContent = data.validation_notes || "N/A";

    // Timing
    const totalSec = (data.total_time_ms / 1000).toFixed(1);
    const parts = [];
    if (data.reformulation_time_ms) parts.push("Reformulation: " + data.reformulation_time_ms + "ms");
    if (data.search_time_ms) parts.push("Search: " + data.search_time_ms + "ms");
    if (data.validation_time_ms) parts.push("Validation: " + data.validation_time_ms + "ms");
    document.getElementById("time-info").textContent =
        "Total: " + totalSec + "s | " + parts.join(" | ");
}

// Submit on Ctrl+Enter
document.getElementById("question").addEventListener("keydown", function (e) {
    if (e.ctrlKey && e.key === "Enter") {
        submitQuery();
    }
});
