"""
WealthVisor — Vector Store
Qdrant client wrapper using FastEmbed (BAAI/bge-small-en-v1.5) for local embeddings.
No OpenAI API calls needed. Collection: wealth_visor_briefs, dim=384, Cosine distance.
"""

import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = "wealth_visor_briefs"
VECTOR_DIM = 384  # BAAI/bge-small-en-v1.5 output dimension

# ─── FastEmbed model (loaded once at module level) ──────────────────────────
_embedder = None

def _get_embedder():
    """Lazy-loads the FastEmbed model."""
    global _embedder
    if _embedder is None:
        try:
            from fastembed import TextEmbedding
            _embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            logger.info("FastEmbed model (BAAI/bge-small-en-v1.5) loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load FastEmbed model: {e}")
    return _embedder


def _get_client():
    """Returns initialized Qdrant client. Creates collection if not exists."""
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams

        client = QdrantClient(url=QDRANT_URL)

        # Create collection if it doesn't exist
        collections = [c.name for c in client.get_collections().collections]
        if COLLECTION not in collections:
            client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(
                    size=VECTOR_DIM,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(f"Created Qdrant collection: {COLLECTION}")

        return client
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant at {QDRANT_URL}: {e}")
        return None


def embed_text(text: str) -> list[float] | None:
    """Embeds text using FastEmbed (BAAI/bge-small-en-v1.5). Returns 384-dim vector."""
    embedder = _get_embedder()
    if embedder is None:
        logger.error("Embedder not available")
        return None
    try:
        embeddings = list(embedder.embed([text]))
        return embeddings[0].tolist()
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return None


def upsert_brief(client_id: int, meeting_id: int, brief_markdown: str) -> bool:
    """
    Embeds brief_markdown and upserts to Qdrant.
    Point ID: meeting_id. Payload: client_id, meeting_id, timestamp, brief_markdown.
    Returns True on success, False on failure.
    """
    try:
        from qdrant_client.models import PointStruct

        qdrant = _get_client()
        if qdrant is None:
            return False

        vector = embed_text(brief_markdown[:2000])  # embed first 2000 chars
        if vector is None:
            return False

        point = PointStruct(
            id=meeting_id,
            vector=vector,
            payload={
                "client_id": client_id,
                "meeting_id": meeting_id,
                "timestamp": datetime.utcnow().isoformat(),
                "brief_markdown": brief_markdown,
            },
        )
        qdrant.upsert(collection_name=COLLECTION, points=[point])
        logger.info(f"Upserted brief for meeting {meeting_id} to Qdrant")
        return True
    except Exception as e:
        logger.error(f"Failed to upsert brief to Qdrant: {e}")
        return False


def retrieve_past_briefs(client_id: int, query: str, top_k: int = 2) -> list[dict]:
    """
    Semantic search for past briefs of this client.
    Returns top_k results with brief_markdown payload.
    """
    try:
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        qdrant = _get_client()
        if qdrant is None:
            return []

        vector = embed_text(query)
        if vector is None:
            return []

        results = qdrant.search(
            collection_name=COLLECTION,
            query_vector=vector,
            query_filter=Filter(
                must=[
                    FieldCondition(key="client_id", match=MatchValue(value=client_id))
                ]
            ),
            limit=top_k,
        )

        return [
            {
                "meeting_id": r.payload.get("meeting_id"),
                "timestamp": r.payload.get("timestamp"),
                "brief_markdown": r.payload.get("brief_markdown", ""),
                "score": r.score,
            }
            for r in results
        ]
    except Exception as e:
        logger.error(f"Failed to retrieve briefs from Qdrant: {e}")
        return []


def check_qdrant_health() -> bool:
    """Returns True if Qdrant is reachable."""
    try:
        client = _get_client()
        return client is not None
    except Exception:
        return False
