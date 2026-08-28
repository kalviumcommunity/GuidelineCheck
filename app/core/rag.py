from app.schemas import QueryRequest, QueryResponse, SourceDocument
from app.core.vector_store import get_vector_store
from app.config import settings
from langchain_core.prompts import PromptTemplate
import logging

logger = logging.getLogger(__name__)

# Try to load groq, fallback to a mocked generation if no API key is provided
try:
    if settings.groq_api_key:
        from langchain_groq import ChatGroq
        llm = ChatGroq(model_name="llama3-8b-8192", groq_api_key=settings.groq_api_key)
    else:
        llm = None
except ImportError:
    llm = None

def generate_rag_response(request: QueryRequest) -> QueryResponse:
    vector_store = get_vector_store()
    
    # 1. Retrieval
    # If the user asks for "historical" or "previous" guidance, we don't filter.
    # Otherwise, prioritize current guidance.
    is_historical_query = any(word in request.question.lower() for word in ["historical", "previous", "past", "superseded", "old"])
    
    search_kwargs = {"k": 4}
    if not is_historical_query:
        search_kwargs["filter"] = {"status": "Current"}
        
    retriever = vector_store.as_retriever(search_kwargs=search_kwargs)
    retrieved_docs = retriever.invoke(request.question)
    
    if not retrieved_docs:
        return QueryResponse(
            answer="I could not find sufficient information in the available guidance documents to answer this question.",
            sources=[]
        )
        
    # 2. Context formatting
    context = ""
    sources = []
    for doc in retrieved_docs:
        context += f"Document: {doc.metadata.get('title', 'Unknown')}\n"
        context += f"Status: {doc.metadata.get('status', 'Unknown')}\n"
        context += f"Content: {doc.page_content}\n\n"
        
        sources.append(SourceDocument(
            document_id=doc.metadata.get('document_id', ''),
            title=doc.metadata.get('title', ''),
            status=doc.metadata.get('status', ''),
            effective_date=doc.metadata.get('effective_date', ''),
            chunk_content=doc.page_content
        ))
        
    # 3. Generation
    prompt_template = """You are a helpful assistant for public health field workers.
Answer the question based ONLY on the following provided guidance context. 
If the context does not contain the answer, say "I could not find sufficient information in the available guidance documents to answer this question." Do not invent information.

Context:
{context}

Question: {question}

Answer:"""
    
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    
    if llm:
        chain = prompt | llm
        response = chain.invoke({"context": context, "question": request.question})
        answer_text = response.content
    else:
        # Fallback if no LLM is configured - for local demo purposes without API keys
        answer_text = f"LLM is not configured (missing API key). Here is the context that would have been used to answer the question:\n\n{context}"
        
    return QueryResponse(answer=answer_text, sources=sources)
