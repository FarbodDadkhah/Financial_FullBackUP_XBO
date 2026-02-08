# Customer Service Support System

## The Vision

This system transforms how bank representatives handle customer inquiries by replacing slow manual knowledge base lookups with an intelligent, AI-powered pipeline that delivers accurate answers in seconds. The **Rep View** gives frontline staff a single place to type any customer question — no matter how emotional, vague, or poorly worded — and instantly receive a polished, source-backed answer with a color-coded confidence score so they know exactly how much to trust it. The **Manager Dashboard** closes the feedback loop by surfacing real-time analytics: which reps are active, which topics dominate, which answers scored low, and how the system performs over time — giving managers actionable oversight without reading a single transcript.

Together, the two screens create a complete operational loop: reps get faster, customers get better answers, and managers spot training gaps and knowledge base weaknesses at a glance — all from one lightweight web app.

## Agent Orchestration

The core intelligence is a sequential 3-agent pipeline where each agent has a single, focused responsibility. **Agent 1 (Reformulation)** takes the raw, messy human input and rewrites it into a precise search query while detecting the topic intent — this is critical because customers say things like "someone stole money off my card" and the system needs to understand that means fraud procedures. **Agent 2 (Search)** uses that refined query to pull the top 3 most relevant chunks from a vector database (ChromaDB with semantic embeddings), then synthesizes those chunks into a coherent, actionable answer via a second LLM call. **Agent 3 (Validation)** acts as a quality gate — it reviews the original question, the reformulated query, and the generated answer together, then assigns a confidence score from 0-100 with explanatory notes. This separation of concerns means each agent can be independently tuned, debugged, and improved, and the validation step ensures no low-quality answer reaches the rep without a clear warning.
