"""Build the vector index for RAG: knowledge docs + MITRE ATT&CK cloud techniques.

Each chunk is turned into an embedding (Chroma's default model, all-MiniLM-L6-v2)
and stored in a local Chroma database, so the agent can search by meaning.

Run from the project root (rebuilds the index from scratch):
    python src/rag/build_index.py
"""
import json
import re
import sys
from pathlib import Path

import chromadb

sys.path.append(str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402

MAX_CHARS = 2000  # keep chunks short: embeddings work best on focused text


def split_markdown(path: Path) -> list[dict]:
    """Split a markdown file into one chunk per '## ' section."""
    text = path.read_text(encoding="utf-8")
    doc_title = text.splitlines()[0].lstrip("# ").strip()
    chunks = []
    for section in re.split(r"\n(?=## )", text)[1:]:
        heading = section.splitlines()[0].lstrip("# ").strip()
        chunks.append({
            "id": f"{path.stem}:{heading}",
            "text": f"{doc_title} - {section.strip()}"[:MAX_CHARS],
            "metadata": {"source": path.name, "title": heading},
        })
    return chunks


def technique_id(obj: dict) -> str:
    """Return the ATT&CK ID (e.g. T1562.008) of a technique object."""
    for ref in obj.get("external_references", []):
        if ref.get("source_name") == "mitre-attack":
            return ref["external_id"]
    return ""


def clean_description(text: str) -> str:
    """Remove ATT&CK citation markers and extra whitespace."""
    text = re.sub(r"\(Citation:[^)]*\)", "", text)
    return " ".join(text.split())


def load_mitre_cloud_techniques(path: Path) -> list[dict]:
    """Load active ATT&CK techniques that apply to cloud infrastructure (IaaS)."""
    objects = json.loads(path.read_text(encoding="utf-8"))["objects"]
    chunks = []
    for obj in objects:
        if obj.get("type") != "attack-pattern" or obj.get("revoked") or obj.get("x_mitre_deprecated"):
            continue
        if "IaaS" not in obj.get("x_mitre_platforms", []):
            continue
        tid = technique_id(obj)
        text = f"MITRE ATT&CK {tid} {obj['name']}: {clean_description(obj.get('description', ''))}"
        chunks.append({
            "id": f"mitre:{tid}",
            "text": text[:MAX_CHARS],
            "metadata": {"source": "MITRE ATT&CK", "title": f"{tid} {obj['name']}"},
        })
    return chunks


def build_collection(chunks: list[dict]):
    """Create a fresh Chroma collection and add all chunks (embedding happens here)."""
    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    if config.CHROMA_COLLECTION in [c.name for c in client.list_collections()]:
        client.delete_collection(config.CHROMA_COLLECTION)
    collection = client.create_collection(config.CHROMA_COLLECTION, metadata={"hnsw:space": "cosine"})
    collection.add(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks],
    )
    return collection


def main() -> None:
    """Collect all chunks, embed them, and save the index."""
    if not config.MITRE_JSON.exists():
        sys.exit(f"Missing {config.MITRE_JSON}. Download enterprise-attack.json from github.com/mitre/cti.")
    docs = [chunk for path in sorted(config.KNOWLEDGE_DIR.glob("*.md")) for chunk in split_markdown(path)]
    mitre = load_mitre_cloud_techniques(config.MITRE_JSON)
    print(f"Knowledge doc sections: {len(docs)} | MITRE cloud techniques: {len(mitre)}")
    collection = build_collection(docs + mitre)
    print(f"Index saved to {config.CHROMA_DIR.name}/ with {collection.count()} chunks")


if __name__ == "__main__":
    main()
