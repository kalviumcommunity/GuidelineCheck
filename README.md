# GuidelineCheck Backend
## Features
- Ingest documents with rich metadata
- Chunking and embedding generation using Sentence Transformers
- Semantic search using ChromaDB, prioritizing "Current" guidelines
- LLM grounded response generation 

## Setup
1. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in the required environment variables:
   ```bash
   cp .env.example .env
   ```
4. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Documentation
Once running, visit `http://127.0.0.1:8000/docs` to interact with the API endpoints.
