import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

from core.config import get_settings

settings = get_settings()

# ---------------------------------------------------------------------------
# JSON loaders
# ---------------------------------------------------------------------------

def load_courses() -> list[Document]:
    """Load kayfa_courses.json → one Document per course."""
    path = settings.JSON_DIR / "kayfa_courses.json"
    if not path.exists():
        print(f"[ingest] Warning: {path} not found")
        return []

    with open(path, "r", encoding="utf-8") as f:
        courses = json.load(f)

    docs: list[Document] = []
    for c in courses:
        text = _course_to_text(c)
        docs.append(
            Document(
                page_content=text,
                metadata={
                    "source": "kayfa_courses.json",
                    "doc_id": c["id"],
                    "doc_type": "course",
                    "track": c.get("track", []),
                    "level": c.get("level", ""),
                    "roadmaps": c.get("roadmaps", []),
                },
            )
        )
    print(f"[ingest] Loaded {len(docs)} courses")
    return docs


def load_roadmaps() -> list[Document]:
    """Load kayfa_roadmaps.json → one Document per roadmap/track."""
    path = settings.JSON_DIR / "kayfa_roadmaps.json"
    if not path.exists():
        print(f"[ingest] Warning: {path} not found")
        return []

    with open(path, "r", encoding="utf-8") as f:
        roadmaps = json.load(f)

    docs: list[Document] = []
    for r in roadmaps:
        text = _roadmap_to_text(r)
        docs.append(
            Document(
                page_content=text,
                metadata={
                    "source": "kayfa_roadmaps.json",
                    "doc_id": r["id"],
                    "doc_type": "roadmap",
                    "track": r.get("track", []),
                    "duration": r.get("duration", ""),
                    "courses_count": r.get("courses_count", 0),
                },
            )
        )
    print(f"[ingest] Loaded {len(docs)} roadmaps")
    return docs


# ---------------------------------------------------------------------------
# Markdown loader (basic section-aware splitting)
# ---------------------------------------------------------------------------

def load_markdown_files() -> list[Document]:
    """Load all .md files in data/text/ → split by H2 sections."""
    docs: list[Document] = []
    for md_path in sorted(settings.TEXT_DIR.glob("*.md")):
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Simple H2-based splitting
        sections = _split_by_h2(content)
        for i, (heading, body) in enumerate(sections):
            chunk_text = f"## {heading}\n\n{body}".strip()
            docs.append(
                Document(
                    page_content=chunk_text,
                    metadata={
                        "source": md_path.name,
                        "doc_id": f"{md_path.stem}_sec{i}",
                        "doc_type": "text",
                        "heading": heading,
                    },
                )
            )
    print(f"[ingest] Loaded {len(docs)} markdown sections")
    return docs


# ---------------------------------------------------------------------------
# Text formatters
# ---------------------------------------------------------------------------

def _course_to_text(c: dict) -> str:
    """Convert a course JSON object to a plain-text description."""
    lines = [
        f"Course: {c['name']}",
        f"ID: {c['id']}",
        f"Track: {', '.join(c.get('track', []))}",
        f"Level: {c.get('level', 'N/A')}",
        f"Duration: {c.get('duration', 'N/A')}",
    ]
    if c.get("prerequisites"):
        lines.append(f"Prerequisites: {c['prerequisites']}")
    lines.append(f"Summary: {c.get('summary', '')}")
    if c.get("link"):
        lines.append(f"Link: {c['link']}")
    return "\n".join(lines)


def _roadmap_to_text(r: dict) -> str:
    """Convert a roadmap JSON object to a plain-text description."""
    lines = [
        f"Track/Diploma: {r['name']}",
        f"ID: {r['id']}",
        f"Track categories: {', '.join(r.get('track', []))}",
        f"Duration: {r.get('duration', 'N/A')}",
        f"Number of courses: {r.get('courses_count', 0)}",
    ]
    if r.get("skills"):
        lines.append(f"Skills you'll learn: {', '.join(r['skills'])}")
    if r.get("tools"):
        lines.append(f"Tools covered: {', '.join(r['tools'])}")
    lines.append(f"Summary: {r.get('summary', '')}")
    if r.get("link"):
        lines.append(f"Link: {r['link']}")
    return "\n".join(lines)


def _split_by_h2(text: str) -> list[tuple[str, str]]:
    """Split markdown text by ## headings. Returns [(heading, body), ...]."""
    import re
    pattern = r"^##\s+(.*)\n"
    parts = re.split(pattern, text, flags=re.MULTILINE)
    # parts[0] is preamble (before first H2), parts[1] = first heading, parts[2] = body, ...
    sections = []
    if parts[0].strip():
        sections.append(("Overview", parts[0].strip()))
    for i in range(1, len(parts), 2):
        heading = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        sections.append((heading, body))
    return sections


# ---------------------------------------------------------------------------
# Embedding & vector store builder
# ---------------------------------------------------------------------------

def build_vector_store(
    persist_dir: Path | None = None,
    collection_name: str = "kayfa_kb",
) -> Chroma | None:
    """Build the ChromaDB vector store from all data sources.

    Returns the vector store instance, or None if OpenAI API key is missing.
    """
    settings = get_settings()

    if not settings.llm_api_key or settings.llm_api_key == "sk-your-openai-api-key-here":
        print("[ingest] OPENAI_API_KEY / OPENROUTER_API_KEY not set. Vector store build skipped.")
        return None

    persist_dir = persist_dir or settings.VECTORSTORE_DIR
    persist_dir.mkdir(parents=True, exist_ok=True)

    # Load all documents
    documents: list[Document] = []
    documents.extend(load_courses())
    documents.extend(load_roadmaps())
    documents.extend(load_markdown_files())

    if not documents:
        print("[ingest] No documents found. Nothing to embed.")
        return None

    print(f"[ingest] Total chunks to embed: {len(documents)}")

    # Initialize embeddings (OpenRouter or native OpenAI)
    embedding_kwargs = {
        "api_key": settings.llm_api_key,
        "model": settings.embedding_model,
    }
    if settings.llm_base_url:
        embedding_kwargs["openai_api_base"] = settings.llm_base_url
    embeddings = OpenAIEmbeddings(**embedding_kwargs)

    # Build and persist ChromaDB
    vectordb = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=str(persist_dir),
        collection_name=collection_name,
    )
    if hasattr(vectordb, "persist"):
        vectordb.persist()
    print(f"[ingest] Vector store built and persisted to {persist_dir}")
    return vectordb


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    build_vector_store()
