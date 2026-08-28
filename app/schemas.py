from pydantic import BaseModel, Field
from typing import List, Optional, Any

class DocumentMetadata(BaseModel):
    document_id: str
    title: str
    document_type: str
    topic: str
    version: str
    publication_date: str
    effective_date: str
    status: str
    supersedes: Optional[str] = None

class DocumentCreate(BaseModel):
    page_content: str
    metadata: DocumentMetadata

class IngestRequest(BaseModel):
    documents: List[DocumentCreate]

class QueryRequest(BaseModel):
    question: str

class SourceDocument(BaseModel):
    document_id: str
    title: str
    status: str
    effective_date: str
    chunk_content: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]
