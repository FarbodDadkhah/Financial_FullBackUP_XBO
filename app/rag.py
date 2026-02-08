import os
import chromadb
from app.config import KB_DIR, CHROMA_DIR, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K


def _chunk_text(text: str, source_file: str) -> list[dict]:
    """Split text into overlapping chunks on paragraph boundaries."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 > CHUNK_SIZE and current:
            chunks.append(current)
            # Keep overlap from end of current chunk
            overlap_text = current[-CHUNK_OVERLAP:] if len(current) > CHUNK_OVERLAP else current
            current = overlap_text + "\n\n" + para
        else:
            current = current + "\n\n" + para if current else para

    if current:
        chunks.append(current)

    return [
        {
            "text": chunk,
            "source_file": source_file,
            "source_title": _title_from_filename(source_file),
        }
        for chunk in chunks
    ]


def _title_from_filename(filename: str) -> str:
    """Convert '01_account_opening.md' to 'Account Opening'."""
    name = filename.replace(".md", "")
    # Remove leading number prefix
    parts = name.split("_", 1)
    if len(parts) > 1 and parts[0].isdigit():
        name = parts[1]
    return name.replace("_", " ").title()


_client: chromadb.ClientAPI | None = None
_collection: chromadb.Collection | None = None


def init_rag() -> int:
    """Load knowledge base into ChromaDB. Returns chunk count."""
    global _client, _collection

    os.makedirs(CHROMA_DIR, exist_ok=True)
    _client = chromadb.PersistentClient(path=CHROMA_DIR)
    _collection = _client.get_or_create_collection(
        name="knowledge_base",
        metadata={"hnsw:space": "cosine"},
    )

    # If already populated, skip
    if _collection.count() > 0:
        return _collection.count()

    # Load and chunk all markdown files
    all_chunks = []
    for filename in sorted(os.listdir(KB_DIR)):
        if not filename.endswith(".md"):
            continue
        filepath = KB_DIR / filename
        text = filepath.read_text(encoding="utf-8")
        all_chunks.extend(_chunk_text(text, filename))

    if not all_chunks:
        return 0

    _collection.add(
        ids=[f"chunk_{i}" for i in range(len(all_chunks))],
        documents=[c["text"] for c in all_chunks],
        metadatas=[{"source_file": c["source_file"], "source_title": c["source_title"]} for c in all_chunks],
    )

    return _collection.count()


def query_knowledge_base(query: str, n_results: int = TOP_K) -> list[dict]:
    """Query ChromaDB and return top matching chunks with metadata."""
    if _collection is None:
        raise RuntimeError("RAG not initialized. Call init_rag() first.")

    results = _collection.query(query_texts=[query], n_results=n_results)

    chunks = []
    for i in range(len(results["ids"][0])):
        chunks.append({
            "text": results["documents"][0][i],
            "source_file": results["metadatas"][0][i]["source_file"],
            "source_title": results["metadatas"][0][i]["source_title"],
            "distance": results["distances"][0][i] if results.get("distances") else None,
        })

    return chunks


def get_document_content(filename: str) -> str | None:
    """Return full content of a knowledge base document."""
    filepath = KB_DIR / filename
    if filepath.exists() and filepath.suffix == ".md":
        return filepath.read_text(encoding="utf-8")
    return None


def list_documents() -> list[str]:
    """Return sorted list of KB document filenames."""
    return sorted(f for f in os.listdir(KB_DIR) if f.endswith(".md"))
