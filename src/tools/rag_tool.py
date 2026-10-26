"""Tool: semantic search over the security knowledge base (Chroma).

Returns the chunks whose meaning is closest to the query, so the agent can
explain what events mean. Build the index first with src/rag/build_index.py.
"""
import sys
from pathlib import Path

import chromadb

sys.path.append(str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402


def get_collection():
    """Open the existing Chroma collection."""
    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    return client.get_collection(config.CHROMA_COLLECTION)


def search_docs(query: str, k: int = 4) -> list[dict]:
    """Return the k most relevant chunks, each with its source, title and distance."""
    result = get_collection().query(query_texts=[query], n_results=k)
    return [
        {"source": meta["source"], "title": meta["title"], "distance": round(dist, 3), "text": doc}
        for doc, meta, dist in zip(result["documents"][0], result["metadatas"][0], result["distances"][0])
    ]


def format_for_llm(chunks: list[dict]) -> str:
    """Join the chunks into one text block, each labelled with its source."""
    return "\n\n".join(f"[{c['source']} | {c['title']}]\n{c['text']}" for c in chunks)


if __name__ == "__main__":
    # Quick manual test: python src/tools/rag_tool.py "your query"
    for chunk in search_docs(sys.argv[1] if len(sys.argv) > 1 else "who is the root user"):
        print(f"{chunk['distance']:.3f}  {chunk['source']:<22} {chunk['title']}")
