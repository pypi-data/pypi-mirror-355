from pinecone import Pinecone
from pr_agent.settings import settings

# ─── Initialize Pinecone client and index ─────────────────────────────────
_pc = Pinecone(api_key=settings.PINECONE_API_KEY)
_index = _pc.Index(settings.PINECONE_INDEX)

# def upsert_embedding(doc_id: str, vector: list[float], metadata: dict = None):
#     """
#     Upsert a single vector into Pinecone under the given doc_id.
#     Metadata can include fields like source_system, timestamp, etc.
#     """
#     # Pinecone expects a list of tuples: (id, vector, metadata)
#     _index.upsert([(doc_id, vector, metadata or {})])

def upsert_embedding(doc_id: str,
                     vector: list[float],
                     metadata: dict | None = None):
    """
    Upsert a single vector into Pinecone under the given doc_id.
    """
    _index.upsert([(doc_id, vector, metadata or {})])


def query_embedding(vector: list[float],
                    top_k: int = 5,
                    include_metadata: bool = True):
    """
    Query Pinecone for the top_k most similar vectors.
    """
    return _index.query(
        vector=vector,
        top_k=top_k,
        include_metadata=include_metadata
    )