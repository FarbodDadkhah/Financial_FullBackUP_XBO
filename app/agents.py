import json
import time
from dataclasses import dataclass, field
from anthropic import Anthropic
from app.config import ANTHROPIC_API_KEY, MODEL_NAME
from app.rag import query_knowledge_base

_anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)

REFORMULATION_SYSTEM = """You are a query reformulation agent for a bank's internal knowledge base.
Your job is to take a raw customer service question (possibly informal, emotional, or vague)
and reformulate it into a clear, precise search query optimized for document retrieval.
Also detect the primary intent/topic.

Return ONLY valid JSON in this exact format:
{"reformulated_query": "clear search query", "detected_intent": "topic category"}

Intent categories: account_opening, loans, fees, credit_cards, branch_info, troubleshooting, wire_transfers, fraud, general"""

SEARCH_SYSTEM = """You are a search and synthesis agent for a bank's internal knowledge base.
Given a search query and relevant knowledge base excerpts, synthesize a clear, accurate answer
that a bank representative can use to help their customer.

Be specific, cite relevant details (numbers, timeframes, procedures), and stay factual.
If the knowledge base doesn't contain enough information, say so clearly.

Return ONLY valid JSON in this exact format:
{"answer": "your synthesized answer here"}"""

VALIDATION_SYSTEM = """You are a validation agent that evaluates the quality of answers generated
by a customer service support system. You assess whether the answer is accurate, complete,
relevant to the original question, and safe for a bank representative to relay to a customer.

Score from 0 to 100:
- 90-100: Excellent, directly answers the question with specific details
- 70-89: Good, answers the question but may miss minor details
- 50-69: Acceptable, partially answers but significant gaps
- 30-49: Poor, mostly irrelevant or potentially misleading
- 0-29: Unacceptable, wrong or harmful information

Return ONLY valid JSON in this exact format:
{"confidence_score": 85, "validation_notes": "brief explanation of the score"}"""


def _call_claude(system: str, user_message: str) -> str:
    """Call Claude API and return the text response."""
    response = _anthropic.messages.create(
        model=MODEL_NAME,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def _parse_json(text: str) -> dict | None:
    """Try to parse JSON from Claude's response, handling markdown fences."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]  # Remove opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def agent_reformulate(raw_question: str) -> dict:
    """Agent 1: Reformulate the raw question into a search-optimized query."""
    prompt = f"Raw customer question: {raw_question}"
    response_text = _call_claude(REFORMULATION_SYSTEM, prompt)
    result = _parse_json(response_text)

    if result and "reformulated_query" in result:
        return {
            "reformulated_query": result["reformulated_query"],
            "detected_intent": result.get("detected_intent", "general"),
        }

    # Retry once
    response_text = _call_claude(REFORMULATION_SYSTEM, prompt)
    result = _parse_json(response_text)
    if result and "reformulated_query" in result:
        return {
            "reformulated_query": result["reformulated_query"],
            "detected_intent": result.get("detected_intent", "general"),
        }

    # Fallback
    return {"reformulated_query": raw_question, "detected_intent": "general"}


def agent_search(reformulated_query: str) -> dict:
    """Agent 2: Search knowledge base and synthesize an answer."""
    # Step A: Vector search
    chunks = query_knowledge_base(reformulated_query)

    # Build context from chunks
    context_parts = []
    source_files = []
    source_titles = []
    for chunk in chunks:
        context_parts.append(f"[Source: {chunk['source_title']}]\n{chunk['text']}")
        if chunk["source_file"] not in source_files:
            source_files.append(chunk["source_file"])
            source_titles.append(chunk["source_title"])

    context = "\n\n---\n\n".join(context_parts)

    # Step B: Synthesize answer
    prompt = f"Search query: {reformulated_query}\n\nRelevant knowledge base excerpts:\n\n{context}"
    response_text = _call_claude(SEARCH_SYSTEM, prompt)
    result = _parse_json(response_text)

    if result and "answer" in result:
        answer = result["answer"]
    else:
        # Retry once
        response_text = _call_claude(SEARCH_SYSTEM, prompt)
        result = _parse_json(response_text)
        answer = result["answer"] if result and "answer" in result else "I was unable to generate an answer. Please try rephrasing your question."

    return {
        "answer": answer,
        "source_files": source_files,
        "source_titles": source_titles,
        "chunks": chunks,
    }


def agent_validate(raw_question: str, reformulated_query: str, answer: str, sources: list[str]) -> dict:
    """Agent 3: Validate the answer quality."""
    prompt = (
        f"Original question: {raw_question}\n"
        f"Reformulated query: {reformulated_query}\n"
        f"Generated answer: {answer}\n"
        f"Sources used: {', '.join(sources)}"
    )
    response_text = _call_claude(VALIDATION_SYSTEM, prompt)
    result = _parse_json(response_text)

    if result and "confidence_score" in result:
        return {
            "confidence_score": int(result["confidence_score"]),
            "validation_notes": result.get("validation_notes", ""),
        }

    # Retry once
    response_text = _call_claude(VALIDATION_SYSTEM, prompt)
    result = _parse_json(response_text)
    if result and "confidence_score" in result:
        return {
            "confidence_score": int(result["confidence_score"]),
            "validation_notes": result.get("validation_notes", ""),
        }

    # Fallback
    return {"confidence_score": 0, "validation_notes": "Validation failed to produce a score."}


@dataclass
class PipelineResult:
    rep_id: str = ""
    raw_question: str = ""
    reformulated_query: str = ""
    detected_intent: str = ""
    answer: str = ""
    confidence_score: int = 0
    validation_notes: str = ""
    source_files: list[str] = field(default_factory=list)
    source_titles: list[str] = field(default_factory=list)
    total_time_ms: int = 0
    reformulation_time_ms: int = 0
    search_time_ms: int = 0
    validation_time_ms: int = 0

    def to_dict(self) -> dict:
        return {
            "rep_id": self.rep_id,
            "raw_question": self.raw_question,
            "reformulated_query": self.reformulated_query,
            "detected_intent": self.detected_intent,
            "answer": self.answer,
            "confidence_score": self.confidence_score,
            "validation_notes": self.validation_notes,
            "source_files": self.source_files,
            "source_titles": self.source_titles,
            "total_time_ms": self.total_time_ms,
            "reformulation_time_ms": self.reformulation_time_ms,
            "search_time_ms": self.search_time_ms,
            "validation_time_ms": self.validation_time_ms,
        }


def run_pipeline(raw_question: str, rep_id: str) -> PipelineResult:
    """Execute the full 3-agent pipeline."""
    result = PipelineResult(rep_id=rep_id, raw_question=raw_question)
    total_start = time.time()

    # Agent 1: Reformulation
    t0 = time.time()
    reformulation = agent_reformulate(raw_question)
    result.reformulation_time_ms = int((time.time() - t0) * 1000)
    result.reformulated_query = reformulation["reformulated_query"]
    result.detected_intent = reformulation["detected_intent"]

    # Agent 2: Search
    t0 = time.time()
    search = agent_search(result.reformulated_query)
    result.search_time_ms = int((time.time() - t0) * 1000)
    result.answer = search["answer"]
    result.source_files = search["source_files"]
    result.source_titles = search["source_titles"]

    # Agent 3: Validation
    t0 = time.time()
    validation = agent_validate(
        raw_question, result.reformulated_query, result.answer, result.source_titles
    )
    result.validation_time_ms = int((time.time() - t0) * 1000)
    result.confidence_score = validation["confidence_score"]
    result.validation_notes = validation["validation_notes"]

    result.total_time_ms = int((time.time() - total_start) * 1000)
    return result
