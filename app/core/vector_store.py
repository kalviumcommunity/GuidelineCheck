from langchain_community.vectorstores import Chroma
from app.core.embeddings import get_embeddings
from app.config import settings
import os

_vector_store = None

def get_vector_store() -> Chroma:
    """Returns the Chroma vector store instance."""
    global _vector_store
    if _vector_store is None:
        os.makedirs(settings.chroma_db_dir, exist_ok=True)
        _vector_store = Chroma(
            collection_name="guidelines",
            embedding_function=get_embeddings(),
            persist_directory=settings.chroma_db_dir
        )
    return _vector_store
