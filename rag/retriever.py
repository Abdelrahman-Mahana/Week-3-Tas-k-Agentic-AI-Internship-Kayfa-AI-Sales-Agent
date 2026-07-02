from typing import List, Dict, Any
from pathlib import Path

from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma

from core.config import get_settings

_settings = get_settings()

# Lazy-loaded singletons
_embeddings = None
_vectordb = None


def _get_embeddings() -> OpenAIEmbeddings | None:
    """Lazy-load embeddings client."""
    global _embeddings
    if _embeddings is None:
        if not _settings.llm_api_key or _settings.llm_api_key == "sk-your-openai-api-key-here":
            return None
        embedding_kwargs = {
            "api_key": _settings.llm_api_key,
            "model": _settings.embedding_model,
        }
        if _settings.llm_base_url:
            embedding_kwargs["openai_api_base"] = _settings.llm_base_url
        _embeddings = OpenAIEmbeddings(**embedding_kwargs)
    return _embeddings


def _get_vectorstore() -> Chroma | None:
    """Lazy-load ChromaDB vector store."""
    global _vectordb
    if _vectordb is None:
        persist_dir = _settings.VECTORSTORE_DIR
        if not persist_dir.exists():
            return None
        embeddings = _get_embeddings()
        if embeddings is None:
            return None
        _vectordb = Chroma(
            persist_directory=str(persist_dir),
            embedding_function=embeddings,
            collection_name="kayfa_kb",
        )
    return _vectordb


def search_kb(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """Search the knowledge base for relevant chunks.

    Returns a list of dicts with keys: content, metadata, score.
    If vector store is unavailable, returns empty list.
    """
    vectordb = _get_vectorstore()
    if vectordb is None:
        return []

    results = vectordb.similarity_search_with_score(query, k=k)
    output = []
    for doc, score in results:
        output.append({
            "content": doc.page_content,
            "metadata": doc.metadata,
            "score": round(float(score), 4),
        })
    return output


def get_course_by_id(course_id: str) -> Dict[str, Any] | None:
    """Retrieve a specific course by its ID."""
    vectordb = _get_vectorstore()
    if vectordb is None:
        return None

    # Chroma metadata filter
    results = vectordb.get(
        where={"doc_id": course_id, "doc_type": "course"},
        include=["documents", "metadatas"],
    )
    if results and results["documents"]:
        return {
            "content": results["documents"][0],
            "metadata": results["metadatas"][0],
        }
    return None


def get_roadmap_by_id(roadmap_id: str) -> Dict[str, Any] | None:
    """Retrieve a specific roadmap/track by its ID."""
    vectordb = _get_vectorstore()
    if vectordb is None:
        return None

    results = vectordb.get(
        where={"doc_id": roadmap_id, "doc_type": "roadmap"},
        include=["documents", "metadatas"],
    )
    if results and results["documents"]:
        return {
            "content": results["documents"][0],
            "metadata": results["metadatas"][0],
        }
    return None


def is_kb_ready() -> bool:
    """Check if the vector store is built and accessible."""
    return _get_vectorstore() is not None
