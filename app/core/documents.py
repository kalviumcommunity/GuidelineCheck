from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.schemas import IngestRequest
from app.core.vector_store import get_vector_store
import logging

logger = logging.getLogger(__name__)

def process_and_ingest_documents(ingest_request: IngestRequest) -> int:
    """Chunks documents while preserving metadata, and stores them in Chroma."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )

    langchain_docs = []
    
    for doc in ingest_request.documents:
        # We need to make sure the metadata dictionary values are strings/ints/floats/bools for Chroma
        metadata = doc.metadata.model_dump(exclude_none=True)
        
        chunks = text_splitter.split_text(doc.page_content)
        for chunk in chunks:
            langchain_docs.append(Document(page_content=chunk, metadata=metadata))
            
    if langchain_docs:
        vector_store = get_vector_store()
        vector_store.add_documents(langchain_docs)
        logger.info(f"Ingested {len(langchain_docs)} chunks from {len(ingest_request.documents)} documents.")
        
    return len(langchain_docs)
