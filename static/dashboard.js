async function loadDashboard() {
    try {
        const [overview, reps, system] = await Promise.all([
            fetch("/api/stats/overview").then((r) => r.json()),
            fetch("/api/stats/reps").then((r) => r.json()),
            fetch("/api/stats/system").then((r) => r.json()),
        ]);

        renderOverview(overview);
        renderRepTable(reps);
        renderConfidenceDist(system.confidence_distribution);
        renderTopDocs(system.top_documents);
        renderIntentBreakdown(system.intent_breakdown);
        renderLowConfidence(system.low_confidence_queries);
    } catch (err) {
        console.error("Dashboard load error:", err);
    }
}

function renderOverview(data) {
    document.getElementById("total-queries").textContent = data.total_queries;
    document.getElementById("active-reps").textContent = data.unique_reps;
    document.getElementById("avg-confidence").textContent = data.avg_confidence + "%";
    document.getElementById("avg-time").textContent = (data.avg_time_ms / 1000).toFixed(1) + "s";
}

function renderRepTable(reps) {
    const tbody = document.querySelector("#rep-table tbody");
    const empty = document.getElementById("rep-empty");
    tbody.innerHTML = "";

    if (reps.length === 0) {
        empty.style.display = "block";
        return;
    }
    empty.style.display = "none";

    for (const rep of reps) {
        const tr = document.createElement("tr");
        tr.innerHTML =
            "<td>" + rep.rep_id + "</td>" +
            "<td>" + rep.query_count + "</td>" +
            "<td>" + rep.avg_confidence + "%</td>" +
            "<td>" + rep.top_intent + "</td>" +
            "<td>" + formatTime(rep.last_active) + "</td>";
        tbody.appendChild(tr);
    }
}

function renderConfidenceDist(dist) {
    const container = document.getElementById("confidence-dist");
    const total = (dist.high || 0) + (dist.medium || 0) + (dist.low || 0);
    if (total === 0) {
        container.innerHTML = '<p class="empty-msg">No data yet</p>';
        return;
    }
    const maxVal = Math.max(dist.high, dist.medium, dist.low, 1);
    container.innerHTML =
        buildBar("High (80-100)", dist.high, maxVal, "green") +
        buildBar("Medium (50-79)", dist.medium, maxVal, "yellow") +
        buildBar("Low (0-49)", dist.low, maxVal, "red");
}

function renderTopDocs(docs) {
    const container = document.getElementById("top-docs");
    if (docs.length === 0) {
        container.innerHTML = '<p class="empty-msg">No data yet</p>';
        return;
    }
    const maxVal = Math.max(...docs.map((d) => d.count), 1);
    container.innerHTML = docs
        .map((d) => {
            const label = d.file.replace(".md", "").replace(/^\d+_/, "").replace(/_/g, " ");
            return buildBar(label, d.count, maxVal, "blue");
        })
        .join("");
}

function renderIntentBreakdown(intents) {
    const container = document.getElementById("intent-breakdown");
    if (intents.length === 0) {
        container.innerHTML = '<p class="empty-msg">No data yet</p>';
        return;
    }
    const maxVal = Math.max(...intents.map((i) => i.cnt), 1);
    container.innerHTML = intents
        .map((i) => buildBar(i.detected_intent, i.cnt, maxVal, "blue"))
        .join("");
}

function renderLowConfidence(queries) {
    const tbody = document.querySelector("#low-conf-table tbody");
    const empty = document.getElementById("low-conf-empty");
    tbody.innerHTML = "";

    if (queries.length === 0) {
        empty.style.display = "block";
        return;
    }
    empty.style.display = "none";

    for (const q of queries) {
        const tr = document.createElement("tr");
        const question = q.raw_question.length > 80
            ? q.raw_question.substring(0, 80) + "..."
            : q.raw_question;
        tr.innerHTML =
            "<td>" + escapeHtml(question) + "</td>" +
            '<td><span class="confidence-badge confidence-low">' + q.confidence_score + "%</span></td>" +
            "<td>" + formatTime(q.created_at) + "</td>";
        tbody.appendChild(tr);
    }
}

function buildBar(label, value, max, color) {
    const pct = max > 0 ? (value / max) * 100 : 0;
    return (
        '<div class="bar-row">' +
        '<span class="bar-label">' + escapeHtml(label) + "</span>" +
        '<div class="bar-track"><div class="bar-fill ' + color + '" style="width:' + pct + '%">' +
        (pct > 15 ? value : "") +
        "</div></div>" +
        '<span class="bar-count">' + value + "</span>" +
        "</div>"
    );
}

function formatTime(ts) {
    if (!ts) return "N/A";
    try {
        const d = new Date(ts + "Z");
        return d.toLocaleString();
    } catch {
        return ts;
    }
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// Initial load
loadDashboard();

// Auto-refresh every 30 seconds
setInterval(loadDashboard, 30000);
