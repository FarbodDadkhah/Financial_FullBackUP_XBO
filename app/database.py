import json
import os
import sqlite3
from app.config import SQLITE_PATH, DATA_DIR

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS queries (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    rep_id                TEXT NOT NULL,
    raw_question          TEXT NOT NULL,
    reformulated_query    TEXT NOT NULL,
    detected_intent       TEXT NOT NULL,
    answer                TEXT NOT NULL,
    confidence_score      INTEGER NOT NULL,
    validation_notes      TEXT,
    source_files          TEXT NOT NULL,
    source_titles         TEXT NOT NULL,
    total_time_ms         INTEGER NOT NULL,
    reformulation_time_ms INTEGER,
    search_time_ms        INTEGER,
    validation_time_ms    INTEGER,
    created_at            TEXT DEFAULT (datetime('now'))
);
"""


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create database and tables if they don't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = _get_conn()
    conn.execute(_CREATE_TABLE)
    conn.commit()
    conn.close()


def log_query(data: dict):
    """Insert a completed pipeline result into the queries table."""
    conn = _get_conn()
    conn.execute(
        """INSERT INTO queries
           (rep_id, raw_question, reformulated_query, detected_intent,
            answer, confidence_score, validation_notes,
            source_files, source_titles,
            total_time_ms, reformulation_time_ms, search_time_ms, validation_time_ms)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data["rep_id"],
            data["raw_question"],
            data["reformulated_query"],
            data["detected_intent"],
            data["answer"],
            data["confidence_score"],
            data.get("validation_notes", ""),
            json.dumps(data["source_files"]),
            json.dumps(data["source_titles"]),
            data["total_time_ms"],
            data.get("reformulation_time_ms"),
            data.get("search_time_ms"),
            data.get("validation_time_ms"),
        ),
    )
    conn.commit()
    conn.close()


def get_overview_stats() -> dict:
    """Return total queries, unique reps, avg confidence, avg time."""
    conn = _get_conn()
    row = conn.execute(
        """SELECT
             COUNT(*) as total_queries,
             COUNT(DISTINCT rep_id) as unique_reps,
             COALESCE(ROUND(AVG(confidence_score), 1), 0) as avg_confidence,
             COALESCE(ROUND(AVG(total_time_ms), 0), 0) as avg_time_ms
           FROM queries"""
    ).fetchone()
    conn.close()
    return dict(row)


def get_rep_stats() -> list[dict]:
    """Return per-rep stats."""
    conn = _get_conn()
    rows = conn.execute(
        """SELECT
             rep_id,
             COUNT(*) as query_count,
             ROUND(AVG(confidence_score), 1) as avg_confidence,
             detected_intent as top_intent,
             MAX(created_at) as last_active
           FROM queries
           GROUP BY rep_id
           ORDER BY query_count DESC"""
    ).fetchall()
    conn.close()

    results = []
    for row in rows:
        row_dict = dict(row)
        # Get the most common intent per rep
        conn2 = _get_conn()
        intent_row = conn2.execute(
            """SELECT detected_intent, COUNT(*) as cnt
               FROM queries WHERE rep_id = ?
               GROUP BY detected_intent ORDER BY cnt DESC LIMIT 1""",
            (row_dict["rep_id"],),
        ).fetchone()
        conn2.close()
        row_dict["top_intent"] = intent_row["detected_intent"] if intent_row else "N/A"
        results.append(row_dict)

    return results


def get_system_stats() -> dict:
    """Return system-wide analytics."""
    conn = _get_conn()

    # Confidence distribution
    brackets = conn.execute(
        """SELECT
             SUM(CASE WHEN confidence_score >= 80 THEN 1 ELSE 0 END) as high,
             SUM(CASE WHEN confidence_score >= 50 AND confidence_score < 80 THEN 1 ELSE 0 END) as medium,
             SUM(CASE WHEN confidence_score < 50 THEN 1 ELSE 0 END) as low
           FROM queries"""
    ).fetchone()

    # Most used documents
    all_sources = conn.execute("SELECT source_files FROM queries").fetchall()
    doc_counts: dict[str, int] = {}
    for row in all_sources:
        for f in json.loads(row["source_files"]):
            doc_counts[f] = doc_counts.get(f, 0) + 1
    top_docs = sorted(doc_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # Intent breakdown
    intents = conn.execute(
        """SELECT detected_intent, COUNT(*) as cnt
           FROM queries GROUP BY detected_intent
           ORDER BY cnt DESC"""
    ).fetchall()

    # Low confidence queries
    low_conf = conn.execute(
        """SELECT raw_question, confidence_score, created_at
           FROM queries WHERE confidence_score < 50
           ORDER BY created_at DESC LIMIT 10"""
    ).fetchall()

    # Daily trend (last 7 days)
    daily = conn.execute(
        """SELECT DATE(created_at) as day, COUNT(*) as cnt
           FROM queries
           GROUP BY DATE(created_at)
           ORDER BY day DESC LIMIT 7"""
    ).fetchall()

    conn.close()

    return {
        "confidence_distribution": {
            "high": brackets["high"] or 0,
            "medium": brackets["medium"] or 0,
            "low": brackets["low"] or 0,
        },
        "top_documents": [{"file": f, "count": c} for f, c in top_docs],
        "intent_breakdown": [dict(r) for r in intents],
        "low_confidence_queries": [dict(r) for r in low_conf],
        "daily_trend": [dict(r) for r in daily],
    }
