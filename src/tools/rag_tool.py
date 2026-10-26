"""Tool: search the security knowledge base (Chroma index).

Three search methods:
- vector: semantic similarity of embeddings (meaning)
- bm25:   keyword match (exact words such as 'RequestLimitExceeded')
- hybrid: both rankings merged with Reciprocal Rank Fusion (RRF)
Build the index first with src/rag/build_index.py.
"""
import re
import sys
from functools import lru_cache
from pathlib import Path

import chromadb
from rank_bm25 import BM25Okapi

sys.path.append(str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402

CANDIDATES = 20  # how many results each method contributes before fusion
RRF_K = 60       # standard RRF constant: damps the weight of top ranks


@lru_cache(maxsize=1)
def get_collection():
    """Open the existing Chroma collection (once per process)."""
    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    return client.get_collection(config.CHROMA_COLLECTION)


def tokenize(text: str) -> list[str]:
    """Lowercase words and codes; keeps tokens like 'requestlimitexceeded' and 't1496'."""
    return re.findall(r"[a-z0-9_.]+", text.lower())


@lru_cache(maxsize=1)
def get_bm25():
    """Build a BM25 keyword index over all chunks (once per process)."""
    data = get_collection().get(include=["documents", "metadatas"])
    chunks = [{"id": i, "text": d, "source": m["source"], "title": m["title"]}
              for i, d, m in zip(data["ids"], data["documents"], data["metadatas"])]
    return BM25Okapi([tokenize(c["text"]) for c in chunks]), chunks


def search_vector(query: str, k: int) -> list[dict]:
    """Top-k chunks by embedding similarity."""
    result = get_collection().query(query_texts=[query], n_results=k)
    return [{"id": i, "text": d, "source": m["source"], "title": m["title"]}
            for i, d, m in zip(result["ids"][0], result["documents"][0], result["metadatas"][0])]


def search_bm25(query: str, k: int) -> list[dict]:
    """Top-k chunks by BM25 keyword score."""
    bm25, chunks = get_bm25()
    scores = bm25.get_scores(tokenize(query))
    order = sorted(range(len(chunks)), key=lambda i: scores[i], reverse=True)
    return [chunks[i] for i in order[:k]]


def search_hybrid(query: str, k: int) -> list[dict]:
    """Merge vector and BM25 rankings with Reciprocal Rank Fusion: score = sum 1/(RRF_K + rank)."""
    scores, by_id = {}, {}
    for ranking in (search_vector(query, CANDIDATES), search_bm25(query, CANDIDATES)):
        for rank, chunk in enumerate(ranking, start=1):
            scores[chunk["id"]] = scores.get(chunk["id"], 0.0) + 1.0 / (RRF_K + rank)
            by_id[chunk["id"]] = chunk
    best = sorted(scores, key=scores.get, reverse=True)[:k]
    return [by_id[i] for i in best]


SEARCH_METHODS = {"vector": search_vector, "bm25": search_bm25, "hybrid": search_hybrid}


def search_docs(query: str, k: int = 4, method: str | None = None) -> list[dict]:
    """Return the k most relevant chunks with the chosen (or configured) method."""
    return SEARCH_METHODS[method or config.RAG_METHOD](query, k)


def format_for_llm(chunks: list[dict]) -> str:
    """Join the chunks into one text block, each labelled with its source."""
    return "\n\n".join(f"[{c['source']} | {c['title']}]\n{c['text']}" for c in chunks)


if __name__ == "__main__":
    # Quick manual test: python src/tools/rag_tool.py "your query"
    q = sys.argv[1] if len(sys.argv) > 1 else "who is the root user"
    for name in SEARCH_METHODS:
        print(f"{name:<7}", [c["title"] for c in search_docs(q, method=name)])
